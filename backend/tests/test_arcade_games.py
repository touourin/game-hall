from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.accounts import AccountStore
from backend.app.arcade.models import ArcadePlayer, ArcadeRoom, ArcadeSpectator
from backend.app.arcade.rooms import (
    ActiveRoomError,
    ArcadeRoomError,
    ArcadeRoomManager,
)
from backend.app.arcade.views import (
    build_lobby_view as build_arcade_lobby_view,
    build_room_view as build_arcade_room_view,
    build_spectator_room_view,
)
from backend.app.games.base import GameRuleError
from backend.app.games.catalog import BUILTIN_GAME_NAMES
from backend.app.games.doudizhu.engine import (
    Card,
    DoudizhuEngine,
    PlayPattern,
    beats,
    classify_cards,
    create_deck,
)
from backend.app.games.go import GoEngine
from backend.app.games.gomoku import GomokuEngine
from backend.app.games.hanoi import HanoiEngine
from backend.app.games.junqi.engine import JunqiEngine, JunqiPiece, JunqiState
from backend.app.games.reaction import ReactionEngine
from backend.app.games.registry import build_engine_registry
from backend.app.games.xiangqi import XiangqiEngine
from backend.app.games.xiangqi.engine import XiangqiState


def test_builtin_game_catalog_matches_engine_registry() -> None:
    builtin_engine_keys = {
        key for key in build_engine_registry() if not key.startswith("plugin-")
    }

    assert builtin_engine_keys == set(BUILTIN_GAME_NAMES)


def test_every_enabled_game_can_render_an_exact_player_spectator_view() -> None:
    engines = build_engine_registry()
    manager = ArcadeRoomManager(engines)

    for game_key, engine in engines.items():
        room, target, _ = manager.create_room(
            game_key,
            "视角玩家",
            f"target-{game_key}",
        )
        spectator = ArcadeSpectator(
            id=f"spectator-{game_key}",
            account_id=f"spectator-account-{game_key}",
            name="观众",
            target_player_id=target.id,
        )

        view = build_spectator_room_view(
            room,
            target,
            spectator,
            engine,
            [spectator],
        )

        assert view["game"] == engine.view(room, target)
        assert view["self"]["id"] == target.id
        assert view["viewer"]["mode"] == "spectator"
        assert view["viewer"]["targetPlayerId"] == target.id
        assert not any(view["actions"].values())


def make_room(
    engine, player_count: int, options: dict | None = None
) -> ArcadeRoom:
    players = [
        ArcadePlayer(
            id=f"p{seat}",
            account_id=f"a{seat}",
            name=f"玩家{seat + 1}",
            token_hash=f"token-{seat}",
            seat=seat,
        )
        for seat in range(player_count)
    ]
    room = ArcadeRoom(
        code="TEST",
        game_key=engine.key,
        host_id=players[0].id,
        players=players,
        state=engine.initial_state(),
        game_id="game-test",
        started_at="2026-08-01T00:00:00+00:00",
        options=options or {},
    )
    engine.start(room)
    return room


def test_gomoku_enforces_turns_and_detects_five() -> None:
    engine = GomokuEngine()
    room = make_room(engine, 2)

    with pytest.raises(GameRuleError, match="轮到"):
        engine.act(room, room.players[1], "place", {"row": 3, "column": 3})

    for column in range(4):
        engine.act(room, room.players[0], "place", {"row": 7, "column": column})
        engine.act(room, room.players[1], "place", {"row": 8, "column": column})
    engine.act(room, room.players[0], "place", {"row": 7, "column": 4})

    assert room.phase == "finished"
    assert room.winner == "black"
    assert room.winner_player_ids == [room.players[0].id]


def test_gomoku_uses_fifteen_lines_and_supports_exact_five_rules() -> None:
    engine = GomokuEngine()
    exact_room = make_room(
        engine,
        2,
        {"winRule": "exact_five"},
    )
    assert len(exact_room.state.board) == 15

    for index, column in enumerate((0, 1, 2, 4, 5)):
        engine.act(
            exact_room,
            exact_room.players[0],
            "place",
            {"row": 7, "column": column},
        )
        engine.act(
            exact_room,
            exact_room.players[1],
            "place",
            {"row": 10, "column": index * 2},
        )
    engine.act(
        exact_room,
        exact_room.players[0],
        "place",
        {"row": 7, "column": 3},
    )
    assert exact_room.phase == "playing"

    freestyle_room = make_room(
        engine,
        2,
        {"winRule": "freestyle"},
    )
    for index, column in enumerate((0, 1, 2, 4, 5)):
        engine.act(
            freestyle_room,
            freestyle_room.players[0],
            "place",
            {"row": 7, "column": column},
        )
        engine.act(
            freestyle_room,
            freestyle_room.players[1],
            "place",
            {"row": 10, "column": index * 2},
        )
    engine.act(
        freestyle_room,
        freestyle_room.players[0],
        "place",
        {"row": 7, "column": 3},
    )
    assert freestyle_room.phase == "finished"


def test_renju_requires_the_first_black_move_at_the_center() -> None:
    engine = GomokuEngine()
    room = make_room(engine, 2, {"winRule": "renju"})

    with pytest.raises(GameRuleError, match="天元"):
        engine.act(
            room,
            room.players[0],
            "place",
            {"row": 0, "column": 0},
        )

    engine.act(
        room,
        room.players[0],
        "place",
        {"row": 7, "column": 7},
    )
    assert room.state.board[7][7] == 1
    assert room.state.turn_seat == 1


@pytest.mark.parametrize(
    ("black_stones", "move", "expected"),
    [
        (
            [(7, 5), (7, 6), (7, 8), (5, 7), (6, 7), (8, 7)],
            (7, 7),
            (False, "四四"),
        ),
        (
            [(7, 6), (7, 8), (6, 7), (8, 7)],
            (7, 7),
            (False, "三三"),
        ),
        (
            [(1, 0), (1, 2), (0, 1), (2, 1)],
            (1, 1),
            (False, None),
        ),
        (
            [(7, 5), (7, 6), (7, 8), (6, 7), (8, 7)],
            (7, 7),
            (False, None),
        ),
        (
            [(7, column) for column in range(3, 8)],
            (7, 8),
            (False, "长连"),
        ),
    ],
)
def test_renju_classifies_core_forbidden_patterns(
    black_stones: list[tuple[int, int]],
    move: tuple[int, int],
    expected: tuple[bool, str | None],
) -> None:
    engine = GomokuEngine()
    board = [[0] * 15 for _ in range(15)]
    for row, column in black_stones:
        board[row][column] = 1

    assert engine._analyze_black_move(board, *move) == expected


def test_renju_ignores_a_three_when_all_extensions_are_forbidden() -> None:
    engine = GomokuEngine()
    board = [[0] * 15 for _ in range(15)]
    for row, column in [
        (7, 6),
        (7, 8),
        (6, 7),
        (8, 7),
        (5, 5),
        (6, 5),
        (8, 5),
        (5, 9),
        (6, 9),
        (8, 9),
    ]:
        board[row][column] = 1

    assert engine._analyze_black_move(board, 7, 7) == (False, None)


def test_renju_exact_five_has_priority_over_an_overline() -> None:
    engine = GomokuEngine()
    board = [[0] * 15 for _ in range(15)]
    for column in range(3, 8):
        board[8][column] = 1
    for row in range(4, 8):
        board[row][8] = 1

    assert engine._analyze_black_move(board, 8, 8) == (True, None)


def test_renju_rejects_black_forbidden_move_without_mutating_board() -> None:
    engine = GomokuEngine()
    room = make_room(engine, 2, {"winRule": "renju"})
    for row, column in [(7, 6), (7, 8), (6, 7), (8, 7)]:
        room.state.board[row][column] = 1
        room.state.moves.append({"row": row, "column": column, "stone": 1})

    with pytest.raises(GameRuleError, match="三三"):
        engine.act(
            room,
            room.players[0],
            "place",
            {"row": 7, "column": 7},
        )

    assert room.state.board[7][7] == 0
    assert room.state.turn_seat == 0


