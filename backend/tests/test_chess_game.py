from __future__ import annotations

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.chess.engine import ChessEngine, ChessState


def make_room(engine: ChessEngine) -> ArcadeRoom:
    players = [
        ArcadePlayer(
            id=f"p{seat}",
            account_id=f"a{seat}",
            name=f"玩家{seat + 1}",
            token_hash=f"token-{seat}",
            seat=seat,
        )
        for seat in range(2)
    ]
    room = ArcadeRoom(
        code="CHESS",
        game_key="chess",
        host_id=players[0].id,
        players=players,
        state=engine.initial_state(),
        game_id="chess-game",
        started_at="2026-08-08T00:00:00+00:00",
        options={},
    )
    engine.start(room)
    return room


def empty_board() -> list[list[str | None]]:
    return [[None] * 8 for _ in range(8)]


def move(
    engine: ChessEngine,
    room: ArcadeRoom,
    player_index: int,
    source: tuple[int, int],
    target: tuple[int, int],
    promotion: str | None = None,
) -> None:
    payload = {
        "fromRow": source[0],
        "fromColumn": source[1],
        "toRow": target[0],
        "toColumn": target[1],
    }
    if promotion is not None:
        payload["promotion"] = promotion
    engine.act(room, room.players[player_index], "move", payload)


def test_chess_starts_with_white_and_validates_turns() -> None:
    engine = ChessEngine()
    room = make_room(engine)

    move(engine, room, 0, (6, 4), (4, 4))

    assert room.state.board[4][4] == "wP"
    assert room.state.turn_color == "black"
    assert room.state.en_passant_target == (5, 4)
    assert room.state.history[-1]["notation"] == "e4"
    with pytest.raises(GameRuleError, match="还没有轮到你"):
        move(engine, room, 0, (6, 3), (4, 3))


def test_chess_rejects_moves_that_expose_own_king() -> None:
    engine = ChessEngine()
    room = make_room(engine)
    board = empty_board()
    board[0][0] = "bK"
    board[0][4] = "bR"
    board[6][4] = "wR"
    board[7][4] = "wK"
    room.state = ChessState(
        board=board,
        castling_rights={key: False for key in room.state.castling_rights},
    )

    with pytest.raises(GameRuleError, match="不符合国际象棋规则"):
        move(engine, room, 0, (6, 4), (6, 5))

    assert room.state.board[6][4] == "wR"


def test_chess_castles_and_rejects_castling_through_check() -> None:
    engine = ChessEngine()
    room = make_room(engine)
    board = empty_board()
    board[0][4] = "bK"
    board[7][4] = "wK"
    board[7][7] = "wR"
    room.state = ChessState(board=board)

    move(engine, room, 0, (7, 4), (7, 6))

    assert room.state.board[7][6] == "wK"
    assert room.state.board[7][5] == "wR"
    assert room.state.history[-1]["notation"] == "O-O"
    assert room.state.castling_rights["whiteKingside"] is False

    attacked = empty_board()
    attacked[0][0] = "bK"
    attacked[0][5] = "bR"
    attacked[7][4] = "wK"
    attacked[7][7] = "wR"
    assert engine._is_legal_move(
        attacked,
        {
            "whiteKingside": True,
            "whiteQueenside": False,
            "blackKingside": False,
            "blackQueenside": False,
        },
        None,
        "white",
        7,
        4,
        7,
        6,
    ) is False


def test_chess_supports_en_passant_on_the_immediately_following_move() -> None:
    engine = ChessEngine()
    room = make_room(engine)
    board = empty_board()
    board[0][4] = "bK"
    board[1][3] = "bP"
    board[3][4] = "wP"
    board[7][4] = "wK"
    room.state = ChessState(
        board=board,
        turn_color="black",
        castling_rights={key: False for key in room.state.castling_rights},
    )

    move(engine, room, 1, (1, 3), (3, 3))
    move(engine, room, 0, (3, 4), (2, 3))

    assert room.state.board[2][3] == "wP"
    assert room.state.board[3][3] is None
    assert room.state.history[-1]["enPassant"] is True
    assert room.state.history[-1]["captured"] == "bP"
    assert room.state.history[-1]["notation"] == "exd6"


