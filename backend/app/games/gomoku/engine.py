from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


BOARD_SIZE = 15
WIN_RULES = {"freestyle", "exact_five", "renju"}
OPENING_RULES = {"standard", "swap2"}
TIME_LIMIT_SECONDS = {0, 180, 300, 600}
RENJU_RULE = "renju"
SWAP2_RULE = "swap2"
SWAP2_PLACE_THREE = "place_three"
SWAP2_SECOND_CHOICE = "second_choice"
SWAP2_PLACE_TWO = "place_two"
SWAP2_FIRST_CHOICE = "first_choice"
BLACK = 1
WHITE = 2
Direction = tuple[int, int]
Point = tuple[int, int]
Pattern = frozenset[Point]
DIRECTIONS: tuple[Direction, ...] = ((1, 0), (0, 1), (1, 1), (1, -1))


@dataclass
class GomokuState:
    board: list[list[int]] = field(
        default_factory=lambda: [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    )
    turn_seat: int = 0
    moves: list[dict[str, int]] = field(default_factory=list)
    last_action: dict[str, int | bool] | None = None
    consecutive_passes: int = 0
    forbidden_points: list[dict[str, int | str]] | None = None
    seat_stones: list[int] = field(default_factory=lambda: [BLACK, WHITE])
    swap2_stage: str | None = None
    swap2_initial_seat: int = 0
    clock_remaining_ms: list[int] | None = None
    turn_started_at_ms: int | None = None


class GomokuEngine:
    key = "gomoku"
    name = "五子棋"
    min_players = 2
    max_players = 2

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self.clock = clock or time.time

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        win_rule = options.get("winRule", "freestyle")
        if win_rule not in WIN_RULES:
            raise GameRuleError("请选择自由五子、正好五子或有禁手连珠")
        opening_rule = options.get("openingRule", "standard")
        if opening_rule not in OPENING_RULES:
            raise GameRuleError("请选择标准开局或 Swap2 开局")
        time_limit = options.get("timeLimitSeconds", 0)
        if (
            not isinstance(time_limit, int)
            or isinstance(time_limit, bool)
            or time_limit not in TIME_LIMIT_SECONDS
        ):
            raise GameRuleError("请选择不计时、3 分钟、5 分钟或 10 分钟")
        return {
            "winRule": win_rule,
            "openingRule": opening_rule,
            "timeLimitSeconds": time_limit,
        }

    def initial_state(self) -> GomokuState:
        return GomokuState()

    def start(self, room: ArcadeRoom) -> None:
        time_limit_ms = room.options.get("timeLimitSeconds", 0) * 1000
        room.state = GomokuState(
            swap2_stage=(
                SWAP2_PLACE_THREE
                if room.options.get("openingRule") == SWAP2_RULE
                else None
            ),
            clock_remaining_ms=(
                [time_limit_ms, time_limit_ms]
                if time_limit_ms > 0
                else None
            ),
            turn_started_at_ms=(
                self._now_ms() if time_limit_ms > 0 else None
            ),
        )
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        state: GomokuState = room.state
        now_ms = self._now_ms()
        if self._expire_timeout_at(room, state, now_ms):
            return
        if action == "resign":
            opponent = room.players[1 - player.seat]
            self._finish(
                room,
                state,
                self._stone_name(state.seat_stones[opponent.seat]),
                [opponent.id],
                f"{player.name} 认输",
            )
            return
        if player.seat != state.turn_seat:
            raise GameRuleError("还没有轮到你落子")
        if action == "swap2_choose":
            self._choose_swap2_color(
                room,
                state,
                player,
                payload,
                now_ms,
            )
            return
        if action == "pass":
            self._pass(room, state, player, now_ms)
            return
        if action != "place":
            raise GameRuleError("不支持这个五子棋操作")
        if state.swap2_stage in {
            SWAP2_SECOND_CHOICE,
            SWAP2_FIRST_CHOICE,
        }:
            raise GameRuleError("请先完成 Swap2 选色")
        board_size = len(state.board)
        row = self._coordinate(payload, "row", board_size)
        column = self._coordinate(payload, "column", board_size)
        if state.board[row][column] != 0:
            raise GameRuleError("这个位置已经有棋子")
        if state.swap2_stage is not None:
            self._place_swap2_stone(
                room,
                state,
                player,
                row,
                column,
                now_ms,
            )
            return

        stone = state.seat_stones[player.seat]
        win_rule = room.options.get("winRule", "freestyle")
        renju_analysis: tuple[bool, str | None] | None = None
        if win_rule == RENJU_RULE and stone == BLACK:
            center = board_size // 2
            if not state.moves and (row, column) != (center, center):
                raise GameRuleError("有禁手连珠的黑方首手必须落在天元")
            renju_analysis = self._analyze_black_move(
                state.board,
                row,
                column,
            )
            if renju_analysis[1] is not None:
                raise GameRuleError(f"黑方禁手：{renju_analysis[1]}")
        self._charge_clock(state, now_ms)
        state.board[row][column] = stone
        move = {"row": row, "column": column, "stone": stone}
        state.moves.append(move)
        state.last_action = move
        state.consecutive_passes = 0
        state.forbidden_points = None
        if win_rule == RENJU_RULE:
            has_won = (
                bool(renju_analysis and renju_analysis[0])
                if stone == BLACK
                else self._has_winning_line(
                    state.board,
                    row,
                    column,
                    stone,
                    exact=False,
                )
            )
        else:
            has_won = self._has_winning_line(
                state.board,
                row,
                column,
                stone,
                exact=win_rule == "exact_five",
            )
        if has_won:
            self._finish(
                room,
                state,
                self._stone_name(stone),
                [player.id],
                f"{player.name} 连成五子",
            )
            return
        if len(state.moves) == board_size * board_size:
            self._finish(room, state, "draw", [], "棋盘已满，双方和棋")
            return
        state.turn_seat = 1 - state.turn_seat
        state.turn_started_at_ms = now_ms

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: GomokuState = room.state
        win_rule = room.options.get("winRule", "freestyle")
        now_ms = self._now_ms()
        opening_move: dict[str, int] | None = None
        expected_swap2_stone = self._swap2_expected_stone(state)
        turn_stone = (
            expected_swap2_stone
            if expected_swap2_stone is not None
            else state.seat_stones[state.turn_seat]
        )
        if (
            room.phase == "playing"
            and win_rule == RENJU_RULE
            and turn_stone == BLACK
            and state.swap2_stage not in {
                SWAP2_SECOND_CHOICE,
                SWAP2_FIRST_CHOICE,
            }
        ):
            if not state.moves:
                center = len(state.board) // 2
                opening_move = {"row": center, "column": center}
                forbidden_points: list[dict[str, int | str]] = []
            else:
                if state.forbidden_points is None:
                    state.forbidden_points = self._find_forbidden_points(
                        state.board
                    )
                forbidden_points = state.forbidden_points
        else:
            forbidden_points = []
        return {
            "board": state.board,
            "turnPlayerId": (
                room.players[state.turn_seat].id
                if room.phase == "playing"
                else None
            ),
            "lastMove": state.last_action,
            "winRule": win_rule,
            "forbiddenPoints": forbidden_points,
            "openingMove": opening_move,
            "consecutivePasses": state.consecutive_passes,
            "swap2": {
                "enabled": room.options.get("openingRule") == SWAP2_RULE,
                "stage": state.swap2_stage,
                "actorPlayerId": (
                    room.players[state.turn_seat].id
                    if room.phase == "playing"
                    else None
                ),
                "initialPlayerId": room.players[
                    state.swap2_initial_seat
                ].id,
                "expectedColor": (
                    self._stone_name(expected_swap2_stone)
                    if expected_swap2_stone is not None
                    else None
                ),
                "resolved": state.swap2_stage is None,
            },
            "clock": self._clock_view(room, state, now_ms),
            "colors": {
                player.id: self._stone_name(state.seat_stones[player.seat])
                for player in room.players
            }
            if len(room.players) == 2
            else {},
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        state: GomokuState = room.state
        color = self._stone_name(state.seat_stones[player.seat])
        return color, color, player.id in room.winner_player_ids

    def expire_timeout(self, room: ArcadeRoom) -> bool:
        if room.phase != "playing":
            return False
        state: GomokuState = room.state
        return self._expire_timeout_at(room, state, self._now_ms())

    def resume_clock(self, room: ArcadeRoom) -> None:
        state: GomokuState = room.state
        if state.clock_remaining_ms is not None and room.phase == "playing":
            state.turn_started_at_ms = self._now_ms()

    @staticmethod
    def should_track_undo(room: ArcadeRoom, action: str) -> bool:
        state: GomokuState = room.state
        return state.swap2_stage is None and action in {"place", "pass"}

    def _place_swap2_stone(
        self,
        room: ArcadeRoom,
        state: GomokuState,
        player: ArcadePlayer,
        row: int,
        column: int,
        now_ms: int,
    ) -> None:
        stone = self._swap2_expected_stone(state)
        if stone is None:
            raise GameRuleError("当前不是 Swap2 摆子阶段")
        if (
            room.options.get("winRule") == RENJU_RULE
            and stone == BLACK
            and not state.moves
        ):
            center = len(state.board) // 2
            if (row, column) != (center, center):
                raise GameRuleError("有禁手连珠的黑方首手必须落在天元")

        self._charge_clock(state, now_ms)
        state.board[row][column] = stone
        move = {"row": row, "column": column, "stone": stone}
        state.moves.append(move)
        state.last_action = move
        state.consecutive_passes = 0
        state.forbidden_points = None

        if state.swap2_stage == SWAP2_PLACE_THREE and len(state.moves) == 3:
            state.swap2_stage = SWAP2_SECOND_CHOICE
            state.turn_seat = 1 - state.swap2_initial_seat
        elif state.swap2_stage == SWAP2_PLACE_TWO and len(state.moves) == 5:
            state.swap2_stage = SWAP2_FIRST_CHOICE
            state.turn_seat = state.swap2_initial_seat
        state.turn_started_at_ms = now_ms

    def _choose_swap2_color(
        self,
        room: ArcadeRoom,
        state: GomokuState,
        player: ArcadePlayer,
        payload: dict[str, Any],
        now_ms: int,
    ) -> None:
        choice = payload.get("choice")
        if state.swap2_stage == SWAP2_SECOND_CHOICE:
            if choice not in {"white", "black", "add"}:
                raise GameRuleError("请选择执白、交换执黑或再摆两子")
            self._charge_clock(state, now_ms)
            if choice == "add":
                state.swap2_stage = SWAP2_PLACE_TWO
            else:
                self._resolve_swap2_color(
                    state,
                    player.seat,
                    BLACK if choice == "black" else WHITE,
                )
        elif state.swap2_stage == SWAP2_FIRST_CHOICE:
            if choice not in {"white", "black"}:
                raise GameRuleError("请选择执黑或执白")
            self._charge_clock(state, now_ms)
            self._resolve_swap2_color(
                state,
                player.seat,
                BLACK if choice == "black" else WHITE,
            )
        else:
            raise GameRuleError("当前不是 Swap2 选色阶段")
        state.turn_started_at_ms = now_ms

    @staticmethod
    def _resolve_swap2_color(
        state: GomokuState,
        choosing_seat: int,
        chosen_stone: int,
    ) -> None:
        state.seat_stones[choosing_seat] = chosen_stone
        state.seat_stones[1 - choosing_seat] = (
            WHITE if chosen_stone == BLACK else BLACK
        )
        state.swap2_stage = None
        state.turn_seat = state.seat_stones.index(WHITE)
        state.forbidden_points = None

    def _pass(
        self,
        room: ArcadeRoom,
        state: GomokuState,
        player: ArcadePlayer,
        now_ms: int,
    ) -> None:
        if state.swap2_stage is not None:
            raise GameRuleError("Swap2 开局完成前不能停一手")
        if room.options.get("winRule") == RENJU_RULE and len(state.moves) < 3:
            raise GameRuleError("有禁手连珠的前三手不能停一手")
        self._charge_clock(state, now_ms)
        state.last_action = {"pass": True, "seat": player.seat}
        state.consecutive_passes += 1
        state.forbidden_points = None
        if state.consecutive_passes >= 2:
            self._finish(room, state, "draw", [], "双方连续停一手，本局和棋")
            return
        state.turn_seat = 1 - state.turn_seat
        state.turn_started_at_ms = now_ms

    @staticmethod
    def _swap2_expected_stone(state: GomokuState) -> int | None:
        if state.swap2_stage == SWAP2_PLACE_THREE:
            index = len(state.moves)
            sequence = (BLACK, WHITE, BLACK)
            return sequence[index] if index < len(sequence) else None
        if state.swap2_stage == SWAP2_PLACE_TWO:
            index = len(state.moves) - 3
            sequence = (WHITE, BLACK)
            return sequence[index] if 0 <= index < len(sequence) else None
        return None

    def _clock_view(
        self,
        room: ArcadeRoom,
        state: GomokuState,
        now_ms: int,
    ) -> dict[str, Any] | None:
        if state.clock_remaining_ms is None:
            return None
        remaining = state.clock_remaining_ms[:]
        if room.phase == "playing" and state.turn_started_at_ms is not None:
            elapsed = max(0, now_ms - state.turn_started_at_ms)
            remaining[state.turn_seat] = max(
                0,
                remaining[state.turn_seat] - elapsed,
            )
        return {
            "limitMs": room.options.get("timeLimitSeconds", 0) * 1000,
            "remainingMs": {
                player.id: remaining[player.seat]
                for player in room.players
            },
            "activePlayerId": (
                room.players[state.turn_seat].id
                if room.phase == "playing"
                else None
            ),
            "serverNowMs": now_ms,
        }

    def _expire_timeout_at(
        self,
        room: ArcadeRoom,
        state: GomokuState,
        now_ms: int,
    ) -> bool:
        if (
            room.phase != "playing"
            or state.clock_remaining_ms is None
            or state.turn_started_at_ms is None
        ):
            return False
        active_seat = state.turn_seat
        elapsed = max(0, now_ms - state.turn_started_at_ms)
        if elapsed < state.clock_remaining_ms[active_seat]:
            return False
        state.clock_remaining_ms[active_seat] = 0
        loser = room.players[active_seat]
        winner = room.players[1 - active_seat]
        self._finish(
            room,
            state,
            self._stone_name(state.seat_stones[winner.seat]),
            [winner.id],
            f"{loser.name} 用时耗尽，{winner.name} 获胜",
        )
        return True

    @staticmethod
    def _charge_clock(state: GomokuState, now_ms: int) -> None:
        if (
            state.clock_remaining_ms is None
            or state.turn_started_at_ms is None
        ):
            return
        elapsed = max(0, now_ms - state.turn_started_at_ms)
        state.clock_remaining_ms[state.turn_seat] = max(
            0,
            state.clock_remaining_ms[state.turn_seat] - elapsed,
        )
        state.turn_started_at_ms = now_ms

    @staticmethod
    def _finish(
        room: ArcadeRoom,
        state: GomokuState,
        winner: str,
        winner_player_ids: list[str],
        reason: str,
    ) -> None:
        state.turn_started_at_ms = None
        room.finish(winner, winner_player_ids, reason)

    def _now_ms(self) -> int:
        return int(self.clock() * 1000)

    @staticmethod
    def _stone_name(stone: int) -> str:
        return "black" if stone == BLACK else "white"

    @staticmethod
    def _coordinate(
        payload: dict[str, Any], key: str, board_size: int
    ) -> int:
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise GameRuleError("落子坐标格式不正确")
        if not 0 <= value < board_size:
            raise GameRuleError("落子位置超出棋盘")
        return value

    @staticmethod
    def _has_winning_line(
        board: list[list[int]],
        row: int,
        column: int,
        stone: int,
        *,
        exact: bool,
    ) -> bool:
        for row_step, column_step in ((1, 0), (0, 1), (1, 1), (1, -1)):
            count = 1
            for direction in (-1, 1):
                next_row = row + row_step * direction
                next_column = column + column_step * direction
                while (
                    0 <= next_row < len(board)
                    and 0 <= next_column < len(board)
                    and board[next_row][next_column] == stone
                ):
                    count += 1
                    next_row += row_step * direction
                    next_column += column_step * direction
            has_winning_length = count == 5 if exact else count >= 5
            if has_winning_length:
                return True
        return False

    def _analyze_black_move(
        self,
        board: list[list[int]],
        row: int,
        column: int,
        memo: dict[tuple[str, int, int], tuple[bool, str | None]] | None = None,
    ) -> tuple[bool, str | None]:
        """Return (wins, forbidden reason) for one hypothetical black move.

        RIF rule 9 gives an exact five priority over every forbidden pattern.
        A double-three is evaluated recursively because a three only counts when
        black has a legal continuation that creates a straight four.
        """
        if board[row][column] != 0:
            return False, "已有棋子"
        cache = memo if memo is not None else {}
        key = (self._board_key(board), row, column)
        cached = cache.get(key)
        if cached is not None:
            return cached

        next_board = [line[:] for line in board]
        next_board[row][column] = BLACK
        move = (row, column)
        if self._has_exact_five(next_board, move):
            result = (True, None)
        elif self._has_overline(next_board, move):
            result = (False, "长连")
        elif len(self._four_patterns(next_board, move)) >= 2:
            result = (False, "四四")
        elif len(self._three_patterns(next_board, move, cache)) >= 2:
            result = (False, "三三")
        else:
            result = (False, None)
        cache[key] = result
        return result

    def _find_forbidden_points(
        self, board: list[list[int]]
    ) -> list[dict[str, int | str]]:
        memo: dict[tuple[str, int, int], tuple[bool, str | None]] = {}
        points: list[dict[str, int | str]] = []
        for row in range(len(board)):
            for column in range(len(board)):
                if board[row][column] != 0:
                    continue
                _, reason = self._analyze_black_move(
                    board,
                    row,
                    column,
                    memo,
                )
                if reason is not None:
                    points.append(
                        {"row": row, "column": column, "reason": reason}
                    )
        return points

    def _four_patterns(
        self, board: list[list[int]], move: Point
    ) -> set[Pattern]:
        patterns: set[Pattern] = set()
        for direction in DIRECTIONS:
            for offset in range(-4, 1):
                window = self._line_window(board, move, direction, offset, 5)
                if window is None or move not in window:
                    continue
                black_points = [
                    point
                    for point in window
                    if self._cell(board, point) == BLACK
                ]
                empty_points = [
                    point
                    for point in window
                    if self._cell(board, point) == 0
                ]
                if len(black_points) != 4 or len(empty_points) != 1:
                    continue
                completion = empty_points[0]
                completed = [line[:] for line in board]
                completed[completion[0]][completion[1]] = BLACK
                if self._line_length(completed, completion, direction) == 5:
                    patterns.add(frozenset(black_points))
        return patterns

    def _three_patterns(
        self,
        board: list[list[int]],
        move: Point,
        memo: dict[tuple[str, int, int], tuple[bool, str | None]],
    ) -> set[Pattern]:
        patterns: set[Pattern] = set()
        for extension in self._nearby_line_points(board, move):
            if self._cell(board, extension) != 0:
                continue
            extended = [line[:] for line in board]
            extended[extension[0]][extension[1]] = BLACK
            if self._has_exact_five(extended, extension):
                continue
            straight_fours = self._straight_four_patterns(
                extended,
                required={move, extension},
            )
            if not straight_fours:
                continue
            _, forbidden_reason = self._analyze_black_move(
                board,
                extension[0],
                extension[1],
                memo,
            )
            if forbidden_reason is not None:
                continue
            for straight_four in straight_fours:
                three = frozenset(straight_four.difference({extension}))
                if len(three) == 3 and move in three:
                    patterns.add(three)
        return patterns

    def _straight_four_patterns(
        self,
        board: list[list[int]],
        *,
        required: set[Point],
    ) -> set[Pattern]:
        anchor = min(required)
        patterns: set[Pattern] = set()
        for direction in DIRECTIONS:
            for offset in range(-3, 1):
                window = self._line_window(board, anchor, direction, offset, 4)
                if window is None or not required.issubset(window):
                    continue
                if any(self._cell(board, point) != BLACK for point in window):
                    continue
                before = self._shift(window[0], direction, -1)
                after = self._shift(window[-1], direction, 1)
                if not self._in_bounds(
                    board, before
                ) or not self._in_bounds(board, after):
                    continue
                if self._cell(board, before) != 0 or self._cell(board, after) != 0:
                    continue
                if not all(
                    self._completion_is_exact_five(board, point, direction)
                    for point in (before, after)
                ):
                    continue
                patterns.add(frozenset(window))
        return patterns

    def _completion_is_exact_five(
        self,
        board: list[list[int]],
        point: Point,
        direction: Direction,
    ) -> bool:
        completed = [line[:] for line in board]
        completed[point[0]][point[1]] = BLACK
        return self._line_length(completed, point, direction) == 5

    def _has_exact_five(self, board: list[list[int]], move: Point) -> bool:
        return any(
            self._line_length(board, move, direction) == 5
            for direction in DIRECTIONS
        )

    def _has_overline(self, board: list[list[int]], move: Point) -> bool:
        return any(
            self._line_length(board, move, direction) >= 6
            for direction in DIRECTIONS
        )

    def _line_length(
        self,
        board: list[list[int]],
        point: Point,
        direction: Direction,
    ) -> int:
        stone = self._cell(board, point)
        count = 1
        for sign in (-1, 1):
            next_point = self._shift(point, direction, sign)
            while (
                self._in_bounds(board, next_point)
                and self._cell(board, next_point) == stone
            ):
                count += 1
                next_point = self._shift(next_point, direction, sign)
        return count

    def _nearby_line_points(
        self, board: list[list[int]], move: Point
    ) -> set[Point]:
        return {
            point
            for direction in DIRECTIONS
            for distance in range(-4, 5)
            if distance != 0
            for point in [self._shift(move, direction, distance)]
            if self._in_bounds(board, point)
        }

    @classmethod
    def _line_window(
        cls,
        board: list[list[int]],
        anchor: Point,
        direction: Direction,
        offset: int,
        length: int,
    ) -> tuple[Point, ...] | None:
        points = tuple(
            cls._shift(anchor, direction, offset + index)
            for index in range(length)
        )
        return (
            points
            if all(cls._in_bounds(board, point) for point in points)
            else None
        )

    @staticmethod
    def _shift(point: Point, direction: Direction, distance: int) -> Point:
        return (
            point[0] + direction[0] * distance,
            point[1] + direction[1] * distance,
        )

    @staticmethod
    def _in_bounds(board: list[list[int]], point: Point) -> bool:
        return 0 <= point[0] < len(board) and 0 <= point[1] < len(board)

    @staticmethod
    def _cell(board: list[list[int]], point: Point) -> int:
        return board[point[0]][point[1]]

    @staticmethod
    def _board_key(board: list[list[int]]) -> str:
        return "".join(str(cell) for row in board for cell in row)