def test_renju_white_can_win_with_an_overline() -> None:
    engine = GomokuEngine()
    room = make_room(engine, 2, {"winRule": "renju"})
    room.state.turn_seat = 1
    for column in range(3, 8):
        room.state.board[7][column] = 2
        room.state.moves.append({"row": 7, "column": column, "stone": 2})

    engine.act(
        room,
        room.players[1],
        "place",
        {"row": 7, "column": 8},
    )

    assert room.phase == "finished"
    assert room.winner == "white"


def test_renju_view_exposes_forbidden_points_with_reasons() -> None:
    engine = GomokuEngine()
    room = make_room(engine, 2, {"winRule": "renju"})
    for row, column in [(7, 6), (7, 8), (6, 7), (8, 7)]:
        room.state.board[row][column] = 1
        room.state.moves.append({"row": row, "column": column, "stone": 1})

    view = engine.view(room, room.players[0])
    assert {"row": 7, "column": 7, "reason": "三三"} in view[
        "forbiddenPoints"
    ]


def test_gomoku_swap2_can_keep_or_exchange_the_initial_colors() -> None:
    engine = GomokuEngine()
    room = make_room(
        engine,
        2,
        {
            "winRule": "freestyle",
            "openingRule": "swap2",
        },
    )
    first, second = room.players

    for row, column in [(7, 7), (7, 8), (8, 8)]:
        engine.act(
            room,
            first,
            "place",
            {"row": row, "column": column},
        )

    assert [move["stone"] for move in room.state.moves] == [1, 2, 1]
    assert room.state.swap2_stage == "second_choice"
    assert room.state.turn_seat == second.seat

    engine.act(room, second, "swap2_choose", {"choice": "black"})

    assert room.state.swap2_stage is None
    assert room.state.seat_stones == [2, 1]
    assert room.state.turn_seat == first.seat
    view = engine.view(room, first)
    assert view["colors"] == {first.id: "white", second.id: "black"}
    assert view["turnPlayerId"] == first.id


def test_gomoku_swap2_can_add_two_stones_before_first_player_chooses() -> None:
    engine = GomokuEngine()
    room = make_room(
        engine,
        2,
        {
            "winRule": "freestyle",
            "openingRule": "swap2",
        },
    )
    first, second = room.players
    for row, column in [(7, 7), (7, 8), (8, 8)]:
        engine.act(
            room,
            first,
            "place",
            {"row": row, "column": column},
        )

    engine.act(room, second, "swap2_choose", {"choice": "add"})
    engine.act(room, second, "place", {"row": 8, "column": 7})
    engine.act(room, second, "place", {"row": 9, "column": 7})

    assert [move["stone"] for move in room.state.moves] == [1, 2, 1, 2, 1]
    assert room.state.swap2_stage == "first_choice"
    assert room.state.turn_seat == first.seat

    engine.act(room, first, "swap2_choose", {"choice": "black"})
    assert room.state.seat_stones == [1, 2]
    assert room.state.turn_seat == second.seat


def test_gomoku_rejects_swap2_with_renju() -> None:
    engine = GomokuEngine()

    assert engine.room_options(
        {"winRule": "renju", "openingRule": "standard"}
    ) == {"winRule": "renju", "openingRule": "standard"}
    with pytest.raises(GameRuleError, match="有禁手连珠不能使用 Swap2"):
        engine.room_options(
            {"winRule": "renju", "openingRule": "swap2"}
        )


def test_gomoku_two_consecutive_passes_draw_and_a_move_resets_passes() -> None:
    engine = GomokuEngine()
    room = make_room(engine, 2)
    black, white = room.players

    engine.act(room, black, "pass", {})
    assert room.state.consecutive_passes == 1
    engine.act(room, white, "place", {"row": 7, "column": 7})
    assert room.state.consecutive_passes == 0
    engine.act(room, black, "pass", {})
    engine.act(room, white, "pass", {})

    assert room.phase == "finished"
    assert room.winner == "draw"
    assert room.win_reason == "双方连续停一手，本局和棋"


def test_renju_cannot_pass_during_the_first_three_stones() -> None:
    engine = GomokuEngine()
    room = make_room(engine, 2, {"winRule": "renju"})

    with pytest.raises(GameRuleError, match="前三手"):
        engine.act(room, room.players[0], "pass", {})


def test_gomoku_rejects_unsupported_opening_options() -> None:
    with pytest.raises(GameRuleError):
        GomokuEngine().room_options({"openingRule": "unknown"})


def test_go_captures_stones_and_rejects_suicide() -> None:
    engine = GoEngine()
    room = make_room(engine, 2)
    state = room.state
    state.board[1][1] = 2
    state.board[0][1] = state.board[1][0] = state.board[2][1] = 1
    state.turn_seat = 0

    engine.act(room, room.players[0], "place", {"row": 1, "column": 2})

    assert state.board[1][1] == 0
    assert state.captures == [1, 0]

    state.board = [[0] * 19 for _ in range(19)]
    state.board[0][1] = state.board[1][0] = state.board[2][1] = state.board[1][2] = 1
    state.turn_seat = 1
    with pytest.raises(GameRuleError, match="无气"):
        engine.act(room, room.players[1], "place", {"row": 1, "column": 1})


def test_go_two_passes_enter_scoring_and_both_players_confirm_result() -> None:
    engine = GoEngine()
    room = make_room(engine, 2)
    engine.act(room, room.players[0], "pass", {})
    engine.act(room, room.players[1], "pass", {})

    assert room.phase == "scoring"
    preview = engine.view(room, room.players[0])["score"]
    assert preview["black"] == 0.0
    assert preview["white"] == 7.5
    assert preview["neutralPoints"] == 361

    engine.act(room, room.players[0], "confirm_score", {})
    assert room.phase == "scoring"
    engine.act(room, room.players[1], "confirm_score", {})

    assert room.phase == "finished"
    assert room.state.score["black"] == 0.0
    assert room.state.score["white"] == 7.5
    assert room.winner == "white"


def test_go_supports_small_boards_and_zero_komi_draws() -> None:
    engine = GoEngine()
    room = make_room(engine, 2, {"boardSize": 9, "komi": 0.0})

    assert len(room.state.board) == 9
    engine.act(room, room.players[0], "pass", {})
    engine.act(room, room.players[1], "pass", {})
    engine.act(room, room.players[0], "confirm_score", {})
    engine.act(room, room.players[1], "confirm_score", {})

    assert room.phase == "finished"
    assert room.winner == "draw"
    assert room.state.score["black"] == 0.0
    assert room.state.score["white"] == 0.0
    assert room.state.score["neutralPoints"] == 81


def test_go_dead_stone_changes_reset_confirmation_and_affect_score() -> None:
    engine = GoEngine()
    room = make_room(engine, 2, {"boardSize": 9, "komi": 0.0})
    state = room.state
    state.board[0][0] = 1
    state.board[0][1] = 2
    room.phase = "scoring"

    engine.act(
        room,
        room.players[0],
        "mark_dead",
        {"row": 0, "column": 1},
    )
    preview = engine.view(room, room.players[0])["score"]
    assert state.dead_stones == [(0, 1)]
    assert preview["deadWhite"] == 1
    assert preview["black"] == 81.0

    engine.act(room, room.players[0], "confirm_score", {})
    assert state.score_confirmed_player_ids == [room.players[0].id]
    engine.act(
        room,
        room.players[1],
        "mark_dead",
        {"row": 0, "column": 1},
    )
    assert state.dead_stones == []
    assert state.score_confirmed_player_ids == []

    engine.act(
        room,
        room.players[1],
        "mark_dead",
        {"row": 0, "column": 1},
    )
    engine.act(room, room.players[0], "confirm_score", {})
    engine.act(room, room.players[1], "confirm_score", {})

    assert room.phase == "finished"
    assert state.board[0][1] == 0
    assert state.captures == [1, 0]
    assert state.score["deadWhite"] == 1


