from __future__ import annotations

import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.deep_shaft.engine import (
    INPUT_LEFT,
    INPUT_RIGHT,
    MAX_TICKS,
    PLAYER_HALF_WIDTH,
    TARGET_FLOOR,
    DeepShaftEngine,
    advance_simulation,
    create_simulation,
    generate_platforms,
    simulate_run,
)


def make_room() -> tuple[
    DeepShaftEngine,
    ArcadeRoom,
    ArcadePlayer,
    list[float],
]:
    clock = [100.0]
    engine = DeepShaftEngine(
        clock=lambda: clock[0],
        rng=random.Random(1),
    )
    player = ArcadePlayer(
        id="player-1",
        account_id="account-1",
        name="挑战者",
        token_hash="token",
        seat=0,
    )
    room = ArcadeRoom(
        code="DOWN",
        game_key=engine.key,
        host_id=player.id,
        players=[player],
        state=engine.initial_state(),
    )
    engine.start(room)
    return engine, room, player, clock


def verified_route(seed: int) -> list[int]:
    """Simple test pilot that proves a real 100-floor replay can finish."""
    platforms = generate_platforms(seed)
    simulation = create_simulation(seed)
    inputs: list[int] = []
    while simulation.end_reason is None:
        target = platforms[min(simulation.deepest_floor + 1, TARGET_FLOOR)]
        target_center = target.x + target.width // 2
        if simulation.grounded_floor is not None:
            current = platforms[simulation.grounded_floor]
            if target_center < current.x:
                direction = -1
            elif target_center > current.x + current.width:
                direction = 1
            else:
                left_exit = current.x - PLAYER_HALF_WIDTH - 20
                right_exit = current.x + current.width + PLAYER_HALF_WIDTH + 20
                direction = (
                    -1
                    if abs(simulation.player_x - left_exit)
                    < abs(right_exit - simulation.player_x)
                    else 1
                )
        else:
            direction = (
                -1
                if simulation.player_x > target_center + 60
                else 1 if simulation.player_x < target_center - 60 else 0
            )
        input_mask = (
            INPUT_LEFT
            if direction < 0
            else INPUT_RIGHT if direction > 0 else 0
        )
        inputs.append(input_mask)
        advance_simulation(simulation, input_mask, platforms)
        assert len(inputs) <= MAX_TICKS
    assert simulation.end_reason == "completed"
    return inputs


def test_platform_generation_is_deterministic_reachable_and_hazard_spaced() -> None:
    for seed in range(1, 101):
        first = generate_platforms(seed)
        assert first == generate_platforms(seed)
        assert first[TARGET_FLOOR].kind == "normal"
        for current, following in zip(first, first[1:]):
            assert current.x < following.x + following.width
            assert following.x < current.x + current.width
        spike_floors = [
            platform.floor for platform in first if platform.kind == "spikes"
        ]
        assert all(
            right - left >= 4
            for left, right in zip(spike_floors, spike_floors[1:])
        )


def test_engine_accepts_a_server_replayed_hundred_floor_run() -> None:
    engine, room, player, clock = make_room()
    room.state.seed = 1
    inputs = verified_route(room.state.seed)
    clock[0] += 31

    engine.act(room, player, "finish", {"inputs": inputs})

    assert room.phase == "finished"
    assert room.winner == "completed"
    assert engine.player_score(room, player) == TARGET_FLOOR
    assert engine.record_state(room)["input_count"] == len(inputs)


def test_engine_replays_and_records_a_failed_run() -> None:
    engine, room, player, _ = make_room()
    inputs = [0] * MAX_TICKS
    result = simulate_run(room.state.seed, inputs)
    assert result.end_reason in {"fell", "health"}

    engine.act(room, player, "finish", {"inputs": inputs[: result.ticks]})

    assert room.phase == "finished"
    assert room.winner == result.end_reason
    assert engine.player_score(room, player) == result.deepest_floor


@pytest.mark.parametrize(
    "inputs",
    [[], [4], [True], [0] * (MAX_TICKS + 1)],
)
def test_engine_rejects_malformed_trajectories(inputs) -> None:
    engine, room, player, _ = make_room()

    with pytest.raises(GameRuleError):
        engine.act(room, player, "finish", {"inputs": inputs})


def test_engine_does_not_accept_an_instant_hundred_floor_run() -> None:
    engine, room, player, _ = make_room()
    room.state.seed = 1

    with pytest.raises(GameRuleError, match="完成得太快"):
        engine.act(
            room,
            player,
            "finish",
            {"inputs": verified_route(room.state.seed)},
        )


def test_maximum_duration_has_a_server_verified_timeout() -> None:
    simulation = create_simulation(42)
    simulation.tick = MAX_TICKS - 1
    simulation.camera_y = -5_000

    advance_simulation(simulation, 0)

    assert simulation.tick == MAX_TICKS
    assert simulation.end_reason == "timeout"


def test_deep_shaft_is_a_private_single_player_room() -> None:
    engine = DeepShaftEngine()

    assert engine.min_players == 1
    assert engine.max_players == 1
    assert engine.public_rooms is False
