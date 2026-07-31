from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


ROWS = 10
COLUMNS = 9


def initial_board() -> list[list[str | None]]:
    board: list[list[str | None]] = [[None] * COLUMNS for _ in range(ROWS)]
    back_rank = ["R", "H", "E", "A", "K", "A", "E", "H", "R"]
    board[0] = [f"b{piece}" for piece in back_rank]
    board[2][1] = board[2][7] = "bC"
    for column in range(0, COLUMNS, 2):
        board[3][column] = "bP"
        board[6][column] = "rP"
    board[7][1] = board[7][7] = "rC"
    board[9] = [f"r{piece}" for piece in back_rank]
    return board


@dataclass
class XiangqiState:
    board: list[list[str | None]] = field(default_factory=initial_board)
    turn_color: str = "red"
    last_move: dict[str, int | str] | None = None
    move_count: int = 0


class XiangqiEngine:
    key = "xiangqi"
    name = "中国象棋"
    min_players = 2
    max_players = 2

    def initial_state(self) -> XiangqiState:
        return XiangqiState()

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
        state: XiangqiState = room.state
        player_color = self._seat_color(player.seat)
        if action == "resign":
            opponent = room.players[1 - player.seat]
            room.finish(
                self._seat_color(opponent.seat),
                [opponent.id],
                f"{player.name} 认输",
            )
            return
        if action != "move":
            raise GameRuleError("不支持这个象棋操作")
        if player_color != state.turn_color:
            raise GameRuleError("还没有轮到你走棋")
        source_row = self._coordinate(payload, "fromRow", ROWS)
        source_column = self._coordinate(payload, "fromColumn", COLUMNS)
        target_row = self._coordinate(payload, "toRow", ROWS)
        target_column = self._coordinate(payload, "toColumn", COLUMNS)
        board = state.board
        piece = board[source_row][source_column]
        if piece is None or self._piece_color(piece) != player_color:
            raise GameRuleError("请选择自己的棋子")
        if not self._is_legal_move(
            board,
            player_color,
            source_row,
            source_column,
            target_row,
            target_column,
        ):
            raise GameRuleError("这个走法不符合象棋规则")
        captured = board[target_row][target_column]
        board[target_row][target_column] = piece
        board[source_row][source_column] = None
        state.last_move = {
            "fromRow": source_row,
            "fromColumn": source_column,
            "toRow": target_row,
            "toColumn": target_column,
            "piece": piece,
        }
        state.move_count += 1
        opponent_color = self._opponent(player_color)
        if captured is not None and captured[1] == "K":
            room.finish(player_color, [player.id], f"{player.name} 将死对方")
            return
        if not self._has_legal_move(board, opponent_color):
            reason = "将死" if self._in_check(board, opponent_color) else "困毙"
            room.finish(player_color, [player.id], f"{player.name} {reason}对方")
            return
        state.turn_color = opponent_color

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: XiangqiState = room.state
        return {
            "board": state.board,
            "turnPlayerId": (
                room.players[0 if state.turn_color == "red" else 1].id
                if room.phase == "playing"
                else None
            ),
            "colors": {
                room.players[0].id: "red",
                room.players[1].id: "black",
            }
            if len(room.players) == 2
            else {},
            "lastMove": state.last_move,
            "redInCheck": self._in_check(state.board, "red"),
            "blackInCheck": self._in_check(state.board, "black"),
            "viewerColor": self._seat_color(viewer.seat),
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        color = self._seat_color(player.seat)
        return color, color, player.id in room.winner_player_ids

    def _is_legal_move(
        self,
        board: list[list[str | None]],
        color: str,
        source_row: int,
        source_column: int,
        target_row: int,
        target_column: int,
    ) -> bool:
        piece = board[source_row][source_column]
        if piece is None or self._piece_color(piece) != color:
            return False
        target = board[target_row][target_column]
        if target is not None and self._piece_color(target) == color:
            return False
        if not self._piece_can_move(
            board,
            piece,
            source_row,
            source_column,
            target_row,
            target_column,
        ):
            return False
        next_board = [row[:] for row in board]
        next_board[target_row][target_column] = piece
        next_board[source_row][source_column] = None
        return not self._in_check(next_board, color)

    def _piece_can_move(
        self,
        board: list[list[str | None]],
        piece: str,
        source_row: int,
        source_column: int,
        target_row: int,
        target_column: int,
    ) -> bool:
        if source_row == target_row and source_column == target_column:
            return False
        color = self._piece_color(piece)
        kind = piece[1]
        row_delta = target_row - source_row
        column_delta = target_column - source_column
        absolute_row = abs(row_delta)
        absolute_column = abs(column_delta)

        if kind == "K":
            target = board[target_row][target_column]
            if (
                target is not None
                and target[1] == "K"
                and source_column == target_column
            ):
                return self._pieces_between(
                    board,
                    source_row,
                    source_column,
                    target_row,
                    target_column,
                ) == 0
            return (
                absolute_row + absolute_column == 1
                and self._inside_palace(color, target_row, target_column)
            )
        if kind == "A":
            return (
                absolute_row == absolute_column == 1
                and self._inside_palace(color, target_row, target_column)
            )
        if kind == "E":
            if absolute_row != 2 or absolute_column != 2:
                return False
            if color == "red" and target_row < 5:
                return False
            if color == "black" and target_row > 4:
                return False
            return board[source_row + row_delta // 2][
                source_column + column_delta // 2
            ] is None
        if kind == "H":
            if sorted((absolute_row, absolute_column)) != [1, 2]:
                return False
            if absolute_row == 2:
                leg_row, leg_column = source_row + row_delta // 2, source_column
            else:
                leg_row, leg_column = source_row, source_column + column_delta // 2
            return board[leg_row][leg_column] is None
        if kind == "R":
            return (
                source_row == target_row or source_column == target_column
            ) and self._pieces_between(
                board,
                source_row,
                source_column,
                target_row,
                target_column,
            ) == 0
        if kind == "C":
            if source_row != target_row and source_column != target_column:
                return False
            screens = self._pieces_between(
                board,
                source_row,
                source_column,
                target_row,
                target_column,
            )
            return screens == (1 if board[target_row][target_column] else 0)
        if kind == "P":
            forward = -1 if color == "red" else 1
            if row_delta == forward and column_delta == 0:
                return True
            crossed_river = source_row <= 4 if color == "red" else source_row >= 5
            return crossed_river and row_delta == 0 and absolute_column == 1
        return False

    def _in_check(self, board: list[list[str | None]], color: str) -> bool:
        king_position: tuple[int, int] | None = None
        for row in range(ROWS):
            for column in range(COLUMNS):
                if board[row][column] == ("rK" if color == "red" else "bK"):
                    king_position = (row, column)
                    break
            if king_position is not None:
                break
        if king_position is None:
            return True
        for row in range(ROWS):
            for column in range(COLUMNS):
                piece = board[row][column]
                if piece is None or self._piece_color(piece) == color:
                    continue
                if self._piece_can_move(
                    board,
                    piece,
                    row,
                    column,
                    king_position[0],
                    king_position[1],
                ):
                    return True
        return False

    def _has_legal_move(
        self, board: list[list[str | None]], color: str
    ) -> bool:
        for source_row in range(ROWS):
            for source_column in range(COLUMNS):
                piece = board[source_row][source_column]
                if piece is None or self._piece_color(piece) != color:
                    continue
                for target_row in range(ROWS):
                    for target_column in range(COLUMNS):
                        if self._is_legal_move(
                            board,
                            color,
                            source_row,
                            source_column,
                            target_row,
                            target_column,
                        ):
                            return True
        return False

    @staticmethod
    def _pieces_between(
        board: list[list[str | None]],
        source_row: int,
        source_column: int,
        target_row: int,
        target_column: int,
    ) -> int:
        if source_row == target_row:
            start, end = sorted((source_column, target_column))
            return sum(
                board[source_row][column] is not None
                for column in range(start + 1, end)
            )
        if source_column == target_column:
            start, end = sorted((source_row, target_row))
            return sum(
                board[row][source_column] is not None
                for row in range(start + 1, end)
            )
        return -1

    @staticmethod
    def _inside_palace(color: str, row: int, column: int) -> bool:
        if not 3 <= column <= 5:
            return False
        return 7 <= row <= 9 if color == "red" else 0 <= row <= 2

    @staticmethod
    def _piece_color(piece: str) -> str:
        return "red" if piece[0] == "r" else "black"

    @staticmethod
    def _opponent(color: str) -> str:
        return "black" if color == "red" else "red"

    @staticmethod
    def _seat_color(seat: int) -> str:
        return "red" if seat == 0 else "black"

    @staticmethod
    def _coordinate(payload: dict[str, Any], key: str, limit: int) -> int:
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise GameRuleError("走棋坐标格式不正确")
        if not 0 <= value < limit:
            raise GameRuleError("走棋位置超出棋盘")
        return value