def test_go_scoring_resume_requires_both_players_and_restores_turn() -> None:
    engine = GoEngine()
    room = make_room(engine, 2, {"boardSize": 9, "komi": 7.5})
    engine.act(room, room.players[0], "pass", {})
    engine.act(room, room.players[1], "pass", {})

    engine.act(room, room.players[0], "resume_play", {})
    assert room.phase == "scoring"
    assert room.state.resume_requested_by == room.players[0].id

    engine.act(room, room.players[0], "resume_play", {})
    assert room.state.resume_requested_by is None
    engine.act(room, room.players[0], "resume_play", {})
    engine.act(room, room.players[1], "resume_play", {})

    assert room.phase == "playing"
    assert room.state.turn_seat == 0
    assert room.state.consecutive_passes == 0


def test_go_rejects_any_previously_seen_board_position() -> None:
    engine = GoEngine()
    room = make_room(engine, 2, {"boardSize": 9, "komi": 7.5})
    repeated_board = [row[:] for row in room.state.board]
    repeated_board[0][0] = 1
    room.state.position_history.append(engine._board_key(repeated_board))

    with pytest.raises(GameRuleError, match="全局同形禁着"):
        engine.act(
            room,
            room.players[0],
            "place",
            {"row": 0, "column": 0},
        )

    assert room.state.board[0][0] == 0


def test_xiangqi_validates_piece_ownership_and_turns() -> None:
    engine = XiangqiEngine()
    room = make_room(engine, 2)

    engine.act(
        room,
        room.players[0],
        "move",
        {"fromRow": 6, "fromColumn": 0, "toRow": 5, "toColumn": 0},
    )
    assert room.state.board[5][0] == "rP"
    assert room.state.turn_color == "black"

    with pytest.raises(GameRuleError, match="自己的棋子"):
        engine.act(
            room,
            room.players[1],
            "move",
            {"fromRow": 5, "fromColumn": 0, "toRow": 4, "toColumn": 0},
        )

    engine.act(
        room,
        room.players[1],
        "move",
        {"fromRow": 3, "fromColumn": 0, "toRow": 4, "toColumn": 0},
    )
    assert room.state.turn_color == "red"


@pytest.mark.parametrize(
    ("piece", "source", "target", "blocker", "expected"),
    [
        ("rK", (9, 4), (8, 4), None, True),
        ("rK", (9, 4), (9, 6), None, False),
        ("rA", (9, 3), (8, 4), None, True),
        ("rA", (9, 3), (8, 3), None, False),
        ("rE", (9, 2), (7, 4), None, True),
        ("rE", (9, 2), (7, 4), (8, 3), False),
        ("rE", (5, 2), (3, 4), None, False),
        ("rH", (9, 1), (7, 2), None, True),
        ("rH", (9, 1), (7, 2), (8, 1), False),
        ("rR", (9, 0), (5, 0), None, True),
        ("rR", (9, 0), (5, 0), (7, 0), False),
        ("rC", (7, 1), (2, 1), (5, 1), False),
        ("rC", (7, 1), (2, 1), None, True),
        ("rP", (6, 0), (5, 0), None, True),
        ("rP", (6, 0), (6, 1), None, False),
        ("rP", (4, 0), (4, 1), None, True),
    ],
)
def test_xiangqi_piece_movement_rules(
    piece: str,
    source: tuple[int, int],
    target: tuple[int, int],
    blocker: tuple[int, int] | None,
    expected: bool,
) -> None:
    engine = XiangqiEngine()
    board = [[None] * 9 for _ in range(10)]
    board[source[0]][source[1]] = piece
    if blocker is not None:
        board[blocker[0]][blocker[1]] = "rP"

    assert engine._piece_can_move(board, piece, *source, *target) is expected


def test_xiangqi_cannon_captures_over_exactly_one_screen() -> None:
    engine = XiangqiEngine()
    board = [[None] * 9 for _ in range(10)]
    board[7][1] = "rC"
    board[5][1] = "rP"
    board[2][1] = "bP"

    assert engine._piece_can_move(board, "rC", 7, 1, 2, 1) is True


def test_xiangqi_rejects_exposing_the_flying_generals() -> None:
    engine = XiangqiEngine()
    board = [[None] * 9 for _ in range(10)]
    board[0][4] = "bK"
    board[9][4] = "rK"
    board[5][4] = "rR"

    assert engine._is_legal_move(board, "red", 5, 4, 5, 3) is False


def test_xiangqi_view_exposes_legal_moves_history_and_captures() -> None:
    engine = XiangqiEngine()
    room = make_room(engine, 2)
    view = engine.view(room, room.players[0])

    assert {
        "fromRow": 6,
        "fromColumn": 0,
        "toRow": 5,
        "toColumn": 0,
    } in view["legalMoves"]

    engine.act(
        room,
        room.players[0],
        "move",
        {"fromRow": 7, "fromColumn": 7, "toRow": 7, "toColumn": 4},
    )
    assert room.state.history[-1]["piece"] == "rC"

    room.state.turn_color = "red"
    room.state.board[6][0] = "rP"
    room.state.board[5][0] = "bP"
    engine.act(
        room,
        room.players[0],
        "move",
        {"fromRow": 6, "fromColumn": 0, "toRow": 5, "toColumn": 0},
    )
    assert room.state.captured_pieces[-1]["piece"] == "bP"


def test_xiangqi_identifies_checkmate_and_stalemate_positions() -> None:
    engine = XiangqiEngine()
    checkmate = [[None] * 9 for _ in range(10)]
    checkmate[0][4] = "bK"
    checkmate[9][4] = "rK"
    checkmate[2][3] = "rR"
    checkmate[2][4] = "rR"
    checkmate[2][5] = "rR"
    assert engine._in_check(checkmate, "black") is True
    assert engine._has_legal_move(checkmate, "black") is False

    stalemate = [[None] * 9 for _ in range(10)]
    stalemate[0][4] = "bK"
    stalemate[9][4] = "rK"
    stalemate[5][4] = "rP"
    stalemate[1][3] = "rR"
    stalemate[1][5] = "rR"
    stalemate[3][3] = "rH"
    assert engine._in_check(stalemate, "black") is False
    assert engine._has_legal_move(stalemate, "black") is False


def test_xiangqi_third_repeated_position_must_be_changed() -> None:
    engine = XiangqiEngine()
    repeat_room = make_room(engine, 2)
    next_board = [row[:] for row in repeat_room.state.board]
    next_board[5][0] = next_board[6][0]
    next_board[6][0] = None
    repeated_key = engine._position_key(next_board, "black")
    repeat_room.state.position_history.extend([repeated_key, repeated_key])
    with pytest.raises(GameRuleError, match="请更换走法"):
        engine.act(
            repeat_room,
            repeat_room.players[0],
            "move",
            {"fromRow": 6, "fromColumn": 0, "toRow": 5, "toColumn": 0},
        )

    assert repeat_room.phase == "playing"
    assert repeat_room.winner is None
    assert repeat_room.state.board[6][0] == "rP"
    assert repeat_room.state.board[5][0] is None
    assert repeat_room.state.move_count == 0
    assert repeat_room.state.history == []
    assert repeat_room.state.position_history.count(repeated_key) == 2


def cards(*ranks: int) -> list[Card]:
    return [Card(id=f"card-{index}-{rank}", rank=rank, suit="spade") for index, rank in enumerate(ranks)]


