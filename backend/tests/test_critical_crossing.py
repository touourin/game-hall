from __future__ import annotations

import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.critical_crossing.engine import (
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    DOWN,
    LEFT,
    RIGHT,
    UP,
    CriticalCrossingEngine,
    boundary_collision,
    build_pulse_plan,
    build_safe_route,
    duration_ticks,
    pulse_fronts,
    simulate_run,
    update_boundary_pressure,
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


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_each_difficulty_accepts_a_server_verified_crossing(
    difficulty: str,
) -> None:
    config = DIFFICULTIES[difficulty]
    engine, room, player, clock = make_room(difficulty)
    inputs = build_safe_route(room.state.seed, config)
    clock[0] += config.duration_seconds + 0.1

    engine.act(room, player, "finish", {"inputs": inputs})

    assert room.phase == "finished"
    assert room.winner == "crossed"
    assert room.winner_player_ids == [player.id]
    assert room.state.difficulty == difficulty
    assert room.state.elapsed_ms == config.duration_seconds * 1_000
    assert engine.view(room, player)["crossed"] is True


def test_engine_replays_a_collision_and_records_an_interruption() -> None:
    config = DIFFICULTIES["5s"]
    engine, room, player, _ = make_room("5s")
    inputs = [UP | LEFT] * duration_ticks(config.duration_seconds)
    result = simulate_run(room.state.seed, inputs, config)
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
    config = DIFFICULTIES["5s"]
    engine, room, player, _ = make_room("5s")
    inputs = build_safe_route(room.state.seed, config)

    with pytest.raises(GameRuleError, match="完成得太快"):
        engine.act(room, player, "finish", {"inputs": inputs})


def test_fixed_plan_vector_matches_the_browser_engine() -> None:
    plan = build_pulse_plan(3_000_000_005, DIFFICULTIES["5s"])

    assert [(pulse.x_gate, pulse.y_gate) for pulse in plan] == [
        (6_728, 4_303),
        (3_106, 4_276),
        (6_748, 2_295),
        (6_704, 2_147),
        (6_540, 4_350),
    ]


def test_profiles_reduce_reaction_and_boundary_margins() -> None:
    calibration = DIFFICULTIES["5s"]
    overload = DIFFICULTIES["8s"]
    critical = DIFFICULTIES["10s"]

    assert (
        calibration.pulse_warning_ticks
        > overload.pulse_warning_ticks
        > critical.pulse_warning_ticks
    )
    assert (
        calibration.safe_gate_radius
        > overload.safe_gate_radius
        > critical.safe_gate_radius
    )
    assert (
        calibration.boundary_pressure_limit
        > overload.boundary_pressure_limit
        > critical.boundary_pressure_limit
    )


def test_seeded_intersections_use_all_four_board_quadrants() -> None:
    config = DIFFICULTIES["10s"]
    quadrant_counts = {(x, y): 0 for x in range(2) for y in range(2)}
    for seed in range(1, 4_097):
        for pulse in build_pulse_plan(seed, config):
            quadrant = (int(pulse.x_gate > 5_000), int(pulse.y_gate > 3_250))
            quadrant_counts[quadrant] += 1

    total = sum(quadrant_counts.values())
    assert all(0.23 < count / total < 0.27 for count in quadrant_counts.values())


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_one_thousand_seeds_per_difficulty_have_a_verified_route(
    difficulty: str,
) -> None:
    config = DIFFICULTIES[difficulty]
    for seed in range(1, 1_001):
        result = simulate_run(seed, build_safe_route(seed, config), config)
        assert result.crossed, f"{difficulty=} {seed=}"
        assert result.collision_kind is None


def test_restart_changes_both_seed_and_intersection_route() -> None:
    config = DIFFICULTIES["5s"]
    engine, room, _, _ = make_room("5s")
    previous_seed = room.state.seed
    previous_plan = build_pulse_plan(previous_seed, config)

    engine.start(room)

    assert room.state.seed != previous_seed
    assert build_pulse_plan(room.state.seed, config) != previous_plan


def test_first_pulse_waits_for_its_profile_warning() -> None:
    config = DIFFICULTIES["5s"]
    plan = build_pulse_plan(162_944_417, config)
    assert pulse_fronts(plan, config.pulse_warning_ticks - 1, config) == []

    fronts = pulse_fronts(plan, config.pulse_warning_ticks, config)
    assert [front.side for front in fronts] == [
        "top",
        "right",
        "bottom",
        "left",
    ]
    assert [front.gate for front in fronts] == [
        plan[0].x_gate,
        plan[0].y_gate,
        plan[0].x_gate,
        plan[0].y_gate,
    ]
    assert [front.position for front in fronts] == [
        585 + config.pulse_front_speed,
        9_100 - config.pulse_front_speed,
        5_915 - config.pulse_front_speed,
        900 + config.pulse_front_speed,
    ]


def test_boundary_camping_triggers_the_tuned_lock() -> None:
    config = DIFFICULTIES["5s"]
    pressure = {side: 0 for side in ("top", "right", "bottom", "left")}
    for _ in range(config.boundary_pressure_limit):
        pressure = update_boundary_pressure(pressure, 105, 3_250, config)
    assert not boundary_collision(105, 3_250, pressure, config)

    pressure = update_boundary_pressure(pressure, 105, 3_250, config)
    assert boundary_collision(105, 3_250, pressure, config)


def test_static_center_is_interrupted_without_boundary_pressure() -> None:
    config = DIFFICULTIES["5s"]
    result = simulate_run(
        162_944_417,
        [0] * duration_ticks(config.duration_seconds),
        config,
    )
    assert not result.crossed
    assert result.collision_kind == "pulse"
    assert result.max_boundary_pressure == 0


def test_crossing_inputs_support_all_four_directions() -> None:
    config = DIFFICULTIES["5s"]
    result = simulate_run(
        162_944_417,
        [UP, DOWN, LEFT, RIGHT]
        * (duration_ticks(config.duration_seconds) // 4),
        config,
    )
    assert result.ticks > 0
