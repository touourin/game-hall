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
    build_course_plan,
    build_safe_route,
    duration_ticks,
    runner_distance_meters,
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
def test_each_difficulty_accepts_a_server_verified_bridge_run(
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
    assert room.state.distance_meters == config.duration_seconds * 18
    assert room.state.passed_sections == config.section_count
    assert engine.view(room, player)["crossed"] is True


def test_engine_replays_a_barrier_collision_and_records_an_interruption() -> None:
    config = DIFFICULTIES["5s"]
    engine, room, player, _ = make_room("5s")
    inputs = [0] * duration_ticks(config.duration_seconds)
    result = simulate_run(room.state.seed, inputs, config)
    assert result.collision_tick is not None

    engine.act(room, player, "finish", {"inputs": inputs[: result.ticks]})

    assert room.phase == "finished"
    assert room.winner == "interrupted"
    assert room.winner_player_ids == []
    assert room.state.collision_tick == result.collision_tick
    assert room.state.distance_meters == runner_distance_meters(result.ticks)


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
    plan = build_course_plan(3_000_000_005, DIFFICULTIES["5s"])

    assert [
        (
            section.impact_tick,
            section.branch_count,
            section.active_lanes,
            section.obstacles,
            section.safe_lane,
        )
        for section in plan
    ] == [
        (50, 2, (0, 1), ("gap", "barrier", "ground"), 1),
        (110, 3, (-1, 0, 1), ("barrier", "overhead", "barrier"), 0),
        (170, 3, (-1, 0, 1), ("clear", "barrier", "barrier"), -1),
        (230, 2, (0, 1), ("gap", "barrier", "ground"), 1),
        (290, 3, (-1, 0, 1), ("overhead", "barrier", "barrier"), -1),
    ]


def test_every_short_course_mixes_two_and_three_way_forks_and_actions() -> None:
    config = DIFFICULTIES["5s"]
    for seed in range(1, 257):
        plan = build_course_plan(seed, config)
        assert {section.branch_count for section in plan} == {2, 3}
        obstacles = {
            obstacle
            for section in plan
            for obstacle in section.obstacles
        }
        assert {"ground", "overhead"} <= obstacles


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_one_thousand_seeds_per_difficulty_have_a_verified_route(
    difficulty: str,
) -> None:
    config = DIFFICULTIES[difficulty]
    for seed in range(1, 1_001):
        result = simulate_run(seed, build_safe_route(seed, config), config)
        assert result.crossed, f"{difficulty=} {seed=}"
        assert result.collision_kind is None
        assert result.passed_sections == config.section_count


def test_w_and_s_are_required_for_ground_and_overhead_obstacles() -> None:
    config = DIFFICULTIES["5s"]
    seed = 3_000_000_005
    route = build_safe_route(seed, config)
    assert route[30] == UP
    without_jump = route.copy()
    without_jump[30] = 0
    assert simulate_run(seed, without_jump, config).collision_kind == "ground"

    assert route[90] == DOWN
    without_slide = route.copy()
    without_slide[90] = 0
    assert simulate_run(seed, without_slide, config).collision_kind == "overhead"


def test_held_direction_changes_only_one_lane_until_released() -> None:
    config = DIFFICULTIES["5s"]
    result = simulate_run(1, [RIGHT] * 20, config)
    assert result.player_lane == 1

    result = simulate_run(1, [LEFT, 0, LEFT] + [0] * 17, config)
    assert result.player_lane == -1


def test_restart_changes_both_seed_and_bridge_route() -> None:
    config = DIFFICULTIES["5s"]
    engine, room, _, _ = make_room("5s")
    previous_seed = room.state.seed
    previous_plan = build_course_plan(previous_seed, config)

    engine.start(room)

    assert room.state.seed != previous_seed
    assert build_course_plan(room.state.seed, config) != previous_plan


def test_input_mask_supports_all_four_keyboard_actions() -> None:
    config = DIFFICULTIES["5s"]
    result = simulate_run(
        162_944_417,
        [UP, 0, DOWN, 0, LEFT, 0, RIGHT, 0] * 4,
        config,
    )
    assert result.ticks > 0