def test_doudizhu_classifies_and_compares_major_patterns() -> None:
    assert classify_cards(cards(16, 17)).kind == "rocket"
    assert classify_cards(cards(9, 9, 9, 9)).kind == "bomb"
    assert classify_cards(cards(3, 4, 5, 6, 7)).kind == "straight"
    assert classify_cards(cards(3, 3, 4, 4, 5, 5)).kind == "pair_straight"
    assert classify_cards(cards(3, 3, 3, 4, 4, 4)).kind == "airplane"
    assert classify_cards(cards(3, 3, 3, 4, 4, 4, 7, 8)).kind == "airplane_single"
    assert classify_cards(cards(3, 3, 3, 4, 4, 4, 7, 7)).kind == "airplane_single"
    assert (
        classify_cards(cards(4, 5, 5, 5, 6, 6, 6, 7, 7, 7, 9, 9)).kind
        == "airplane_single"
    )
    assert classify_cards(cards(3, 3, 3, 4, 4, 4, 7, 7, 8, 8)).kind == "airplane_pair"
    assert classify_cards(cards(6, 6, 6, 6, 8, 9)).kind == "four_two_single"
    assert classify_cards(cards(6, 6, 6, 6, 8, 8)).kind == "four_two_single"
    assert classify_cards(cards(6, 6, 6, 6, 8, 8, 9, 9)).kind == "four_two_pair"
    assert beats(classify_cards(cards(8, 8, 8, 8)), classify_cards(cards(14)))
    with pytest.raises(GameRuleError, match="有效牌型"):
        classify_cards(cards(3, 3, 4))
    with pytest.raises(GameRuleError, match="有效牌型"):
        classify_cards(cards(3, 3, 3, 3, 4, 4, 4, 4))
    with pytest.raises(GameRuleError, match="有效牌型"):
        classify_cards(cards(3, 3, 3, 4, 4, 4, 7, 7, 7, 7))
    with pytest.raises(GameRuleError, match="有效牌型"):
        classify_cards(cards(6, 6, 6, 6, 8, 8, 8, 8))


def test_doudizhu_laizi_supports_soft_hard_and_pure_wild_bombs() -> None:
    soft = classify_cards(cards(3, 3, 3, 4), wild_rank=3)
    hard = classify_cards(cards(4, 4, 4, 4), wild_rank=3)
    pure = classify_cards(cards(3, 3, 3, 3), wild_rank=3)

    assert (soft.kind, soft.bomb_level) == ("bomb", 1)
    assert (hard.kind, hard.bomb_level) == ("bomb", 2)
    assert (pure.kind, pure.bomb_level) == ("bomb", 3)
    assert beats(pure, hard)
    assert beats(PlayPattern("rocket", 17, 2, bomb_level=4), pure)


def test_doudizhu_call_rob_assigns_landlord_and_settles_spring() -> None:
    engine = DoudizhuEngine(random.Random(7))
    room = make_room(engine, 3)

    engine.act(room, room.players[0], "bid", {"decision": "call"})
    engine.act(room, room.players[1], "bid", {"decision": "rob"})
    engine.act(room, room.players[2], "bid", {"decision": "pass"})

    assert room.phase == "playing"
    assert room.state.landlord_seat == 1
    assert len(room.state.hands[1]) == 20
    assert room.state.multiplier == 2

    room.state.hands[1] = cards(3)
    engine.act(
        room,
        room.players[1],
        "play",
        {"cardIds": [room.state.hands[1][0].id]},
    )
    assert room.phase == "finished"
    assert room.winner == "landlord"
    assert room.winner_player_ids == [room.players[1].id]
    assert room.state.settlement["spring"] == "春天"
    assert room.state.multiplier == 4
    assert room.state.scores == {0: -4, 1: 8, 2: -4}


@pytest.mark.parametrize("landlord_seat", [0, 1, 2])
def test_doudizhu_turn_order_is_clockwise_for_every_landlord_seat(
    landlord_seat: int,
) -> None:
    engine = DoudizhuEngine(random.Random(7))
    room = make_room(engine, 3)
    engine._assign_landlord(room, landlord_seat)
    play_order = [(landlord_seat + offset) % 3 for offset in range(3)]

    for rank, seat in zip((3, 4, 5), play_order):
        room.state.hands[seat] = cards(rank, 15)
        card_id = room.state.hands[seat][0].id
        engine.act(room, room.players[seat], "play", {"cardIds": [card_id]})

    assert room.state.current_seat == landlord_seat


def test_doudizhu_late_caller_still_gives_both_opponents_a_rob_turn() -> None:
    engine = DoudizhuEngine(random.Random(13))
    room = make_room(engine, 3)

    engine.act(room, room.players[0], "bid", {"decision": "pass"})
    engine.act(room, room.players[1], "bid", {"decision": "call"})
    engine.act(room, room.players[2], "bid", {"decision": "pass"})
    assert room.phase == "bidding"
    assert room.state.current_bidder == 0
    engine.act(room, room.players[0], "bid", {"decision": "rob"})

    assert room.phase == "playing"
    assert room.state.landlord_seat == 0
    assert room.state.multiplier == 2


def test_doudizhu_bomb_and_anti_spring_double_the_score() -> None:
    engine = DoudizhuEngine(random.Random(3))
    room = make_room(engine, 3)
    engine.act(room, room.players[0], "bid", {"decision": "call"})
    engine.act(room, room.players[1], "bid", {"decision": "pass"})
    engine.act(room, room.players[2], "bid", {"decision": "pass"})
    state = room.state
    state.hands[0] = cards(6, 6, 6, 6, 9)
    state.hands[1] = cards(10)
    state.current_seat = 0

    engine.act(
        room,
        room.players[0],
        "play",
        {"cardIds": [card.id for card in state.hands[0] if card.rank == 6]},
    )
    assert state.multiplier == 2
    engine.act(room, room.players[1], "pass", {})
    engine.act(room, room.players[2], "pass", {})
    engine.act(
        room,
        room.players[0],
        "play",
        {"cardIds": [state.hands[0][0].id]},
    )
    assert room.phase == "finished"
    assert state.multiplier == 4
    assert state.settlement["spring"] == "春天"


def test_doudizhu_all_pass_redeals_and_bidding_exit_cancels() -> None:
    engine = DoudizhuEngine(random.Random(5))
    room = make_room(engine, 3)
    first_hand = [card.id for card in room.state.hands[0]]
    for player in room.players:
        engine.act(room, player, "bid", {"decision": "pass"})
    assert room.phase == "bidding"
    assert room.state.bids == []
    assert [card.id for card in room.state.hands[0]] != first_hand

    engine.act(room, room.players[0], "resign", {})
    assert room.phase == "finished"
    assert room.winner == "draw"
    assert "本局取消" in room.win_reason


def test_doudizhu_initial_no_shuffle_deck_simulates_collected_hands() -> None:
    engine = DoudizhuEngine(random.Random(19))

    deck = engine._initial_no_shuffle_deck()

    assert len(deck) == 54
    assert len({card.id for card in deck}) == 54
    for start, end in ((0, 17), (17, 34), (34, 51), (51, 54)):
        ranks = [card.rank for card in deck[start:end]]
        assert ranks == sorted(ranks)


