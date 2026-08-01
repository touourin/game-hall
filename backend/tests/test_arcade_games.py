from __future__ import annotations

import pytest

from backend.app.accounts import AccountStore
from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.arcade.rooms import ArcadeRoomManager
from backend.app.games.base import GameRuleError
from backend.app.games.doudizhu.engine import (
    Card,
    DoudizhuEngine,
    beats,
    classify_cards,
)
from backend.app.games.go import GoEngine
from backend.app.games.gomoku import GomokuEngine
from backend.app.games.junqi.engine import JunqiEngine, JunqiPiece, JunqiState
from backend.app.games.reaction import ReactionEngine
from backend.app.games.registry import build_engine_registry
from backend.app.games.xiangqi import XiangqiEngine


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


def test_go_two_passes_finish_with_chinese_area_score() -> None:
    engine = GoEngine()
    room = make_room(engine, 2)
    engine.act(room, room.players[0], "pass", {})
    engine.act(room, room.players[1], "pass", {})

    assert room.phase == "finished"
    assert room.state.score == {"black": 0.0, "white": 7.5}
    assert room.winner == "white"


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


def cards(*ranks: int) -> list[Card]:
    return [Card(id=f"card-{index}-{rank}", rank=rank, suit="spade") for index, rank in enumerate(ranks)]


def test_doudizhu_classifies_and_compares_major_patterns() -> None:
    assert classify_cards(cards(16, 17)).kind == "rocket"
    assert classify_cards(cards(9, 9, 9, 9)).kind == "bomb"
    assert classify_cards(cards(3, 4, 5, 6, 7)).kind == "straight"
    assert classify_cards(cards(3, 3, 4, 4, 5, 5)).kind == "pair_straight"
    assert classify_cards(cards(3, 3, 3, 4, 4, 4)).kind == "airplane"
    assert classify_cards(cards(6, 6, 6, 6, 8, 9)).kind == "four_two_single"
    assert beats(classify_cards(cards(8, 8, 8, 8)), classify_cards(cards(14)))
    with pytest.raises(GameRuleError, match="有效牌型"):
        classify_cards(cards(3, 3, 4))


def test_doudizhu_bidding_assigns_landlord_and_records_winner() -> None:
    engine = DoudizhuEngine()
    room = make_room(engine, 3)

    engine.act(room, room.players[0], "bid", {"score": 1})
    engine.act(room, room.players[1], "bid", {"score": 0})
    engine.act(room, room.players[2], "bid", {"score": 2})

    assert room.phase == "playing"
    assert room.state.landlord_seat == 2
    assert len(room.state.hands[2]) == 20

    room.state.hands[2] = cards(3)
    engine.act(
        room,
        room.players[2],
        "play",
        {"cardIds": [room.state.hands[2][0].id]},
    )
    assert room.phase == "finished"
    assert room.winner == "landlord"
    assert room.winner_player_ids == [room.players[2].id]


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
                "displayName": first.display_name,
                "seat": 0,
                "role": "black",
                "alignment": "black",
                "won": True,
                "isHost": True,
            },
            {
                "accountId": second.id,
                "displayName": second.display_name,
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
    assert manager.leave(room, host.id) is False
    assert room.player(host.id).connected is False
    assert room.player(guest.id).connected is True


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
