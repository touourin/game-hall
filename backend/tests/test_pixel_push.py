from __future__ import annotations

import copy
import math
import random

import pytest

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError
from backend.app.games.pixel_push.engine import (
    ACTIVE_ROUND_TICKS,
    COUNTDOWN_TICKS,
    DISCONNECT_KO_TICKS,
    INPUT_BRACE,
    INPUT_DASH,
    INPUT_RIGHT,
    MAP_CROSS_BRIDGE,
    MAP_MOON_STATION,
    MAP_PULSE_FACTORY,
    PLAYER_RADIUS,
    PixelPushEngine,
    ROUND_RESULT_TICKS,
)
from backend.app.games.registry import build_engine_registry


class FixedRng:
    def __init__(self, value: int = 0) -> None:
        self.value = value

    def randrange(self, stop: int) -> int:
        return self.value % stop


def make_room(
    engine: PixelPushEngine,
    count: int = 2,
    *,
    arena: str = MAP_MOON_STATION,
) -> ArcadeRoom:
    players = [
        ArcadePlayer(
            id=f"p{seat}",
            account_id=f"a{seat}",
            name=f"玩家{seat + 1}",
            token_hash=f"token-{seat}",
            seat=seat,
        )
        for seat in range(count)
    ]
    room = ArcadeRoom(
        code="PUSH",
        game_key="pixel_push",
        host_id=players[0].id,
        players=players,
        state=engine.initial_state(),
        options={"arena": arena},
    )
    engine.start(room)
    return room


def activate(room: ArcadeRoom) -> None:
    room.state.stage = "active"
    room.state.stage_ticks_remaining = ACTIVE_ROUND_TICKS
    room.state.round_ticks_remaining = ACTIVE_ROUND_TICKS


def test_pixel_push_is_registered_for_two_to_four_players() -> None:
    engine = build_engine_registry()["pixel_push"]

    assert engine.name == "像素推推王"
    assert engine.min_players == 2
    assert engine.max_players == 4
    assert engine.realtime_tick_rate == 30


def test_pixel_push_validates_map_options_and_starts_a_countdown() -> None:
    engine = PixelPushEngine(FixedRng(1))

    assert engine.room_options({}) == {"arena": "rotation"}
    assert engine.room_options({"arena": MAP_CROSS_BRIDGE}) == {
        "arena": MAP_CROSS_BRIDGE
    }
    with pytest.raises(GameRuleError, match="地图"):
        engine.room_options({"arena": "missing"})

    room = make_room(engine, 4)

    assert room.phase == "playing"
    assert room.state.stage == "countdown"
    assert room.state.stage_ticks_remaining == COUNTDOWN_TICKS
    assert len({(actor.x, actor.y) for actor in room.state.players.values()}) == 4
    assert set(room.state.round_wins.values()) == {0}


def test_realtime_input_is_ordered_and_dash_uses_a_rising_edge() -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine)
    player = room.players[0]

    assert engine.apply_input(room, player, 4, INPUT_RIGHT | INPUT_DASH) is True
    assert engine.apply_input(room, player, 4, INPUT_RIGHT) is False
    assert engine.apply_input(room, player, 3, 0) is False
    assert room.state.players[player.id].dash_requested is True

    with pytest.raises(GameRuleError, match="输入序号"):
        engine.apply_input(room, player, -1, 0)
    with pytest.raises(GameRuleError, match="移动输入"):
        engine.apply_input(room, player, 5, 128)


def test_dash_collision_adds_balance_and_knockback() -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine)
    activate(room)
    attacker = room.state.players["p0"]
    target = room.state.players["p1"]
    attacker.x = attacker.previous_x = 4_200
    attacker.y = attacker.previous_y = 3_500
    target.x = target.previous_x = 4_810
    target.y = target.previous_y = 3_500
    attacker.facing_x = attacker.dash_direction_x = 1_000
    attacker.facing_y = attacker.dash_direction_y = 0
    attacker.dash_ticks = 3

    engine.tick(room)

    assert target.balance > 0
    assert target.velocity_x > 0
    assert target.last_hit_by == attacker.player_id
    assert any(event.kind == "hit" for event in room.state.events)


def test_front_brace_reduces_knockback_and_stops_the_dash() -> None:
    engine = PixelPushEngine(FixedRng())
    unbraced_room = make_room(engine)
    braced_room = copy.deepcopy(unbraced_room)
    braced_room.lock = unbraced_room.lock
    for room in (unbraced_room, braced_room):
        activate(room)
        attacker = room.state.players["p0"]
        target = room.state.players["p1"]
        attacker.x = attacker.previous_x = 4_200
        attacker.y = attacker.previous_y = 3_500
        target.x = target.previous_x = 4_810
        target.y = target.previous_y = 3_500
        attacker.facing_x = attacker.dash_direction_x = 1_000
        attacker.facing_y = attacker.dash_direction_y = 0
        attacker.dash_ticks = 3
        target.facing_x = -1_000
        target.facing_y = 0
    braced_room.state.players["p1"].input_mask = INPUT_BRACE

    engine.tick(unbraced_room)
    engine.tick(braced_room)

    unbraced_speed = unbraced_room.state.players["p1"].velocity_x
    braced_speed = braced_room.state.players["p1"].velocity_x
    assert 0 < braced_speed < unbraced_speed
    assert braced_room.state.players["p0"].dash_ticks == 0
    assert any(event.kind == "braced" for event in braced_room.state.events)


def test_ring_out_finishes_the_round_and_advances_the_score() -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine)
    activate(room)
    loser = room.state.players["p1"]
    loser.x = loser.previous_x = -2_000

    for _ in range(5):
        engine.tick(room)

    assert loser.alive is False
    assert room.state.stage == "round_result"
    assert room.state.round_winner_id == "p0"
    assert room.state.round_wins["p0"] == 1