def test_doudizhu_laizi_and_no_shuffle_variants_are_applied() -> None:
    laizi_engine = DoudizhuEngine(random.Random(2))
    laizi_room = make_room(laizi_engine, 3, {"variant": "laizi"})
    laizi_engine.act(
        laizi_room,
        laizi_room.players[0],
        "bid",
        {"decision": "call"},
    )
    laizi_engine.act(
        laizi_room,
        laizi_room.players[1],
        "bid",
        {"decision": "pass"},
    )
    laizi_engine.act(
        laizi_room,
        laizi_room.players[2],
        "bid",
        {"decision": "pass"},
    )
    assert 3 <= laizi_room.state.wild_rank <= 15

    class TrackingRandom(random.Random):
        def __init__(self, seed: int) -> None:
            super().__init__(seed)
            self.shuffle_calls = 0
            self.cut_calls = 0

        def shuffle(self, sequence) -> None:
            self.shuffle_calls += 1
            super().shuffle(sequence)

        def randrange(self, *args, **kwargs) -> int:
            self.cut_calls += 1
            return super().randrange(*args, **kwargs)

    no_shuffle_rng = TrackingRandom(0)
    no_shuffle_engine = DoudizhuEngine(no_shuffle_rng)
    no_shuffle_room = make_room(
        no_shuffle_engine,
        3,
        {"variant": "no_shuffle"},
    )
    assert no_shuffle_rng.shuffle_calls == 1
    assert no_shuffle_rng.cut_calls == 1

    no_shuffle_room.state.next_deck = create_deck()
    no_shuffle_engine.start(no_shuffle_room)
    assert no_shuffle_rng.shuffle_calls == 1
    assert no_shuffle_rng.cut_calls == 2
    dealt_ids = {
        card.id
        for hand in no_shuffle_room.state.hands.values()
        for card in hand
    } | {card.id for card in no_shuffle_room.state.bottom_cards}
    assert dealt_ids == {card.id for card in create_deck()}


def test_doudizhu_bidding_view_includes_the_viewers_hand() -> None:
    engine = DoudizhuEngine(random.Random(17))
    room = make_room(engine, 3)

    view = engine.view(room, room.players[0])

    assert room.phase == "bidding"
    assert len(view["hand"]) == 17
    assert {card["id"] for card in view["hand"]} == {
        card.id for card in room.state.hands[0]
    }
    assert "remainingRanks" not in view


def test_doudizhu_completes_a_full_deal_through_legal_play() -> None:
    engine = DoudizhuEngine(random.Random(11))
    room = make_room(engine, 3)
    engine.act(room, room.players[0], "bid", {"decision": "call"})
    engine.act(room, room.players[1], "bid", {"decision": "pass"})
    engine.act(room, room.players[2], "bid", {"decision": "pass"})

    for _ in range(500):
        if room.phase == "finished":
            break
        state = room.state
        player = room.players[state.current_seat]
        previous = engine._last_pattern(state)
        playable = next(
            (
                card
                for card in state.hands[player.seat]
                if previous is None
                or beats(classify_cards([card]), previous)
            ),
            None,
        )
        if playable is None:
            engine.act(room, player, "pass", {})
        else:
            engine.act(room, player, "play", {"cardIds": [playable.id]})

    assert room.phase == "finished"
    assert room.winner in {"landlord", "farmers"}
    assert room.state.history


def test_junqi_dark_setup_keeps_opponent_pieces_private() -> None:
    engine = JunqiEngine()
    room = make_room(engine, 2, {"mode": "dark"})

    assert room.phase == "setup"
    first_view = engine.view(room, room.players[0])
    own_pieces = []
    enemy_pieces = []
    for row in first_view["board"]:
        for piece in row:
            if piece is None:
                continue
            if piece["side"] == "red":
                own_pieces.append(piece)
            else:
                enemy_pieces.append(piece)
    assert len(own_pieces) == len(enemy_pieces) == 25
    assert all(piece["kind"] for piece in own_pieces)
    assert all(piece["kind"] is None for piece in enemy_pieces)

    engine.act(room, room.players[0], "ready", {})
    engine.act(room, room.players[1], "ready", {})
    assert room.phase == "playing"
    assert room.state.turn_seat == 0


def test_junqi_flip_first_piece_assigns_sides() -> None:
    engine = JunqiEngine()
    room = make_room(engine, 2, {"mode": "flip"})
    state: JunqiState = room.state
    position = next(
        (row, column)
        for row in range(12)
        for column in range(5)
        if state.board[row][column] is not None
    )
    piece = state.board[position[0]][position[1]]
    assert piece is not None

    engine.act(
        room,
        room.players[0],
        "flip",
        {"row": position[0], "column": position[1]},
    )

    assert state.seat_sides == [piece.side, 1 - piece.side]
    assert piece.revealed is True
    assert state.turn_seat == 1
    second_view = engine.view(room, room.players[1])
    assert second_view["board"][position[0]][position[1]]["kind"] == piece.kind


def test_junqi_engineer_turns_on_rail_and_captures_mine() -> None:
    engine = JunqiEngine()
    board = [[None] * 5 for _ in range(12)]
    engineer = JunqiPiece("engineer", 0, "engineer", True)
    mine = JunqiPiece("mine", 1, "mine", True)
    board[5][1] = engineer
    board[10][4] = mine

    assert engine._can_move(board, engineer, (5, 1), (10, 4)) is True
    assert engine._combat(engineer, mine) == "attacker"
    regular = JunqiPiece("company", 0, "company", True)
    board[5][1] = regular
    assert engine._can_move(board, regular, (5, 1), (10, 4)) is False


def test_junqi_capture_flag_finishes_match() -> None:
    engine = JunqiEngine()
    room = make_room(engine, 2, {"mode": "dark"})
    state = JunqiState(mode="dark")
    state.board[6][2] = JunqiPiece("red-company", 0, "company")
    state.board[5][2] = JunqiPiece("blue-flag", 1, "flag")
    room.state = state
    room.phase = "playing"

    engine.act(
        room,
        room.players[0],
        "move",
        {"fromRow": 6, "fromColumn": 2, "toRow": 5, "toColumn": 2},
    )

    assert room.phase == "finished"
    assert room.winner == "red"
    assert room.winner_player_ids == [room.players[0].id]


def test_generic_game_match_is_filterable_by_game(tmp_path) -> None:
    store = AccountStore(tmp_path / "game-hall.sqlite3")
    first, _ = store.register("board_one", "secret123", "棋手一")
    second, _ = store.register("board_two", "secret123", "棋手二")

    assert store.record_game_match(
        game_key="gomoku",
        match_id="gomoku-match",
        room_code="ABCD",
        winner="black",
        reason="黑方连成五子",
        started_at="2026-08-01T00:00:00+00:00",
        ended_at="2026-08-01T00:10:00+00:00",
        details={"players": [], "state": {}},
        players=[
            {
                "accountId": first.id,
                "playerName": first.player_name,
                "seat": 0,
                "role": "black",
                "alignment": "black",
                "won": True,
                "isHost": True,
            },
            {
                "accountId": second.id,
                "playerName": second.player_name,
                "seat": 1,
                "role": "white",
                "alignment": "white",
                "won": False,
                "isHost": False,
            },
        ],
    )
    assert store.summary_for_account(first.id, game_key="gomoku")["wins"] == 1
    history = store.history_for_account(first.id, game_key="gomoku")
    assert history[0]["gameKey"] == "gomoku"
    assert history[0]["gameName"] == "五子棋"
    assert store.match_for_account("gomoku-match", first.id)["winner"] == "black"


def test_finished_room_leave_does_not_offer_resume() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    _, guest, _ = manager.join_room(
        room.code, "gomoku", "乙", "account-2"
    )
    manager.start(room, host.id)
    manager.act(room, host.id, "resign", {})

    assert room.phase == "finished"
    manager.leave(room, host.id)
    assert all(player.id != host.id for player in room.players)
    assert room.player(guest.id).connected is True
    assert room.phase == "lobby"


def test_created_room_has_a_normalized_public_name() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room(
        "gomoku",
        "甲",
        "account-1",
        room_name="  周末   棋社  ",
    )

    assert room.name == "周末 棋社"
    lobby = build_arcade_lobby_view([room], manager.engines)
    view = build_arcade_room_view(room, host, manager.engines["gomoku"])
    assert lobby[0]["roomName"] == "周末 棋社"
    assert view["roomName"] == "周末 棋社"


