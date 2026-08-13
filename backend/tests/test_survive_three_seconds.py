from __future__ import annotations

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.survive_three_seconds.engine import (
    DURATION_TICKS,
    EDGE_PRESSURE_LIMIT,
    LEFT,
    SOLVABLE_SEEDS,
    SurviveThreeSecondsEngine,
    UP,
    WAVE_BULLET_SPEED,
    WAVE_WARNING_TICKS,
    build_safe_route,
    simulate_run,
    spawn_bullets,
    wave_safe_gap,
)


def make_room(clock_value: float = 10.0):
    current = [clock_value]
    engine = SurviveThreeSecondsEngine(
        clock=lambda: current[0],
        rng=__import__("random").Random(42),
    )
    player = ArcadePlayer(
        id="player-1",
        account_id="account-1",
        name="挑战者",
        token_hash="token",
        seat=0,
    )
    room = ArcadeRoom(
        code="DODG",
        game_key=engine.key,
        host_id=player.id,
        players=[player],
        state=engine.initial_state(),
    )
    engine.start(room)
    return engine, room, player, current


def find_surviving_inputs(seed: int) -> list[int]:
    return build_safe_route(seed)


def test_engine_accepts_a_server_verified_survival() -> None:
    engine, room, player, clock = make_room()
    inputs = find_surviving_inputs(room.state.seed)
    clock[0] += 3.1

    engine.act(room, player, "finish", {"inputs": inputs})

    assert room.phase == "finished"
    assert room.winner == "survived"
    assert room.winner_player_ids == [player.id]
    assert engine.view(room, player)["survived"] is True


def test_engine_replays_a_collision_and_records_a_loss() -> None:
    engine, room, player, _ = make_room()
    inputs = [UP | LEFT] * DURATION_TICKS
    result = simulate_run(room.state.seed, inputs)
    assert result.collision_tick is not None

    engine.act(room, player, "finish", {"inputs": inputs[: result.ticks]})

    assert room.phase == "finished"
    assert room.winner == "hit"
    assert room.winner_player_ids == []
    assert room.state.collision_tick == result.collision_tick


@pytest.mark.parametrize("inputs", [[], [16], [True], [0] * (DURATION_TICKS + 1)])
def test_engine_rejects_invalid_trajectories(inputs) -> None:
    engine, room, player, _ = make_room()

    with pytest.raises(GameRuleError):
        engine.act(room, player, "finish", {"inputs": inputs})


def test_engine_does_not_accept_an_instant_success() -> None:
    engine, room, player, _ = make_room()
    inputs = find_surviving_inputs(room.state.seed)

    with pytest.raises(GameRuleError, match="完成得太快"):
        engine.act(room, player, "finish", {"inputs": inputs})


def test_every_started_round_has_a_verified_escape_lane() -> None:
    engine, room, _, _ = make_room()

    for _ in range(20):
        engine.start(room)
        assert simulate_run(room.state.seed, build_safe_route(room.state.seed)).survived


def test_each_wave_warns_before_spawning_a_slow_curtain() -> None:
    seed = SOLVABLE_SEEDS[0]
    assert spawn_bullets(seed, WAVE_WARNING_TICKS - 1) == []

    bullets = spawn_bullets(seed, WAVE_WARNING_TICKS)
    gap = wave_safe_gap(seed, 0, "y")
    assert len(bullets) > 20
    assert all(abs(bullet.vx) == WAVE_BULLET_SPEED for bullet in bullets)
    assert all(bullet.vy == 0 for bullet in bullets)
    assert all(abs(bullet.y - gap) > 850 for bullet in bullets)


def test_every_seed_has_a_server_verified_readable_route() -> None:
    for seed in SOLVABLE_SEEDS:
        result = simulate_run(seed, build_safe_route(seed))
        assert result.survived
        assert result.collision_kind is None


def test_corner_camping_triggers_the_warned_edge_wall() -> None:
    result = simulate_run(
        SOLVABLE_SEEDS[0],
        [UP] * DURATION_TICKS,
    )
    assert not result.survived
    assert result.collision_kind == "edge_wall"
    assert result.collision_tick is not None
    assert result.collision_tick >= EDGE_PRESSURE_LIMIT


def test_static_center_is_hit_by_a_wave_without_edge_pressure() -> None:
    for seed in SOLVABLE_SEEDS:
        result = simulate_run(seed, [0] * DURATION_TICKS)
        assert not result.survived
        assert result.collision_kind == "bullet"
        assert result.max_edge_pressure == 0