def test_chess_requires_and_applies_pawn_promotion() -> None:
    engine = ChessEngine()
    room = make_room(engine)
    board = empty_board()
    board[0][7] = "bK"
    board[1][0] = "wP"
    board[7][7] = "wK"
    room.state = ChessState(
        board=board,
        castling_rights={key: False for key in room.state.castling_rights},
    )

    with pytest.raises(GameRuleError, match="完成升变"):
        move(engine, room, 0, (1, 0), (0, 0))

    move(engine, room, 0, (1, 0), (0, 0), "N")
    assert room.state.board[0][0] == "wN"
    assert room.state.history[-1]["promotion"] == "N"
    assert room.state.history[-1]["notation"] == "a8=N"
    assert room.winner == "draw"
    assert "子力不足" in (room.win_reason or "")


def test_chess_detects_fools_mate_and_records_standard_notation() -> None:
    engine = ChessEngine()
    room = make_room(engine)

    move(engine, room, 0, (6, 5), (5, 5))
    move(engine, room, 1, (1, 4), (3, 4))
    move(engine, room, 0, (6, 6), (4, 6))
    move(engine, room, 1, (0, 3), (4, 7))

    assert room.phase == "finished"
    assert room.winner == "black"
    assert room.winner_player_ids == [room.players[1].id]
    assert room.state.history[-1]["notation"] == "Qh4#"
    assert "将死" in (room.win_reason or "")


def test_chess_identifies_stalemate_and_insufficient_material() -> None:
    engine = ChessEngine()
    stalemate = empty_board()
    stalemate[0][0] = "bK"
    stalemate[2][1] = "wQ"
    stalemate[2][2] = "wK"
    rights = {
        "whiteKingside": False,
        "whiteQueenside": False,
        "blackKingside": False,
        "blackQueenside": False,
    }

    assert engine._in_check(stalemate, "black") is False
    assert engine._legal_moves(stalemate, rights, None, "black") == []

    kings = empty_board()
    kings[0][0] = "bK"
    kings[7][7] = "wK"
    assert engine._insufficient_material(kings) is True
    kings[6][5] = "wB"
    assert engine._insufficient_material(kings) is True
    kings[5][4] = "wN"
    assert engine._insufficient_material(kings) is False


def test_chess_automatically_draws_on_third_repetition() -> None:
    engine = ChessEngine()
    room = make_room(engine)

    for _ in range(2):
        move(engine, room, 0, (7, 6), (5, 5))
        move(engine, room, 1, (0, 6), (2, 5))
        move(engine, room, 0, (5, 5), (7, 6))
        move(engine, room, 1, (2, 5), (0, 6))

    assert room.phase == "finished"
    assert room.winner == "draw"
    assert "三次" in (room.win_reason or "")


def test_chess_repetition_key_only_includes_a_legal_en_passant_capture() -> None:
    engine = ChessEngine()
    state = engine.initial_state()
    state.en_passant_target = (5, 4)
    state.turn_color = "black"

    assert engine._position_key(state).endswith(" black KQkq -")

    board = empty_board()
    board[0][4] = "bK"
    board[3][3] = "bP"
    board[3][4] = "wP"
    board[7][4] = "wK"
    state = ChessState(
        board=board,
        en_passant_target=(2, 3),
        castling_rights={key: False for key in state.castling_rights},
    )

    assert engine._position_key(state).endswith(" white - d6")


def test_chess_automatically_draws_after_fifty_quiet_rounds() -> None:
    engine = ChessEngine()
    room = make_room(engine)
    room.state.halfmove_clock = 99

    move(engine, room, 0, (7, 6), (5, 5))

    assert room.winner == "draw"
    assert "50 回合" in (room.win_reason or "")


def test_chess_view_only_exposes_moves_to_the_current_player() -> None:
    engine = ChessEngine()
    room = make_room(engine)

    white_view = engine.view(room, room.players[0])
    black_view = engine.view(room, room.players[1])

    assert any(
        move_item["fromRow"] == 6
        and move_item["fromColumn"] == 4
        and move_item["toRow"] == 4
        and move_item["toColumn"] == 4
        for move_item in white_view["legalMoves"]
    )
    assert black_view["legalMoves"] == []
    assert white_view["viewerColor"] == "white"
    assert black_view["viewerColor"] == "black"