def test_created_room_uses_host_name_when_custom_name_is_blank() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, _, _ = manager.create_room(
        "gomoku", "甲", "account-1", room_name="   "
    )

    assert room.name == "甲的房间"


def test_room_name_is_limited_to_twenty_characters() -> None:
    manager = ArcadeRoomManager(build_engine_registry())

    with pytest.raises(ArcadeRoomError, match="房间名称最多 20 个字符"):
        manager.create_room(
            "gomoku", "甲", "account-1", room_name="房" * 21
        )


def test_active_solo_abandon_removes_room_and_releases_account() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, player, _ = manager.create_room(
        "reaction", "反应玩家", "account-solo"
    )
    manager.start(room, player.id)

    assert manager.abandon(room, player.id) is False
    assert room.code not in manager.rooms
    assert manager.active_room_for_account("account-solo") is None

    next_room, _, _ = manager.create_room(
        "minesweeper", "反应玩家", "account-solo"
    )
    assert next_room.code in manager.rooms


def test_account_cannot_occupy_two_active_rooms() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    first, _, _ = manager.create_room(
        "reaction", "同账号玩家", "same-account"
    )

    with pytest.raises(ActiveRoomError) as error:
        manager.create_room(
            "minesweeper", "同账号玩家", "same-account"
        )

    assert error.value.room_code == first.code
    assert error.value.game_key == "reaction"


def test_active_multiplayer_abandon_forfeits_and_releases_account() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    _, guest, _ = manager.join_room(
        room.code, "gomoku", "乙", "account-2"
    )
    manager.start(room, host.id)

    assert manager.abandon(room, host.id) is True
    assert room.phase == "finished"
    assert room.winner_player_ids == [guest.id]
    assert host.left_room is True
    assert host.connected is False
    assert manager.active_room_for_account("account-1") is None
    assert manager.active_room_for_account("account-2") == (room, guest)


def test_arcade_lobby_host_can_kick_and_dissolve() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    _, guest, _ = manager.join_room(
        room.code, "gomoku", "乙", "account-2"
    )

    manager.kick(room, host.id, guest.id)
    assert [player.id for player in room.players] == [host.id]

    manager.dissolve(room, host.id)
    assert room.code not in manager.rooms


def test_arcade_room_requires_manual_cleanup_after_ten_offline_minutes() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = False
    manager.update_presence(room, now=disconnected_at)

    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=9, seconds=59)
    ) == []
    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=10)
    ) == [room]
    assert room.cleanup_ready is True
    assert room.code in manager.rooms
    cleanup_items = build_arcade_lobby_view(
        list(manager.rooms.values()), manager.engines
    )
    assert cleanup_items[0]["cleanupAvailable"] is True
    assert cleanup_items[0]["allHumansOffline"] is True

    assert manager.cleanup_room(
        room.code,
        now=disconnected_at + timedelta(minutes=10),
    ) is room
    assert room.code not in manager.rooms


@pytest.mark.parametrize(
    ("game_key", "options"),
    [
        ("gomoku", {}),
        ("xiangqi", {}),
        ("go", {}),
        ("junqi", {"mode": "dark"}),
    ],
)
def test_two_player_games_forfeit_after_ten_partially_offline_minutes(
    game_key: str,
    options: dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manager = ArcadeRoomManager(
        build_engine_registry(), rng=random.Random(7)
    )
    room, host, _ = manager.create_room(
        game_key, "甲", "account-1", options
    )
    _, guest, _ = manager.join_room(
        room.code, game_key, "乙", "account-2"
    )
    manager.start(room, host.id)
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    guest.connected = False
    manager.update_presence(room, now=disconnected_at)
    view = build_arcade_room_view(room, host, manager.engine(game_key))
    guest_view = next(
        player for player in view["players"] if player["id"] == guest.id
    )
    assert guest_view["disconnectForfeitAt"] == (
        disconnected_at + timedelta(minutes=10)
    ).isoformat()

    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=9, seconds=59)
    ) == []
    with caplog.at_level("INFO"):
        assert manager.maintain(
            now=disconnected_at + timedelta(minutes=10)
        ) == [room]

    assert room.phase == "finished"
    assert room.winner_player_ids == [host.id]
    assert "掉线超过 10 分钟" in (room.win_reason or "")
    assert guest.disconnect_forfeited is True
    assert any(
        getattr(record, "event", None) == "room.disconnect_forfeit"
        for record in caplog.records
    )


def test_all_offline_active_room_is_cleaned_without_a_match_result() -> None:
    manager = ArcadeRoomManager(
        build_engine_registry(), rng=random.Random(7)
    )
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    _, guest, _ = manager.join_room(
        room.code, "gomoku", "乙", "account-2"
    )
    manager.start(room, host.id)
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = guest.connected = False
    manager.update_presence(room, now=disconnected_at)

    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=10)
    ) == [room]
    assert room.phase == "playing"
    assert room.winner is None
    assert room.ended_at is None
    assert room.cleanup_ready is True


def test_return_to_all_offline_room_restarts_other_players_grace() -> None:
    manager = ArcadeRoomManager(
        build_engine_registry(), rng=random.Random(7)
    )
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    _, guest, _ = manager.join_room(
        room.code, "gomoku", "乙", "account-2"
    )
    manager.start(room, host.id)
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = guest.connected = False
    manager.update_presence(room, now=disconnected_at)

    returned_at = disconnected_at + timedelta(minutes=9)
    host.connected = True
    manager.update_presence(room, now=returned_at)

    assert guest.disconnected_at == returned_at
    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=10)
    ) == []
    assert room.phase == "playing"
    assert manager.maintain(
        now=returned_at + timedelta(minutes=10)
    ) == [room]
    assert room.winner_player_ids == [host.id]


def test_poker_disconnect_timeout_eliminates_the_player_from_the_table() -> None:
    manager = ArcadeRoomManager(
        build_engine_registry(), rng=random.Random(7)
    )
    room, host, _ = manager.create_room("poker", "甲", "account-1")
    _, guest, _ = manager.join_room(
        room.code, "poker", "乙", "account-2"
    )
    manager.start(room, host.id)
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    guest.connected = False
    manager.update_presence(room, now=disconnected_at)

    manager.maintain(now=disconnected_at + timedelta(minutes=10))

    assert guest.id in room.state.folded_ids
    assert guest.id in room.state.eliminated_ids
    assert room.phase == "finished"
    assert room.winner_player_ids == [host.id]


def test_doudizhu_disconnect_timeout_forfeits_the_players_team() -> None:
    manager = ArcadeRoomManager(
        build_engine_registry(), rng=random.Random(7)
    )
    room, host, _ = manager.create_room("doudizhu", "甲", "account-1")
    _, first_guest, _ = manager.join_room(
        room.code, "doudizhu", "乙", "account-2"
    )
    manager.join_room(room.code, "doudizhu", "丙", "account-3")
    manager.start(room, host.id)
    room.state.landlord_seat = host.seat
    room.state.current_seat = host.seat
    room.phase = "playing"
    assert first_guest.seat != room.state.landlord_seat
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    first_guest.connected = False
    manager.update_presence(room, now=disconnected_at)

    manager.maintain(now=disconnected_at + timedelta(minutes=10))

    assert room.phase == "finished"
    assert room.winner == "landlord"
    assert room.winner_player_ids == [host.id]
    assert "掉线超过 10 分钟" in (room.win_reason or "")


def test_arcade_room_cleanup_rechecks_presence_and_offline_lobby_joining():
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = False
    manager.update_presence(room, now=disconnected_at)

    with pytest.raises(ArcadeRoomError, match="原成员恢复"):
        manager.join_room(room.code, "gomoku", "乙", "account-2")
    with pytest.raises(ArcadeRoomError, match="10 分钟"):
        manager.cleanup_room(
            room.code,
            now=disconnected_at + timedelta(minutes=9),
        )

    host.connected = True
    with pytest.raises(ArcadeRoomError, match="重新连接"):
        manager.cleanup_room(
            room.code,
            now=disconnected_at + timedelta(minutes=11),
        )


