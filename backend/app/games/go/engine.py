from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


BOARD_SIZE = 19
KOMI = 7.5
BOARD_SIZES = {9, 13, 19}
KOMI_VALUES = {0.0, 6.5, 7.5}


@dataclass
class GoState:
    board: list[list[int]] = field(
        default_factory=lambda: [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    )
    turn_seat: int = 0
    consecutive_passes: int = 0
    captures: list[int] = field(default_factory=lambda: [0, 0])
    last_move: dict[str, int | bool] | None = None
    move_count: int = 0
    score: dict[str, float | int] | None = None
    position_history: list[str] = field(default_factory=list)
    dead_stones: list[tuple[int, int]] = field(default_factory=list)
    score_confirmed_player_ids: list[str] = field(default_factory=list)
    resume_requested_by: str | None = None


class GoEngine:
    key = "go"
    name = "围棋"
    min_players = 2
    max_players = 2

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        board_size = options.get("boardSize", BOARD_SIZE)
        komi = options.get("komi", KOMI)
        if (
            not isinstance(board_size, int)
            or isinstance(board_size, bool)
            or board_size not in BOARD_SIZES
        ):
            raise GameRuleError("围棋棋盘只能选择 9 路、13 路或 19 路")
        if (
            not isinstance(komi, (int, float))
            or isinstance(komi, bool)
            or float(komi) not in KOMI_VALUES
        ):
            raise GameRuleError("贴目只能选择 0、6.5 或 7.5")
        return {"boardSize": board_size, "komi": float(komi)}

    def initial_state(self) -> GoState:
        return GoState()

    def start(self, room: ArcadeRoom) -> None:
        board_size = room.options.get("boardSize", BOARD_SIZE)
        board = [[0] * board_size for _ in range(board_size)]
        room.state = GoState(
            board=board,
            position_history=[self._board_key(board)],
        )
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        state: GoState = room.state
        if action == "resign":
            opponent = room.players[1 - player.seat]
            room.finish(
                self._color_name(opponent.seat),
                [opponent.id],
                f"{player.name} 认输",
            )
            return
        if room.phase == "scoring":
            self._act_scoring(room, state, player, action, payload)
            return
        if room.phase != "playing":
            raise GameRuleError("当前不能进行这个围棋操作")
        if player.seat != state.turn_seat:
            raise GameRuleError("还没有轮到你落子")
        if action == "pass":
            state.consecutive_passes += 1
            state.move_count += 1
            state.last_move = {"pass": True, "seat": player.seat}
            state.turn_seat = 1 - state.turn_seat
            if state.consecutive_passes >= 2:
                state.dead_stones.clear()
                state.score_confirmed_player_ids.clear()
                state.resume_requested_by = None
                state.score = None
                room.phase = "scoring"
                return
            return
        if action != "place":
            raise GameRuleError("不支持这个围棋操作")
        board_size = len(state.board)
        row = self._coordinate(payload, "row", board_size)
        column = self._coordinate(payload, "column", board_size)
        if state.board[row][column] != 0:
            raise GameRuleError("这个交叉点已经有棋子")

        stone = player.seat + 1
        opponent = 2 if stone == 1 else 1
        old_board = [line[:] for line in state.board]
        next_board = [line[:] for line in state.board]
        next_board[row][column] = stone
        captured = 0
        for neighbor in self._neighbors(row, column, board_size):
            if next_board[neighbor[0]][neighbor[1]] != opponent:
                continue
            group, liberties = self._group(next_board, *neighbor)
            if not liberties:
                captured += len(group)
                for captured_row, captured_column in group:
                    next_board[captured_row][captured_column] = 0
        _, own_liberties = self._group(next_board, row, column)
        if not own_liberties:
            raise GameRuleError("这里会形成无气的棋，不能落子")
        next_position = self._board_key(next_board)
        if next_position in state.position_history:
            raise GameRuleError("这个落子会重复以前的局面，违反全局同形禁着")

        state.board = next_board
        if not state.position_history:
            state.position_history.append(self._board_key(old_board))
        state.position_history.append(next_position)
        state.captures[player.seat] += captured
        state.consecutive_passes = 0
        state.move_count += 1
        state.last_move = {
            "row": row,
            "column": column,
            "seat": player.seat,
            "pass": False,
        }
        state.dead_stones.clear()
        state.score_confirmed_player_ids.clear()
        state.resume_requested_by = None
        state.score = None
        state.turn_seat = 1 - state.turn_seat

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: GoState = room.state
        score = (
            self._score_details(room, state)
            if room.phase == "scoring"
            else state.score
        )
        return {
            "boardSize": len(state.board),
            "board": state.board,
            "turnPlayerId": (
                room.players[state.turn_seat].id
                if room.phase == "playing"
                else None
            ),
            "colors": {
                room.players[0].id: "black",
                room.players[1].id: "white",
            }
            if len(room.players) == 2
            else {},
            "captures": {
                "black": state.captures[0],
                "white": state.captures[1],
            },
            "komi": room.options.get("komi", KOMI),
            "lastMove": state.last_move,
            "score": score,
            "scoring": (
                {
                    "deadStones": [
                        {"row": row, "column": column}
                        for row, column in state.dead_stones
                    ],
                    "confirmedPlayerIds": state.score_confirmed_player_ids,
                    "resumeRequesterId": state.resume_requested_by,
                }
                if room.phase == "scoring"
                else None
            ),
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        color = self._color_name(player.seat)
        return color, color, player.id in room.winner_player_ids

    def _act_scoring(
        self,
        room: ArcadeRoom,
        state: GoState,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if action == "mark_dead":
            board_size = len(state.board)
            row = self._coordinate(payload, "row", board_size)
            column = self._coordinate(payload, "column", board_size)
            if state.board[row][column] == 0:
                raise GameRuleError("请选择棋盘上的棋子")
            group, _ = self._group(state.board, row, column)
            selected = set(state.dead_stones)
            if group.issubset(selected):
                selected.difference_update(group)
            else:
                selected.update(group)
            state.dead_stones = sorted(selected)
            state.score_confirmed_player_ids.clear()
            state.resume_requested_by = None
            return
        if action == "confirm_score":
            if player.id not in state.score_confirmed_player_ids:
                state.score_confirmed_player_ids.append(player.id)
            state.resume_requested_by = None
            if set(state.score_confirmed_player_ids) == {
                member.id for member in room.players
            }:
                self._finish_by_score(room, state)
            return
        if action == "resume_play":
            state.score_confirmed_player_ids.clear()
            if state.resume_requested_by is None:
                state.resume_requested_by = player.id
                return
            if state.resume_requested_by == player.id:
                state.resume_requested_by = None
                return
            state.resume_requested_by = None
            state.dead_stones.clear()
            state.consecutive_passes = 0
            state.score = None
            room.phase = "playing"
            return
        raise GameRuleError("数子阶段只能标记死子、确认结果或继续对局")

    def _finish_by_score(self, room: ArcadeRoom, state: GoState) -> None:
        dead_black = sum(
            state.board[row][column] == 1 for row, column in state.dead_stones
        )
        dead_white = sum(
            state.board[row][column] == 2 for row, column in state.dead_stones
        )
        score = self._score_details(room, state)
        state.board = self._board_without_dead_stones(state)
        state.captures[0] += dead_white
        state.captures[1] += dead_black
        state.score = score
        black_score = float(state.score["black"])
        white_score = float(state.score["white"])
        if black_score > white_score:
            margin = black_score - white_score
            room.finish(
                "black",
                [room.players[0].id],
                f"双方确认数子，黑方领先 {margin:g}",
            )
        elif white_score > black_score:
            margin = white_score - black_score
            room.finish(
                "white",
                [room.players[1].id],
                f"双方确认数子，白方领先 {margin:g}",
            )
        else:
            room.finish("draw", [], "双方确认数子，结果为和棋")

    def _score_details(
        self, room: ArcadeRoom, state: GoState
    ) -> dict[str, float | int]:
        board = self._board_without_dead_stones(state)
        breakdown = self._area_breakdown(board)
        komi = float(room.options.get("komi", KOMI))
        dead_black = sum(
            state.board[row][column] == 1 for row, column in state.dead_stones
        )
        dead_white = sum(
            state.board[row][column] == 2 for row, column in state.dead_stones
        )
        black_score = breakdown["blackStones"] + breakdown["blackTerritory"]
        white_score = (
            breakdown["whiteStones"] + breakdown["whiteTerritory"] + komi
        )
        return {
            "black": float(black_score),
            "white": float(white_score),
            **breakdown,
            "komi": komi,
            "deadBlack": dead_black,
            "deadWhite": dead_white,
        }

    @staticmethod
    def _board_without_dead_stones(state: GoState) -> list[list[int]]:
        board = [row[:] for row in state.board]
        for row, column in state.dead_stones:
            board[row][column] = 0
        return board

    def _area_breakdown(self, board: list[list[int]]) -> dict[str, int]:
        black_stones = sum(cell == 1 for row in board for cell in row)
        white_stones = sum(cell == 2 for row in board for cell in row)
        black_territory = 0
        white_territory = 0
        neutral_points = 0
        visited: set[tuple[int, int]] = set()
        board_size = len(board)
        for row in range(board_size):
            for column in range(board_size):
                if board[row][column] != 0 or (row, column) in visited:
                    continue
                region: set[tuple[int, int]] = set()
                borders: set[int] = set()
                stack = [(row, column)]
                while stack:
                    point = stack.pop()
                    if point in region:
                        continue
                    region.add(point)
                    visited.add(point)
                    for neighbor in self._neighbors(*point, board_size):
                        value = board[neighbor[0]][neighbor[1]]
                        if value == 0 and neighbor not in region:
                            stack.append(neighbor)
                        elif value:
                            borders.add(value)
                if borders == {1}:
                    black_territory += len(region)
                elif borders == {2}:
                    white_territory += len(region)
                else:
                    neutral_points += len(region)
        return {
            "blackStones": black_stones,
            "blackTerritory": black_territory,
            "whiteStones": white_stones,
            "whiteTerritory": white_territory,
            "neutralPoints": neutral_points,
        }

    def _group(
        self, board: list[list[int]], row: int, column: int
    ) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
        stone = board[row][column]
        group: set[tuple[int, int]] = set()
        liberties: set[tuple[int, int]] = set()
        stack = [(row, column)]
        while stack:
            point = stack.pop()
            if point in group:
                continue
            group.add(point)
            for neighbor in self._neighbors(*point, len(board)):
                value = board[neighbor[0]][neighbor[1]]
                if value == 0:
                    liberties.add(neighbor)
                elif value == stone and neighbor not in group:
                    stack.append(neighbor)
        return group, liberties

    @staticmethod
    def _neighbors(
        row: int, column: int, board_size: int
    ) -> list[tuple[int, int]]:
        return [
            (next_row, next_column)
            for next_row, next_column in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            )
            if 0 <= next_row < board_size and 0 <= next_column < board_size
        ]

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
    def _board_key(board: list[list[int]]) -> str:
        return "".join(str(cell) for row in board for cell in row)

    @staticmethod
    def _color_name(seat: int) -> str:
        return "black" if seat == 0 else "white"
