from __future__ import annotations

import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.critical_crossing.engine import (
    BOUNDARY_PRESSURE_LIMIT,
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    DOWN,
    LEFT,
    PULSE_FRONT_SPEED,
    PULSE_WARNING_TICKS,
    RIGHT,
    SOLVABLE_SEEDS,
    UP,
    CriticalCrossingEngine,
    build_safe_route,
    duration_ticks,
    pulse_fronts,
    pulse_safe_gate,
    simulate_run,
)


def make_room(difficulty: str = DEFAULT_DIFFICULTY):
    current = [10.0]
    engine = CriticalCrossingEngine(
        clock=lambda: current[0],
        rng=random.Random(42),
    )
    player = ArcadePlayer(
        id="player-1",
        account_id="account-1",
        name="挑战者",
        token_hash="token",
        seat=0,
    )
    room = ArcadeRoom(
        code="CROS",
        game_key=engine.key,
        host_id=player.id,
        players=[player],
        state=engine.initial_state(),
        options={"difficulty": difficulty},
    )
    engine.start(room)
    return engine, room, player, current


@pytest.mark.parametrize(
    ("difficulty", "duration_seconds"),
    (("5s", 5), ("8s", 8), ("10s", 10)),
)
def test_each_difficulty_accepts_a_server_verified_crossing(
    difficulty: str,
    duration_seconds: int,
) -> None:
    engine, room, player, clock = make_room(difficulty)
    inputs = build_safe_route(room.state.seed, duration_seconds)
    clock[0] += duration_seconds + 0.1

    engine.act(room, player, "finish", {"inputs": inputs})

    assert room.phase == "finished"
    assert room.winner == "crossed"
    assert room.winner_player_ids == [player.id]
    assert room.state.difficulty == difficulty
    assert room.state.elapsed_ms == duration_seconds * 1_000
    assert engine.view(room, player)["crossed"] is True


def test_engine_replays_a_collision_and_records_an_interruption() -> None:
    engine, room, player, _ = make_room("5s")
    inputs = [UP | LEFT] * duration_ticks(5)
    result = simulate_run(room.state.seed, inputs, 5)
    assert result.collision_tick is not None

    engine.act(room, player, "finish", {"inputs": inputs[: result.ticks]})

    assert room.phase == "finished"
    assert room.winner == "interrupted"
    assert room.winner_player_ids == []
    assert room.state.collision_tick == result.collision_tick


@pytest.mark.parametrize(
    "inputs",
    ([], [16], [True], [0] * (duration_ticks(5) + 1)),
)
def test_engine_rejects_invalid_trajectories(inputs: list[int]) -> None:
    engine, room, player, _ = make_room()

    with pytest.raises(GameRuleError):
        engine.act(room, player, "finish", {"inputs": inputs})


def test_engine_validates_the_room_difficulty() -> None:
    engine = CriticalCrossingEngine()

    assert engine.room_options({}) == {"difficulty": "5s"}
    assert engine.room_options({"difficulty": "10s"}) == {
        "difficulty": "10s"
    }
    with pytest.raises(GameRuleError, match="难度不正确"):
        engine.room_options({"difficulty": "3s"})


def test_engine_does_not_accept_an_instant_success() -> None:
    engine, room, player, _ = make_room("5s")
    inputs = build_safe_route(room.state.seed, 5)

    with pytest.raises(GameRuleError, match="完成得太快"):
        engine.act(room, player, "finish", {"inputs": inputs})


def test_every_seed_and_difficulty_has_a_verified_route() -> None:
    for seed in SOLVABLE_SEEDS:
        for config in DIFFICULTIES.values():
            duration_seconds = int(config["duration_seconds"])
            result = simulate_run(
                seed,
                build_safe_route(seed, duration_seconds),
                duration_seconds,
            )
            assert result.crossed
            assert result.collision_kind is None


def test_first_pulse_waits_for_warning_and_exposes_a_safe_gate() -> None:
    seed = SOLVABLE_SEEDS[0]
    assert pulse_fronts(seed, PULSE_WARNING_TICKS - 1, 5) == []

    fronts = pulse_fronts(seed, PULSE_WARNING_TICKS, 5)
    gate = pulse_safe_gate(seed, 0, "y")
    assert {front.side for front in fronts} == {"left", "right"}
    assert all(front.gate == gate for front in fronts)
    assert all(
        abs(front.position - edge) == PULSE_FRONT_SPEED
        for front, edge in zip(fronts, (900, 9_100), strict=True)
    )


def test_boundary_camping_triggers_the_warned_lock() -> None:
    result = simulate_run(
        SOLVABLE_SEEDS[0],
        [UP] * duration_ticks(5),
        5,
    )
    assert not result.crossed
    assert result.collision_kind == "boundary"
    assert result.collision_tick is not None
    assert result.collision_tick >= BOUNDARY_PRESSURE_LIMIT


def test_static_center_is_interrupted_without_boundary_pressure() -> None:
    result = simulate_run(
        SOLVABLE_SEEDS[0],
        [0] * duration_ticks(5),
        5,
    )
    assert not result.crossed
    assert result.collision_kind == "pulse"
    assert result.max_boundary_pressure == 0


def test_crossing_inputs_support_all_four_directions() -> None:
    result = simulate_run(
        SOLVABLE_SEEDS[0],
        [UP, DOWN, LEFT, RIGHT] * (duration_ticks(5) // 4),
        5,
    )
    assert result.ticks > 0