def test_disconnected_player_is_removed_from_the_current_round() -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine)
    activate(room)
    room.players[1].connected = False

    for _ in range(DISCONNECT_KO_TICKS):
        engine.tick(room)

    assert room.state.players["p1"].alive is False
    assert room.state.stage == "round_result"
    assert any(event.kind == "disconnect" for event in room.state.events)


def test_reconnecting_during_the_next_countdown_restores_the_player() -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine)
    activate(room)
    room.players[1].connected = False

    for _ in range(DISCONNECT_KO_TICKS):
        engine.tick(room)
    assert room.state.stage == "round_result"
    assert room.state.players["p1"].alive is False

    room.players[1].connected = True
    for _ in range(ROUND_RESULT_TICKS):
        engine.tick(room)

    assert room.state.stage == "countdown"
    assert room.state.players["p1"].alive is True
    assert room.state.players["p1"].disconnected_ticks == 0


def test_disconnect_or_forfeit_does_not_count_as_a_ring_out() -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine, 3)
    activate(room)
    room.players[1].connected = False
    engine.manual_forfeit(room, room.players[2])

    for _ in range(DISCONNECT_KO_TICKS):
        engine.tick(room)

    assert room.state.players["p1"].ring_outs == 0
    assert room.state.players["p2"].ring_outs == 0


def test_all_offline_freezes_the_authoritative_clock() -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine)
    activate(room)
    for player in room.players:
        player.connected = False
    tick_before = room.state.tick
    timer_before = room.state.round_ticks_remaining

    assert engine.tick(room) is False

    assert room.state.tick == tick_before
    assert room.state.round_ticks_remaining == timer_before
    assert room.state.frozen is True


def test_same_state_and_inputs_produce_the_same_authoritative_result() -> None:
    first_engine = PixelPushEngine(FixedRng())
    second_engine = PixelPushEngine(FixedRng())
    first_room = make_room(first_engine, 4, arena=MAP_CROSS_BRIDGE)
    second_room = make_room(second_engine, 4, arena=MAP_CROSS_BRIDGE)
    activate(first_room)
    activate(second_room)

    for sequence in range(1, 121):
        first_mask = INPUT_RIGHT | (INPUT_DASH if sequence in {1, 61} else 0)
        second_mask = INPUT_BRACE if sequence < 50 else 0
        for engine, room in (
            (first_engine, first_room),
            (second_engine, second_room),
        ):
            engine.apply_input(room, room.players[0], sequence, first_mask)
            engine.apply_input(room, room.players[1], sequence, second_mask)
            engine.tick(room)

    assert first_engine.realtime_frame(first_room) == second_engine.realtime_frame(
        second_room
    )


@pytest.mark.parametrize(
    ("count", "arena"),
    [
        (2, MAP_MOON_STATION),
        (3, MAP_CROSS_BRIDGE),
        (4, MAP_PULSE_FACTORY),
    ],
)
def test_seeded_random_matches_keep_physics_bounded_and_finish(
    count: int,
    arena: str,
) -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine, count, arena=arena)
    activate(room)
    rng = random.Random(24_081_500 + count)
    movement_masks = [
        0,
        INPUT_RIGHT,
        1,
        2,
        4,
        1 | 4,
        1 | INPUT_RIGHT,
        2 | 4,
        2 | INPUT_RIGHT,
        INPUT_BRACE,
    ]

    for sequence in range(8_000):
        if room.phase == "finished":
            break
        if room.state.stage == "active":
            for player in room.players:
                mask = rng.choice(movement_masks)
                if rng.random() < 0.04:
                    mask |= INPUT_DASH
                engine.apply_input(room, player, sequence, mask)
        engine.tick(room)

        assert len(room.state.events) <= 24
        alive = [actor for actor in room.state.players.values() if actor.alive]
        for actor in room.state.players.values():
            assert all(
                isinstance(value, int)
                for value in (
                    actor.x,
                    actor.y,
                    actor.velocity_x,
                    actor.velocity_y,
                    actor.balance,
                )
            )
            assert abs(actor.velocity_x) < 2_000
            assert abs(actor.velocity_y) < 2_000
            assert 0 <= actor.balance <= 100
        for index, first in enumerate(alive):
            for second in alive[index + 1 :]:
                distance = math.isqrt(
                    (first.x - second.x) ** 2
                    + (first.y - second.y) ** 2
                )
                assert distance >= PLAYER_RADIUS * 2 - 3

    assert room.phase == "finished"
    assert len(room.winner_player_ids) == 1


def test_first_player_to_two_rounds_finishes_and_records_the_match() -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine)

    for expected_score in (1, 2):
        activate(room)
        loser = room.state.players["p1"]
        loser.x = loser.previous_x = -2_000
        for _ in range(4):
            engine.tick(room)
        assert room.state.round_wins["p0"] == expected_score
        for _ in range(ROUND_RESULT_TICKS):
            engine.tick(room)

    assert room.phase == "finished"
    assert room.winner_player_ids == ["p0"]
    assert "2 个回合胜利" in (room.win_reason or "")


def test_view_and_record_state_exclude_internal_collision_sets() -> None:
    engine = PixelPushEngine(FixedRng())
    room = make_room(engine, 3)

    view = engine.view(room, room.players[0])
    record = engine.record_state(room)

    assert view["currentMap"] == MAP_MOON_STATION
    assert len(view["players"]) == 3
    assert view["world"]["playerRadius"] > 0
    assert set(record) == {"mapSequence", "roundNumber", "roundWins", "players"}
    assert "dash_hit_ids" not in str(record)
