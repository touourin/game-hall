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
    build_pulse_plan,
    build_safe_route,
    duration_ticks,
    pulse_fronts,
    pulse_sequence,
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

    assert [
        (pulse.kind, pulse.x_gate, pulse.y_gate) for pulse in plan
    ] == [
        ("cross", 6_728, 4_303),
        ("horizontal", 3_106, 4_276),
        ("vertical", 6_748, 2_295),
        ("horizontal", 6_704, 2_147),
        ("vertical", 6_540, 4_350),
    ]


def test_profiles_raise_cross_pressure_and_reduce_reaction_margin() -> None:
    calibration = DIFFICULTIES["5s"]
    overload = DIFFICULTIES["8s"]
    critical = DIFFICULTIES["10s"]

    assert calibration.pulse_weights[2] < overload.pulse_weights[2]
    assert overload.pulse_weights[2] < critical.pulse_weights[2]
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


def test_weighted_sequences_never_repeat_adjacent_pulse_kinds() -> None:
    for config in DIFFICULTIES.values():
        for seed in range(1, 1_025):
            sequence = pulse_sequence(seed, config)
            assert len(sequence) == config.pulse_count
            assert all(
                current != previous
                for previous, current in zip(sequence, sequence[1:])
            )


def test_difficulty_profiles_produce_distinct_cross_pulse_ratios() -> None:
    cross_ratios: dict[str, float] = {}
    for difficulty, config in DIFFICULTIES.items():
        sequences = (
            pulse_sequence(seed, config)
            for seed in range(1, 4_097)
        )
        kinds = [kind for sequence in sequences for kind in sequence]
        cross_ratios[difficulty] = kinds.count("cross") / len(kinds)

    assert cross_ratios["5s"] < 0.10
    assert 0.20 < cross_ratios["8s"] < 0.35
    assert 0.35 < cross_ratios["10s"] < 0.48


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_one_thousand_seeds_per_difficulty_have_a_verified_route(
    difficulty: str,
) -> None:
    config = DIFFICULTIES[difficulty]
    for seed in range(1, 1_001):
        result = simulate_run(seed, build_safe_route(seed, config), config)
        assert result.crossed, f"{difficulty=} {seed=}"
        assert result.collision_kind is None


def test_restart_changes_both_seed_and_pulse_sequence() -> None:
    config = DIFFICULTIES["5s"]
    engine, room, _, _ = make_room("5s")
    previous_seed = room.state.seed
    previous_sequence = pulse_sequence(previous_seed, config)

    engine.start(room)

    assert room.state.seed != previous_seed
    assert pulse_sequence(room.state.seed, config) != previous_sequence


def test_first_pulse_waits_for_its_profile_warning() -> None:
    config = DIFFICULTIES["5s"]
    plan = build_pulse_plan(162_944_417, config)
    assert pulse_fronts(plan, config.pulse_warning_ticks - 1, config) == []

    fronts = pulse_fronts(plan, config.pulse_warning_ticks, config)
    assert {front.side for front in fronts} == {"top", "bottom"}
    assert all(front.gate == plan[0].x_gate for front in fronts)
    assert all(
        abs(front.position - edge) == config.pulse_front_speed
        for front, edge in zip(fronts, (585, 5_915), strict=True)
    )


def test_boundary_camping_triggers_the_tuned_lock() -> None:
    config = DIFFICULTIES["5s"]
    result = simulate_run(
        162_944_417,
        [UP] * duration_ticks(config.duration_seconds),
        config,
    )
    assert not result.crossed
    assert result.collision_kind == "boundary"
    assert result.collision_tick is not None
    assert result.collision_tick >= config.boundary_pressure_limit


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
