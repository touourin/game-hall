from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


BOARD_SIZE = 19
KOMI = 7.5


@dataclass
class GoState:
    board: list[list[int]] = field(
        default_factory=lambda: [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    )
    turn_seat: int = 0
    previous_board: list[list[int]] | None = None
    consecutive_passes: int = 0
    captures: list[int] = field(default_factory=lambda: [0, 0])
    last_move: dict[str, int | bool] | None = None
    move_count: int = 0
    score: dict[str, float] | None = None


class GoEngine:
    key = "go"
    name = "围棋"
    min_players = 2
    max_players = 2

    def initial_state(self) -> GoState:
        return GoState()

    def start(self, room: ArcadeRoom) -> None:
        room.state = self.initial_state()
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
        if player.seat != state.turn_seat:
            raise GameRuleError("还没有轮到你落子")
        if action == "pass":
            state.previous_board = [row[:] for row in state.board]
            state.consecutive_passes += 1
            state.move_count += 1
            state.last_move = {"pass": True, "seat": player.seat}
            if state.consecutive_passes >= 2:
                self._finish_by_score(room, state)
                return
            state.turn_seat = 1 - state.turn_seat
            return
        if action != "place":
            raise GameRuleError("不支持这个围棋操作")
        row = self._coordinate(payload, "row")
        column = self._coordinate(payload, "column")
        if state.board[row][column] != 0:
            raise GameRuleError("这个交叉点已经有棋子")

        stone = player.seat + 1
        opponent = 2 if stone == 1 else 1
        old_board = [line[:] for line in state.board]
        next_board = [line[:] for line in state.board]
        next_board[row][column] = stone
        captured = 0
        for neighbor in self._neighbors(row, column):
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
        if state.previous_board is not None and next_board == state.previous_board:
            raise GameRuleError("这个落子违反打劫规则")

        state.board = next_board
        state.previous_board = old_board
        state.captures[player.seat] += captured
        state.consecutive_passes = 0
        state.move_count += 1
        state.last_move = {
            "row": row,
            "column": column,
            "seat": player.seat,
            "pass": False,
        }
        state.turn_seat = 1 - state.turn_seat

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: GoState = room.state
        return {
            "boardSize": BOARD_SIZE,
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
            "komi": KOMI,
            "lastMove": state.last_move,
            "score": state.score,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        color = self._color_name(player.seat)
        return color, color, player.id in room.winner_player_ids

    def _finish_by_score(self, room: ArcadeRoom, state: GoState) -> None:
        black_score, white_score = self._area_score(state.board)
        white_score += KOMI
        state.score = {
            "black": float(black_score),
            "white": float(white_score),
        }
        if black_score > white_score:
            margin = black_score - white_score
            room.finish(
                "black",
                [room.players[0].id],
                f"双方停一手，黑方胜 {margin:g} 目",
            )
        else:
            margin = white_score - black_score
            room.finish(
                "white",
                [room.players[1].id],
                f"双方停一手，白方胜 {margin:g} 目",
            )

    def _area_score(self, board: list[list[int]]) -> tuple[int, int]:
        black = sum(cell == 1 for row in board for cell in row)
        white = sum(cell == 2 for row in board for cell in row)
        visited: set[tuple[int, int]] = set()
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
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
                    for neighbor in self._neighbors(*point):
                        value = board[neighbor[0]][neighbor[1]]
                        if value == 0 and neighbor not in region:
                            stack.append(neighbor)
                        elif value:
                            borders.add(value)
                if borders == {1}:
                    black += len(region)
                elif borders == {2}:
                    white += len(region)
        return black, white

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
            for neighbor in self._neighbors(*point):
                value = board[neighbor[0]][neighbor[1]]
                if value == 0:
                    liberties.add(neighbor)
                elif value == stone and neighbor not in group:
                    stack.append(neighbor)
        return group, liberties

    @staticmethod
    def _neighbors(row: int, column: int) -> list[tuple[int, int]]:
        return [
            (next_row, next_column)
            for next_row, next_column in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            )
            if 0 <= next_row < BOARD_SIZE and 0 <= next_column < BOARD_SIZE
        ]

    @staticmethod
    def _coordinate(payload: dict[str, Any], key: str) -> int:
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise GameRuleError("落子坐标格式不正确")
        if not 0 <= value < BOARD_SIZE:
            raise GameRuleError("落子位置超出棋盘")
        return value

    @staticmethod
    def _color_name(seat: int) -> str:
        return "black" if seat == 0 else "white"
