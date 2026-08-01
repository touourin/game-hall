from __future__ import annotations

import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.schulte.engine import CELL_COUNT, SchulteEngine


class FakeClock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        return self.value


def make_room(engine: SchulteEngine) -> ArcadeRoom:
    player = ArcadePlayer(
        id="p1",
        account_id="a1",
        name="挑战者",
        token_hash="token",
        seat=0,
    )
    room = ArcadeRoom(
        code="GRID",
        game_key=engine.key,
        host_id=player.id,
        players=[player],
        state=engine.initial_state(),
        game_id="game-schulte",
        started_at="2026-08-01T00:00:00+00:00",
    )
    engine.start(room)
    return room


def test_schulte_hides_grid_until_begin_and_validates_sequence() -> None:
    clock = FakeClock()
    engine = SchulteEngine(clock=clock, rng=random.Random(7))
    room = make_room(engine)
    player = room.players[0]

    assert engine.view(room, player)["grid"] == []
    engine.act(room, player, "begin", {})
    view = engine.view(room, player)
    assert sorted(view["grid"]) == list(range(1, CELL_COUNT + 1))
    assert view["nextNumber"] == 1

    engine.act(room, player, "tap", {"value": 9})
    assert room.state.mistakes == 1
    assert room.state.next_number == 1

    engine.act(room, player, "tap", {"value": 1})
    assert room.state.next_number == 2
    assert engine.view(room, player)["completedCount"] == 1


def test_schulte_finishes_with_server_measured_score() -> None:
    clock = FakeClock()
    engine = SchulteEngine(clock=clock, rng=random.Random(3))
    room = make_room(engine)
    player = room.players[0]
    engine.act(room, player, "begin", {})

    for value in range(1, CELL_COUNT):
        clock.value += 0.2
        engine.act(room, player, "tap", {"value": value})
    clock.value += 0.2
    engine.act(room, player, "tap", {"value": CELL_COUNT})

    assert room.phase == "finished"
    assert room.state.elapsed_ms == 5_000
    assert engine.player_score(room, player) == 5_000
    view = engine.view(room, player)
    assert view["averageCellMs"] == 200
    assert view["accuracy"] == 100


def test_schulte_rejects_impossible_completion_and_can_reset() -> None:
    clock = FakeClock()
    engine = SchulteEngine(clock=clock, rng=random.Random(1))
    room = make_room(engine)
    player = room.players[0]
    engine.act(room, player, "begin", {})
    for value in range(1, CELL_COUNT):
        engine.act(room, player, "tap", {"value": value})

    clock.value += 0.5
    with pytest.raises(GameRuleError, match="速度异常"):
        engine.act(room, player, "tap", {"value": CELL_COUNT})
    assert room.phase == "playing"
    assert room.state.next_number == CELL_COUNT
    assert room.state.mistakes == 0

    engine.act(room, player, "reset", {})
    assert engine.view(room, player)["grid"] == []
    assert room.state.mistakes == 0
