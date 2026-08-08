from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


BOARD_SIZE = 8
PROMOTION_PIECES = {"Q", "R", "B", "N"}
FILES = "abcdefgh"


def initial_board() -> list[list[str | None]]:
    board: list[list[str | None]] = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    back_rank = ["R", "N", "B", "Q", "K", "B", "N", "R"]
    board[0] = [f"b{piece}" for piece in back_rank]
    board[1] = ["bP"] * BOARD_SIZE
    board[6] = ["wP"] * BOARD_SIZE
    board[7] = [f"w{piece}" for piece in back_rank]
    return board


def initial_castling_rights() -> dict[str, bool]:
    return {
        "whiteKingside": True,
        "whiteQueenside": True,
        "blackKingside": True,
        "blackQueenside": True,
    }


@dataclass
class ChessState:
    board: list[list[str | None]] = field(default_factory=initial_board)
    turn_color: str = "white"
    castling_rights: dict[str, bool] = field(default_factory=initial_castling_rights)
    en_passant_target: tuple[int, int] | None = None
    halfmove_clock: int = 0
    fullmove_number: int = 1
    last_move: dict[str, Any] | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    captured_pieces: list[dict[str, Any]] = field(default_factory=list)
    position_history: list[str] = field(default_factory=list)


class ChessEngine:
    key = "chess"
    name = "国际象棋"
    min_players = 2
    max_players = 2

    def initial_state(self) -> ChessState:
        state = ChessState()
        state.position_history.append(self._position_key(state))
        return state

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
        state: ChessState = room.state
        player_color = self._seat_color(player.seat)
        if action == "resign":
            opponent = room.players[1 - player.seat]
            winner_color = self._seat_color(opponent.seat)
            room.finish(
                winner_color,
                [opponent.id],
                f"{player.name} 认输",
            )
            return
        if action != "move":
            raise GameRuleError("不支持这个国际象棋操作")
        if player_color != state.turn_color:
            raise GameRuleError("还没有轮到你走棋")

        source_row = self._coordinate(payload, "fromRow")
        source_column = self._coordinate(payload, "fromColumn")
        target_row = self._coordinate(payload, "toRow")
        target_column = self._coordinate(payload, "toColumn")
        board = state.board
        piece = board[source_row][source_column]
        if piece is None or self._piece_color(piece) != player_color:
            raise GameRuleError("请选择自己的棋子")

        promotion_required = piece[1] == "P" and target_row in {0, 7}
        raw_promotion = payload.get("promotion")
        promotion = raw_promotion.upper() if isinstance(raw_promotion, str) else None
        if promotion_required and promotion not in PROMOTION_PIECES:
            raise GameRuleError("请选择后、车、象或马完成升变")
        if not promotion_required and raw_promotion is not None:
            raise GameRuleError("当前走法不能升变")

        details = self._move_details(
            board,
            state.castling_rights,
            state.en_passant_target,
            player_color,
            source_row,
            source_column,
            target_row,
            target_column,
        )
        if details is None or not self._is_legal_move(
            board,
            state.castling_rights,
            state.en_passant_target,
            player_color,
            source_row,
            source_column,
            target_row,
            target_column,
        ):
            raise GameRuleError("这个走法不符合国际象棋规则")

        legal_moves_before = self._legal_moves(
            board,
            state.castling_rights,
            state.en_passant_target,
            player_color,
        )
        next_board, captured = self._apply_move(
            board,
            source_row,
            source_column,
            target_row,
            target_column,
            promotion,
            details,
        )
        self._update_castling_rights(
            state.castling_rights,
            piece,
            source_row,
            source_column,
            target_row,
            target_column,
            captured,
        )

        state.board = next_board
        state.en_passant_target = (
            ((source_row + target_row) // 2, source_column)
            if piece[1] == "P" and abs(target_row - source_row) == 2
            else None
        )
        state.halfmove_clock = (
            0 if piece[1] == "P" or captured is not None else state.halfmove_clock + 1
        )
        move_full_number = state.fullmove_number
        if player_color == "black":
            state.fullmove_number += 1
        opponent_color = self._opponent(player_color)
        state.turn_color = opponent_color

        opponent_moves = self._legal_moves(
            state.board,
            state.castling_rights,
            state.en_passant_target,
            opponent_color,
        )
        gave_check = self._in_check(state.board, opponent_color)
        is_checkmate = gave_check and not opponent_moves
        notation = self._move_notation(
            board,
            legal_moves_before,
            piece,
            source_row,
            source_column,
            target_row,
            target_column,
            captured,
            promotion,
            details,
            gave_check,
            is_checkmate,
        )
        move = {
            "number": len(state.history) + 1,
            "fullmoveNumber": move_full_number,
            "fromRow": source_row,
            "fromColumn": source_column,
            "toRow": target_row,
            "toColumn": target_column,
            "piece": piece,
            "resultPiece": f"{piece[0]}{promotion}" if promotion else piece,
            "captured": captured,
            "color": player_color,
            "promotion": promotion,
            "castle": details.get("castle"),
            "enPassant": bool(details.get("enPassant")),
            "gaveCheck": gave_check,
            "notation": notation,
        }
        state.last_move = move
        state.history.append(move)
        if captured is not None:
            state.captured_pieces.append(
                {
                    "piece": captured,
                    "capturedBy": player_color,
                    "moveNumber": len(state.history),
                }
            )
        state.position_history.append(self._position_key(state))

        if not opponent_moves:
            if gave_check:
                room.finish(player_color, [player.id], f"{player.name} 将死对方")
            else:
                room.finish("draw", [], "无子可动，逼和")
            return
        if self._insufficient_material(state.board):
            room.finish("draw", [], "子力不足，自动和棋")
            return
        if state.halfmove_clock >= 100:
            room.finish("draw", [], "连续 50 回合没有吃子或兵移动，自动和棋")
            return
        if state.position_history.count(state.position_history[-1]) >= 3:
            room.finish("draw", [], "相同局面出现三次，自动和棋")

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: ChessState = room.state
        viewer_color = self._seat_color(viewer.seat)
        legal_moves = (
            self._legal_moves(
                state.board,
                state.castling_rights,
                state.en_passant_target,
                viewer_color,
            )
            if room.phase == "playing" and viewer_color == state.turn_color
            else []
        )
        white_in_check = self._in_check(state.board, "white")
        black_in_check = self._in_check(state.board, "black")
        return {
            "board": state.board,
            "turnPlayerId": (
                room.players[0 if state.turn_color == "white" else 1].id
                if room.phase == "playing"
                else None
            ),
            "colors": {
                room.players[0].id: "white",
                room.players[1].id: "black",
            }
            if len(room.players) == 2
            else {},
            "viewerColor": viewer_color,
            "lastMove": state.last_move,
            "moveHistory": state.history,
            "capturedPieces": state.captured_pieces,
            "legalMoves": legal_moves,
            "whiteInCheck": white_in_check,
            "blackInCheck": black_in_check,
            "checkedColor": (
                "white" if white_in_check else "black" if black_in_check else None
            ),
            "halfmoveClock": state.halfmove_clock,
            "fullmoveNumber": state.fullmove_number,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        color = self._seat_color(player.seat)
        return color, color, player.id in room.winner_player_ids

    def _legal_moves(
        self,
        board: list[list[str | None]],
        castling_rights: dict[str, bool],
        en_passant_target: tuple[int, int] | None,
        color: str,
    ) -> list[dict[str, Any]]:
        moves: list[dict[str, Any]] = []
        for source_row in range(BOARD_SIZE):
            for source_column in range(BOARD_SIZE):
                piece = board[source_row][source_column]
                if piece is None or self._piece_color(piece) != color:
                    continue
                for target_row in range(BOARD_SIZE):
                    for target_column in range(BOARD_SIZE):
                        if not self._is_legal_move(
                            board,
                            castling_rights,
                            en_passant_target,
                            color,
                            source_row,
                            source_column,
                            target_row,
                            target_column,
                        ):
                            continue
                        details = self._move_details(
                            board,
                            castling_rights,
                            en_passant_target,
                            color,
                            source_row,
                            source_column,
                            target_row,
                            target_column,
                        ) or {}
                        target = board[target_row][target_column]
                        moves.append(
                            {
                                "fromRow": source_row,
                                "fromColumn": source_column,
                                "toRow": target_row,
                                "toColumn": target_column,
                                "isCapture": target is not None
                                or bool(details.get("enPassant")),
                                "promotionRequired": piece[1] == "P"
                                and target_row in {0, 7},
                                "castle": details.get("castle"),
                            }
                        )
        return moves

    def _is_legal_move(
        self,
        board: list[list[str | None]],
        castling_rights: dict[str, bool],
        en_passant_target: tuple[int, int] | None,
        color: str,
        source_row: int,
        source_column: int,
        target_row: int,
        target_column: int,
    ) -> bool:
        details = self._move_details(
            board,
            castling_rights,
            en_passant_target,
            color,
            source_row,
            source_column,
            target_row,
            target_column,
        )
        if details is None:
            return False
        piece = board[source_row][source_column]
        if piece is None:
            return False
        promotion = "Q" if piece[1] == "P" and target_row in {0, 7} else None
        next_board, _ = self._apply_move(
            board,
            source_row,
            source_column,
            target_row,
            target_column,
            promotion,
            details,
        )
        return not self._in_check(next_board, color)

    def _move_details(
        self,
        board: list[list[str | None]],
        castling_rights: dict[str, bool],
        en_passant_target: tuple[int, int] | None,
        color: str,
        source_row: int,
        source_column: int,
        target_row: int,
        target_column: int,
    ) -> dict[str, Any] | None:
        if (source_row, source_column) == (target_row, target_column):
            return None
        piece = board[source_row][source_column]
        if piece is None or self._piece_color(piece) != color:
            return None
        target = board[target_row][target_column]
        if target is not None and (
            self._piece_color(target) == color or target[1] == "K"
        ):
            return None

        row_delta = target_row - source_row
        column_delta = target_column - source_column
        absolute_row = abs(row_delta)
        absolute_column = abs(column_delta)
        kind = piece[1]

        if kind == "P":
            direction = -1 if color == "white" else 1
            start_row = 6 if color == "white" else 1
            if column_delta == 0 and row_delta == direction and target is None:
                return {}
            if (
                column_delta == 0
                and row_delta == direction * 2
                and source_row == start_row
                and target is None
                and board[source_row + direction][source_column] is None
            ):
                return {}
            if absolute_column == 1 and row_delta == direction:
                if target is not None:
                    return {}
                if en_passant_target == (target_row, target_column):
                    adjacent = board[source_row][target_column]
                    if adjacent == f"{self._piece_prefix(self._opponent(color))}P":
                        return {"enPassant": True}
            return None
        if kind == "N":
            return {} if sorted((absolute_row, absolute_column)) == [1, 2] else None
        if kind == "B":
            return (
                {}
                if absolute_row == absolute_column
                and self._path_clear(
                    board,
                    source_row,
                    source_column,
                    target_row,
                    target_column,
                )
                else None
            )
        if kind == "R":
            return (
                {}
                if (source_row == target_row or source_column == target_column)
                and self._path_clear(
                    board,
                    source_row,
                    source_column,
                    target_row,
                    target_column,
                )
                else None
            )
        if kind == "Q":
            straight = source_row == target_row or source_column == target_column
            diagonal = absolute_row == absolute_column
            return (
                {}
                if (straight or diagonal)
                and self._path_clear(
                    board,
                    source_row,
                    source_column,
                    target_row,
                    target_column,
                )
                else None
            )
        if kind == "K":
            if max(absolute_row, absolute_column) == 1:
                return {}
            if row_delta == 0 and absolute_column == 2 and self._can_castle(
                board,
                castling_rights,
                color,
                source_row,
                source_column,
                target_column,
            ):
                return {"castle": "kingside" if target_column == 6 else "queenside"}
        return None

    def _can_castle(
        self,
        board: list[list[str | None]],
        castling_rights: dict[str, bool],
        color: str,
        source_row: int,
        source_column: int,
        target_column: int,
    ) -> bool:
        home_row = 7 if color == "white" else 0
        side = "Kingside" if target_column == 6 else "Queenside"
        right_key = f"{color}{side}"
        if (
            source_row != home_row
            or source_column != 4
            or target_column not in {2, 6}
            or not castling_rights.get(right_key, False)
            or board[home_row][4] != f"{self._piece_prefix(color)}K"
        ):
            return False
        rook_column = 7 if target_column == 6 else 0
        if board[home_row][rook_column] != f"{self._piece_prefix(color)}R":
            return False
        between = range(5, 7) if target_column == 6 else range(1, 4)
        if any(board[home_row][column] is not None for column in between):
            return False
        opponent = self._opponent(color)
        pass_columns = (4, 5, 6) if target_column == 6 else (4, 3, 2)
        return not any(
            self._is_square_attacked(board, home_row, column, opponent)
            for column in pass_columns
        )

    def _apply_move(
        self,
        board: list[list[str | None]],
        source_row: int,
        source_column: int,
        target_row: int,
        target_column: int,
        promotion: str | None,
        details: dict[str, Any],
    ) -> tuple[list[list[str | None]], str | None]:
        next_board = [row[:] for row in board]
        piece = next_board[source_row][source_column]
        captured = next_board[target_row][target_column]
        if details.get("enPassant"):
            captured = next_board[source_row][target_column]
            next_board[source_row][target_column] = None
        next_board[target_row][target_column] = (
            f"{piece[0]}{promotion}" if piece is not None and promotion else piece
        )
        next_board[source_row][source_column] = None
        if details.get("castle"):
            rook_source = 7 if target_column == 6 else 0
            rook_target = 5 if target_column == 6 else 3
            next_board[target_row][rook_target] = next_board[target_row][rook_source]
            next_board[target_row][rook_source] = None
        return next_board, captured

    def _update_castling_rights(
        self,
        rights: dict[str, bool],
        piece: str,
        source_row: int,
        source_column: int,
        target_row: int,
        target_column: int,
        captured: str | None,
    ) -> None:
        color = self._piece_color(piece)
        if piece[1] == "K":
            rights[f"{color}Kingside"] = False
            rights[f"{color}Queenside"] = False
        if piece[1] == "R":
            self._disable_rook_right(rights, color, source_row, source_column)
        if captured is not None and captured[1] == "R":
            self._disable_rook_right(
                rights,
                self._piece_color(captured),
                target_row,
                target_column,
            )

    @staticmethod
    def _disable_rook_right(
        rights: dict[str, bool], color: str, row: int, column: int
    ) -> None:
        home_row = 7 if color == "white" else 0
        if row != home_row:
            return
        if column == 0:
            rights[f"{color}Queenside"] = False
        elif column == 7:
            rights[f"{color}Kingside"] = False

    def _in_check(self, board: list[list[str | None]], color: str) -> bool:
        king = f"{self._piece_prefix(color)}K"
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                if board[row][column] == king:
                    return self._is_square_attacked(
                        board,
                        row,
                        column,
                        self._opponent(color),
                    )
        return True

    def _is_square_attacked(
        self,
        board: list[list[str | None]],
        row: int,
        column: int,
        by_color: str,
    ) -> bool:
        prefix = self._piece_prefix(by_color)
        pawn_direction = -1 if by_color == "white" else 1
        pawn_row = row - pawn_direction
        for pawn_column in (column - 1, column + 1):
            if self._inside(pawn_row, pawn_column) and board[pawn_row][pawn_column] == f"{prefix}P":
                return True

        for row_delta, column_delta in (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ):
            source_row, source_column = row + row_delta, column + column_delta
            if self._inside(source_row, source_column) and board[source_row][source_column] == f"{prefix}N":
                return True

        for source_row in range(max(0, row - 1), min(BOARD_SIZE, row + 2)):
            for source_column in range(max(0, column - 1), min(BOARD_SIZE, column + 2)):
                if (source_row, source_column) != (row, column) and board[source_row][source_column] == f"{prefix}K":
                    return True

        directions = (
            (-1, 0, {"R", "Q"}),
            (1, 0, {"R", "Q"}),
            (0, -1, {"R", "Q"}),
            (0, 1, {"R", "Q"}),
            (-1, -1, {"B", "Q"}),
            (-1, 1, {"B", "Q"}),
            (1, -1, {"B", "Q"}),
            (1, 1, {"B", "Q"}),
        )
        for row_delta, column_delta, attackers in directions:
            source_row, source_column = row + row_delta, column + column_delta
            while self._inside(source_row, source_column):
                piece = board[source_row][source_column]
                if piece is not None:
                    if piece[0] == prefix and piece[1] in attackers:
                        return True
                    break
                source_row += row_delta
                source_column += column_delta
        return False

    @staticmethod
    def _path_clear(
        board: list[list[str | None]],
        source_row: int,
        source_column: int,
        target_row: int,
        target_column: int,
    ) -> bool:
        row_step = (target_row > source_row) - (target_row < source_row)
        column_step = (target_column > source_column) - (
            target_column < source_column
        )
        row, column = source_row + row_step, source_column + column_step
        while (row, column) != (target_row, target_column):
            if board[row][column] is not None:
                return False
            row += row_step
            column += column_step
        return True

    def _move_notation(
        self,
        board: list[list[str | None]],
        legal_moves: list[dict[str, Any]],
        piece: str,
        source_row: int,
        source_column: int,
        target_row: int,
        target_column: int,
        captured: str | None,
        promotion: str | None,
        details: dict[str, Any],
        gave_check: bool,
        is_checkmate: bool,
    ) -> str:
        castle = details.get("castle")
        if castle:
            notation = "O-O" if castle == "kingside" else "O-O-O"
        else:
            kind = piece[1]
            capture = captured is not None
            prefix = "" if kind == "P" else kind
            if kind == "P" and capture:
                prefix = FILES[source_column]
            elif kind != "P":
                alternatives = [
                    move
                    for move in legal_moves
                    if (move["fromRow"], move["fromColumn"])
                    != (source_row, source_column)
                    and (move["toRow"], move["toColumn"])
                    == (target_row, target_column)
                    and board[move["fromRow"]][move["fromColumn"]] == piece
                ]
                if alternatives:
                    same_file = any(
                        move["fromColumn"] == source_column for move in alternatives
                    )
                    same_rank = any(
                        move["fromRow"] == source_row for move in alternatives
                    )
                    if not same_file:
                        prefix += FILES[source_column]
                    elif not same_rank:
                        prefix += str(8 - source_row)
                    else:
                        prefix += f"{FILES[source_column]}{8 - source_row}"
            notation = (
                f"{prefix}{'x' if capture else ''}"
                f"{self._square_name(target_row, target_column)}"
                f"{'=' + promotion if promotion else ''}"
            )
        if is_checkmate:
            return f"{notation}#"
        if gave_check:
            return f"{notation}+"
        return notation

    def _position_key(self, state: ChessState) -> str:
        board_key = "/".join(
            "".join(piece or "--" for piece in row) for row in state.board
        )
        rights = "".join(
            letter
            for letter, key in (
                ("K", "whiteKingside"),
                ("Q", "whiteQueenside"),
                ("k", "blackKingside"),
                ("q", "blackQueenside"),
            )
            if state.castling_rights.get(key, False)
        ) or "-"
        en_passant = self._repetition_en_passant(state)
        return f"{board_key} {state.turn_color} {rights} {en_passant}"

    def _repetition_en_passant(self, state: ChessState) -> str:
        """Only record an en-passant square when it changes the legal moves."""
        if state.en_passant_target is None:
            return "-"
        target_row, target_column = state.en_passant_target
        direction = -1 if state.turn_color == "white" else 1
        source_row = target_row - direction
        pawn = f"{self._piece_prefix(state.turn_color)}P"
        for source_column in (target_column - 1, target_column + 1):
            if not 0 <= source_column < BOARD_SIZE:
                continue
            if not 0 <= source_row < BOARD_SIZE:
                continue
            if state.board[source_row][source_column] != pawn:
                continue
            if self._is_legal_move(
                state.board,
                state.castling_rights,
                state.en_passant_target,
                state.turn_color,
                source_row,
                source_column,
                target_row,
                target_column,
            ):
                return self._square_name(target_row, target_column)
        return "-"

    @staticmethod
    def _insufficient_material(board: list[list[str | None]]) -> bool:
        pieces = [
            (piece, row, column)
            for row, board_row in enumerate(board)
            for column, piece in enumerate(board_row)
            if piece is not None and piece[1] != "K"
        ]
        if not pieces:
            return True
        if len(pieces) == 1 and pieces[0][0][1] in {"B", "N"}:
            return True
        if all(item[0][1] == "B" for item in pieces):
            square_colors = {(row + column) % 2 for _, row, column in pieces}
            return len(square_colors) == 1
        return False

    @staticmethod
    def _coordinate(payload: dict[str, Any], key: str) -> int:
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < BOARD_SIZE:
            raise GameRuleError("棋盘坐标不正确")
        return value

    @staticmethod
    def _seat_color(seat: int) -> str:
        return "white" if seat == 0 else "black"

    @staticmethod
    def _piece_prefix(color: str) -> str:
        return "w" if color == "white" else "b"

    @staticmethod
    def _piece_color(piece: str) -> str:
        return "white" if piece[0] == "w" else "black"

    @staticmethod
    def _opponent(color: str) -> str:
        return "black" if color == "white" else "white"

    @staticmethod
    def _inside(row: int, column: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE

    @staticmethod
    def _square_name(row: int, column: int) -> str:
        return f"{FILES[column]}{8 - row}"
