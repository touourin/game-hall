from __future__ import annotations

import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.minesweeper.engine import DIFFICULTIES, MinesweeperEngine


class FakeClock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        return self.value


def make_room(
    engine: MinesweeperEngine,
    difficulty: str = "beginner",
) -> ArcadeRoom:
    player = ArcadePlayer(
        id="p1",
        account_id="a1",
        name="排雷员",
        token_hash="token",
        seat=0,
    )
    room = ArcadeRoom(
        code="MINE",
        game_key=engine.key,
        host_id=player.id,
        players=[player],
        state=engine.initial_state(),
        options={"difficulty": difficulty},
        game_id="game-minesweeper",
        started_at="2026-08-01T00:00:00+00:00",
    )
    engine.start(room)
    return room


@pytest.mark.parametrize(
    ("difficulty", "rows", "columns", "mines"),
    [
        ("beginner", 9, 9, 10),
        ("intermediate", 16, 16, 40),
        ("expert", 16, 30, 99),
    ],
)
def test_minesweeper_supports_all_classic_difficulties(
    difficulty: str,
    rows: int,
    columns: int,
    mines: int,
) -> None:
    engine = MinesweeperEngine(rng=random.Random(3))
    assert engine.room_options({"difficulty": difficulty}) == {
        "difficulty": difficulty
    }
    room = make_room(engine, difficulty)
    view = engine.view(room, room.players[0])
    assert (view["rows"], view["columns"], view["mineCount"]) == (
        rows,
        columns,
        mines,
    )
    assert len(view["cells"]) == rows * columns


def test_first_open_is_safe_and_mines_stay_hidden() -> None:
    clock = FakeClock()
    engine = MinesweeperEngine(clock=clock, rng=random.Random(7))
    room = make_room(engine)
    player = room.players[0]

    engine.act(room, player, "open", {"index": 40})
    state = room.state
    protected = {40, *engine._neighbors(state, 40)}

    assert not any(state.mines[index] for index in protected)
    assert sum(state.mines) == 10
    view = engine.view(room, player)
    assert view["started"] is True
    assert all(
        cell["state"] != "mine"
        for cell in view["cells"]
    )
    assert all(
        cell["adjacent"] is None
        for cell in view["cells"]
        if cell["state"] == "hidden"
    )


def test_flags_and_number_chording_are_validated_by_server() -> None:
    engine = MinesweeperEngine(rng=random.Random(2))
    room = make_room(engine)
    player = room.players[0]
    engine.act(room, player, "open", {"index": 0})

    hidden = next(
        index for index, revealed in enumerate(room.state.revealed) if not revealed
    )
    engine.act(room, player, "toggle_flag", {"index": hidden})
    assert room.state.flagged[hidden] is True
    engine.act(room, player, "open", {"index": hidden})
    assert room.state.revealed[hidden] is False
    engine.act(room, player, "toggle_flag", {"index": hidden})
    assert room.state.flagged[hidden] is False


def test_opening_a_mine_finishes_as_a_loss_without_score() -> None:
    clock = FakeClock()
    engine = MinesweeperEngine(clock=clock, rng=random.Random(9))
    room = make_room(engine)
    player = room.players[0]
    engine.act(room, player, "open", {"index": 0})
    mine = room.state.mines.index(True)
    clock.value += 4

    engine.act(room, player, "open", {"index": mine})

    assert room.phase == "finished"
    assert room.winner == "mine"
    assert room.state.exploded_index == mine
    assert engine.player_score(room, player) is None
    assert engine.view(room, player)["cells"][mine]["state"] == "exploded"


def test_clearing_safe_cells_records_server_time() -> None:
    clock = FakeClock()
    engine = MinesweeperEngine(clock=clock, rng=random.Random(4))
    room = make_room(engine)
    player = room.players[0]
    engine.act(room, player, "open", {"index": 0})

    clock.value += 12.4
    for index, mine in enumerate(room.state.mines):
        if not mine and not room.state.revealed[index]:
            engine.act(room, player, "open", {"index": index})

    assert room.phase == "finished"
    assert room.winner == "completed"
    assert room.state.elapsed_ms == 12_400
    assert engine.player_score(room, player) == 12_400
    record = engine.record_state(room)
    assert record["difficulty"] == "beginner"
    assert record["mine_count"] == DIFFICULTIES["beginner"]["mines"]


def test_invalid_difficulty_and_cell_are_rejected() -> None:
    engine = MinesweeperEngine()
    with pytest.raises(GameRuleError, match="难度"):
        engine.room_options({"difficulty": "impossible"})
    room = make_room(engine)
    with pytest.raises(GameRuleError, match="方格"):
        engine.act(room, room.players[0], "open", {"index": 999})