def test_arcade_lobby_host_transfers_to_first_online_player_after_twenty_seconds():
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("doudizhu", "甲", "account-1")
    _, first_guest, _ = manager.join_room(
        room.code, "doudizhu", "乙", "account-2"
    )
    _, second_guest, _ = manager.join_room(
        room.code, "doudizhu", "丙", "account-3"
    )
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    host.connected = False
    manager.update_presence(room, now=disconnected_at)

    assert manager.maintain(
        now=disconnected_at + timedelta(seconds=19)
    ) == []
    assert manager.maintain(
        now=disconnected_at + timedelta(seconds=20)
    ) == [room]
    assert room.host_id == first_guest.id
    assert room.host_id != second_guest.id


def test_arcade_host_does_not_transfer_while_playing_or_all_offline():
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    _, guest, _ = manager.join_room(
        room.code, "gomoku", "乙", "account-2"
    )
    disconnected_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    room.phase = "playing"
    host.connected = False
    manager.update_presence(room, now=disconnected_at)

    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=1)
    ) == []
    assert room.host_id == host.id

    room.phase = "lobby"
    guest.connected = False
    manager.update_presence(room, now=disconnected_at)
    assert manager.maintain(
        now=disconnected_at + timedelta(minutes=1)
    ) == []
    assert room.host_id == host.id


def test_arcade_room_rules_are_validated_locked_and_applied_next_game() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room(
        "gomoku",
        "甲",
        "account-1",
        {
            "firstPlayer": "host",
            "allowUndo": False,
            "allowDraw": False,
            "winRule": "exact_five",
        },
    )
    _, guest, _ = manager.join_room(
        room.code, "gomoku", "乙", "account-2"
    )
    assert "boardSize" not in room.options

    with pytest.raises(ArcadeRoomError, match="只有房主"):
        manager.update_options(room, guest.id, room.options)

    manager.start(room, host.id)
    assert room.players[0].id == host.id
    assert len(room.state.board) == 15
    with pytest.raises(ArcadeRoomError, match="没有开启悔棋"):
        manager.request_game_action(room, host.id, "undo")
    with pytest.raises(ArcadeRoomError, match="没有开启和棋"):
        manager.request_game_action(room, host.id, "draw")
    with pytest.raises(ArcadeRoomError, match="进行中"):
        manager.update_options(room, host.id, room.options)

    manager.act(room, host.id, "resign", {})
    manager.update_options(
        room,
        host.id,
        {
            **room.options,
            "winRule": "freestyle",
        },
    )
    assert room.phase == "lobby"
    assert "boardSize" not in room.options
    assert room.options["winRule"] == "freestyle"


def test_swap2_opening_choices_are_not_treated_as_undoable_moves() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room(
        "gomoku",
        "甲",
        "account-1",
        {
            "firstPlayer": "host",
            "openingRule": "swap2",
            "winRule": "freestyle",
        },
    )
    manager.join_room(room.code, "gomoku", "乙", "account-2")
    manager.start(room, host.id)

    for row, column in [(7, 7), (7, 8), (8, 8)]:
        manager.act(
            room,
            host.id,
            "place",
            {"row": row, "column": column},
        )

    assert room.undo_history == []
    with pytest.raises(ArcadeRoomError, match="没有可以撤回"):
        manager.request_game_action(room, host.id, "undo")


def test_arcade_chat_is_shared_and_bounded() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room(
        "gomoku",
        "甲",
        "account-1",
        avatar_url="/avatars/jade-owl.webp",
    )
    message = manager.send_chat(room, host.id, "  准备好了吗  ")

    assert message.content == "准备好了吗"
    assert room.chat_messages[-1].sender_id == host.id
    lobby = build_arcade_lobby_view([room], manager.engines)
    view = build_arcade_room_view(room, host, manager.engines["gomoku"])
    assert lobby[0]["hostAvatarUrl"] == "/avatars/jade-owl.webp"
    assert view["self"]["accountId"] == "account-1"
    assert view["self"]["avatarUrl"] == "/avatars/jade-owl.webp"
    assert view["players"][0]["avatarUrl"] == "/avatars/jade-owl.webp"
    assert (
        view["chat"]["messages"][-1]["senderAvatarUrl"]
        == "/avatars/jade-owl.webp"
    )

    for index in range(101):
        manager.send_chat(room, host.id, f"消息 {index}")
    assert len(room.chat_messages) == 100
    assert room.chat_messages[0].content == "消息 1"


def test_rematch_waits_for_every_player_and_rotates_sides() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    manager.join_room(room.code, "gomoku", "乙", "account-2")
    manager.start(room, host.id)
    first_black = room.players[0]
    second_player = room.players[1]
    manager.act(room, first_black.id, "resign", {})

    manager.restart(room, first_black.id)
    assert room.phase == "finished"
    assert room.rematch_ready_ids == {first_black.id}

    manager.restart(room, second_player.id)
    assert room.phase == "playing"
    assert room.round_number == 2
    assert room.players[1].id == first_black.id
    assert room.rematch_ready_ids == set()


def test_gomoku_players_can_accept_undo_and_draw_requests() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    manager.join_room(room.code, "gomoku", "乙", "account-2")
    manager.start(room, host.id)
    black, white = room.players

    manager.act(room, black.id, "place", {"row": 7, "column": 7})
    manager.request_game_action(room, white.id, "undo")
    manager.resolve_game_request(room, white.id, False)
    assert room.pending_request is None

    manager.request_game_action(room, white.id, "undo")
    manager.resolve_game_request(room, black.id, True)

    assert room.state.board[7][7] == 0
    assert room.state.turn_seat == 0
    assert room.pending_request is None

    manager.request_game_action(room, black.id, "draw")
    with pytest.raises(ArcadeRoomError, match="先处理当前申请"):
        manager.act(room, black.id, "place", {"row": 8, "column": 8})
    manager.resolve_game_request(room, white.id, True)
    assert room.phase == "finished"
    assert room.winner == "draw"
    assert room.winner_player_ids == []


def test_end_table_request_requires_every_human_and_returns_to_lobby() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("doudizhu", "甲", "account-1")
    _, second, _ = manager.join_room(
        room.code, "doudizhu", "乙", "account-2"
    )
    _, third, _ = manager.join_room(
        room.code, "doudizhu", "丙", "account-3"
    )
    manager.start(room, host.id)

    assert manager.request_game_action(room, host.id, "end_table") is False
    assert room.pending_request is not None
    assert room.pending_request.approved_player_ids == {host.id}

    assert manager.resolve_game_request(room, second.id, True) is False
    assert room.phase == "bidding"
    second_view = build_arcade_room_view(
        room, second, manager.engines["doudizhu"]
    )
    assert second_view["request"]["hasApproved"] is True
    assert second_view["request"]["approvalCount"] == 2
    assert second_view["request"]["requiredApprovalCount"] == 3

    assert manager.resolve_game_request(room, third.id, True) is True
    assert room.phase == "lobby"
    assert room.game_id is None
    assert room.round_number == 0
    assert room.pending_request is None
    assert room.recorded is False


def test_rejecting_end_table_request_keeps_the_current_game() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("gomoku", "甲", "account-1")
    _, opponent, _ = manager.join_room(
        room.code, "gomoku", "乙", "account-2"
    )
    manager.start(room, host.id)

    manager.request_game_action(room, host.id, "end_table")
    assert manager.resolve_game_request(room, opponent.id, False) is False

    assert room.phase == "playing"
    assert room.game_id is not None
    assert room.pending_request is None


def test_solo_game_cannot_request_end_table() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, player, _ = manager.create_room(
        "reaction", "单人玩家", "account-solo"
    )
    manager.start(room, player.id)

    with pytest.raises(ArcadeRoomError, match="单人挑战"):
        manager.request_game_action(room, player.id, "end_table")


