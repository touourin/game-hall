from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


BOARD_SIZE = 15


@dataclass
class GomokuState:
    board: list[list[int]] = field(
        default_factory=lambda: [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    )
    turn_seat: int = 0
    moves: list[dict[str, int]] = field(default_factory=list)


class GomokuEngine:
    key = "gomoku"
    name = "五子棋"
    min_players = 2
    max_players = 2

    def initial_state(self) -> GomokuState:
        return GomokuState()

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
        state: GomokuState = room.state
        if action == "resign":
            opponent = room.players[1 - player.seat]
            room.finish(
                self._color_name(opponent.seat),
                [opponent.id],
                f"{player.name} 认输",
            )
            return
        if action != "place":
            raise GameRuleError("不支持这个五子棋操作")
        if player.seat != state.turn_seat:
            raise GameRuleError("还没有轮到你落子")
        row = self._coordinate(payload, "row")
        column = self._coordinate(payload, "column")
        if state.board[row][column] != 0:
            raise GameRuleError("这个位置已经有棋子")
        stone = player.seat + 1
        state.board[row][column] = stone
        state.moves.append({"row": row, "column": column, "stone": stone})
        if self._has_five(state.board, row, column, stone):
            room.finish(
                self._color_name(player.seat),
                [player.id],
                f"{player.name} 连成五子",
            )
            return
        if len(state.moves) == BOARD_SIZE * BOARD_SIZE:
            room.finish("draw", [], "棋盘已满，双方和棋")
            return
        state.turn_seat = 1 - state.turn_seat

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: GomokuState = room.state
        return {
            "boardSize": BOARD_SIZE,
            "board": state.board,
            "turnPlayerId": (
                room.players[state.turn_seat].id
                if room.phase == "playing"
                else None
            ),
            "lastMove": state.moves[-1] if state.moves else None,
            "colors": {
                room.players[0].id: "black",
                room.players[1].id: "white",
            }
            if len(room.players) == 2
            else {},
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        color = "black" if player.seat == 0 else "white"
        return color, color, player.id in room.winner_player_ids

    @staticmethod
    def _coordinate(payload: dict[str, Any], key: str) -> int:
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise GameRuleError("落子坐标格式不正确")
        if not 0 <= value < BOARD_SIZE:
            raise GameRuleError("落子位置超出棋盘")
        return value

    @staticmethod
    def _has_five(
        board: list[list[int]], row: int, column: int, stone: int
    ) -> bool:
        for row_step, column_step in ((1, 0), (0, 1), (1, 1), (1, -1)):
            count = 1
            for direction in (-1, 1):
                next_row = row + row_step * direction
                next_column = column + column_step * direction
                while (
                    0 <= next_row < BOARD_SIZE
                    and 0 <= next_column < BOARD_SIZE
                    and board[next_row][next_column] == stone
                ):
                    count += 1
                    next_row += row_step * direction
                    next_column += column_step * direction
            if count >= 5:
                return True
        return False

    @staticmethod
    def _color_name(seat: int) -> str:
        return "black" if seat == 0 else "white"