@pytest.mark.parametrize(
    "game_key",
    ["avalon", "gomoku", "xiangqi", "go", "poker", "doudizhu", "junqi", "monopoly"],
)
def test_every_multiplayer_game_can_end_the_table_by_unanimous_request(
    game_key: str,
) -> None:
    manager = ArcadeRoomManager(
        build_engine_registry(), rng=random.Random(7)
    )
    engine = manager.engine(game_key)
    room, host, _ = manager.create_room(game_key, "玩家1", "account-1")
    players = [host]
    for index in range(2, engine.min_players + 1):
        _, player, _ = manager.join_room(
            room.code,
            game_key,
            f"玩家{index}",
            f"account-{index}",
        )
        players.append(player)
    manager.start(room, host.id)

    view = build_arcade_room_view(room, host, engine)
    assert view["actions"]["canRequestEndTable"] is True
    assert manager.request_game_action(room, host.id, "end_table") is False
    for player in players[1:-1]:
        assert manager.resolve_game_request(room, player.id, True) is False
    assert manager.resolve_game_request(room, players[-1].id, True) is True

    assert room.phase == "lobby"
    assert room.game_id is None
    assert room.winner is None


def test_end_table_request_ignores_ai_players() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("avalon", "甲", "account-1")
    for _ in range(4):
        manager.act(room, host.id, "add_ai", {})
    manager.start(room, host.id)

    assert manager.request_game_action(room, host.id, "end_table") is True
    assert room.phase == "lobby"
    assert room.pending_request is None


def test_poker_end_table_request_only_needs_surviving_players() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("poker", "甲", "account-1")
    _, second, _ = manager.join_room(
        room.code, "poker", "乙", "account-2"
    )
    _, third, _ = manager.join_room(
        room.code, "poker", "丙", "account-3"
    )
    manager.start(room, host.id)
    manager.act(room, room.state.action_player_id, "fold", {})
    manager.act(room, room.state.action_player_id, "fold", {})
    assert room.phase == "between_hands"

    manager.engine("poker").manual_forfeit(room, host)
    survivors = [
        player for player in (host, second, third)
        if player.id not in room.state.eliminated_ids
    ]
    eliminated_view = build_arcade_room_view(
        room, host, manager.engine("poker")
    )
    assert eliminated_view["actions"]["canRequestEndTable"] is False
    manager.request_game_action(room, survivors[0].id, "end_table")
    view = build_arcade_room_view(room, survivors[0], manager.engine("poker"))

    eliminated_view = build_arcade_room_view(
        room, host, manager.engine("poker")
    )
    assert eliminated_view["request"]["canRespond"] is False
    with pytest.raises(ArcadeRoomError, match="不需要参与"):
        manager.resolve_game_request(room, host.id, False)

    assert view["request"]["requiredApprovalCount"] == 2
    assert manager.resolve_game_request(room, survivors[1].id, True) is True
    assert room.phase == "lobby"


def test_reaction_records_exactly_three_rounds_and_average() -> None:
    engine = ReactionEngine()
    room = make_room(engine, 1)

    engine.act(room, room.players[0], "record", {"elapsedMs": 180})
    with pytest.raises(GameRuleError, match="数据不正确"):
        engine.act(room, room.players[0], "record", {"elapsedMs": 0})
    engine.act(room, room.players[0], "record", {"elapsedMs": 240})
    engine.act(room, room.players[0], "record", {"elapsedMs": 210})

    assert room.phase == "finished"
    assert room.winner == "completed"
    assert room.state.results_ms == [180, 240, 210]
    assert engine.player_score(room, room.players[0]) == 210
    assert engine.view(room, room.players[0]) == {
        "roundsRequired": 3,
        "resultsMs": [180, 240, 210],
        "roundNumber": 3,
        "bestMs": 180,
        "averageMs": 210,
    }


def test_reaction_room_is_private_single_player_room() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room("reaction", "测试者", "account-1")

    assert room.listed is False
    manager.start(room, host.id)
    assert room.phase == "playing"


def test_reaction_false_start_resets_all_completed_rounds() -> None:
    engine = ReactionEngine()
    room = make_room(engine, 1)

    engine.act(room, room.players[0], "record", {"elapsedMs": 180})
    engine.act(room, room.players[0], "record", {"elapsedMs": 220})
    engine.act(room, room.players[0], "false_start", {})

    assert room.phase == "playing"
    assert room.state.results_ms == []
    assert engine.view(room, room.players[0]) == {
        "roundsRequired": 3,
        "resultsMs": [],
        "roundNumber": 1,
        "bestMs": None,
        "averageMs": None,
    }


def test_hanoi_solves_three_discs_in_the_optimal_number_of_moves() -> None:
    now = [100.0]
    engine = HanoiEngine(clock=lambda: now[0])
    room = make_room(engine, 1, {"discCount": 3})

    for source, target in [
        (0, 2),
        (0, 1),
        (2, 1),
        (0, 2),
        (1, 0),
        (1, 2),
        (0, 2),
    ]:
        now[0] += 0.1
        engine.act(
            room,
            room.players[0],
            "move",
            {"fromTower": source, "toTower": target},
        )

    assert room.phase == "finished"
    assert room.winner == "completed"
    assert room.state.towers == [[], [], [3, 2, 1]]
    assert room.state.moves == 7
    assert room.state.elapsed_ms == 700
    assert engine.player_score(room, room.players[0]) == 700
    view = engine.view(room, room.players[0])
    assert view["optimalMoves"] == 7
    assert view["isOptimal"] is True
    assert view["lastMove"] == {"fromTower": 0, "toTower": 2, "disc": 1}


def test_hanoi_rejects_illegal_moves_without_changing_the_towers() -> None:
    engine = HanoiEngine()
    room = make_room(engine, 1, {"discCount": 3})
    player = room.players[0]

    engine.act(room, player, "move", {"fromTower": 0, "toTower": 1})
    before = [list(tower) for tower in room.state.towers]
    with pytest.raises(GameRuleError, match="大圆盘"):
        engine.act(room, player, "move", {"fromTower": 0, "toTower": 1})
    with pytest.raises(GameRuleError, match="没有可以移动"):
        engine.act(room, player, "move", {"fromTower": 2, "toTower": 0})

    assert room.state.towers == before
    assert room.state.moves == 1


def test_hanoi_validates_difficulty_and_resets_the_active_challenge() -> None:
    now = [10.0]
    engine = HanoiEngine(clock=lambda: now[0])
    assert engine.room_options({}) == {"discCount": 5}
    assert engine.room_options({"discCount": 8}) == {"discCount": 8}
    with pytest.raises(GameRuleError, match="3 到 8"):
        engine.room_options({"discCount": 2})
    with pytest.raises(GameRuleError, match="3 到 8"):
        engine.room_options({"discCount": True})

    room = make_room(engine, 1, {"discCount": 4})
    engine.act(
        room,
        room.players[0],
        "move",
        {"fromTower": 0, "toTower": 1},
    )
    now[0] += 1
    engine.act(room, room.players[0], "reset", {})

    assert room.phase == "playing"
    assert room.state.disc_count == 4
    assert room.state.towers == [[4, 3, 2, 1], [], []]
    assert room.state.moves == 0
    assert room.state.elapsed_ms == 0


def test_hanoi_room_is_private_single_player_room() -> None:
    manager = ArcadeRoomManager(build_engine_registry())
    room, host, _ = manager.create_room(
        "hanoi", "解谜者", "account-1", {"discCount": 6}
    )

    assert room.listed is False
    assert room.options == {"discCount": 6, "allowSpectators": True}
    manager.start(room, host.id)
    assert room.phase == "playing"
    assert room.state.disc_count == 6
