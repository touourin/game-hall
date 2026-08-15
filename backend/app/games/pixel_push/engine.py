from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


TICK_RATE = 30
SNAPSHOT_RATE = 15
WORLD_WIDTH = 10_000
WORLD_HEIGHT = 7_000
WORLD_CENTER_X = WORLD_WIDTH // 2
WORLD_CENTER_Y = WORLD_HEIGHT // 2

PLAYER_RADIUS = 330
MOVE_ACCELERATION = 24
MOVE_FRICTION = 17
MOVE_MAX_SPEED = 112
BRACE_MAX_SPEED = 42
BRACE_FRICTION = 28
DASH_SPEED = 270
DASH_TICKS = 8
DASH_COOLDOWN_TICKS = 42
DASH_BALANCE_GAIN = 16
DASH_BASE_KNOCKBACK = 126
DASH_BALANCE_KNOCKBACK = 3
MAX_KNOCKBACK_SPEED = 640
MAX_SIMULATION_SUBSTEPS = 8
BRACE_FRONT_FACTOR = 30
BRACE_REAR_FACTOR = 66
BRACE_RECOIL = 82
SIDE_HIT_BONUS = 5
BALANCE_MAX = 100
BALANCE_RECOVERY_DELAY_TICKS = 48
BALANCE_RECOVERY_INTERVAL_TICKS = 6
RING_OUT_GRACE_TICKS = 4
DISCONNECT_KO_TICKS = 5 * TICK_RATE

COUNTDOWN_TICKS = 3 * TICK_RATE
ACTIVE_ROUND_TICKS = 45 * TICK_RATE
SUDDEN_DEATH_TICKS = 15 * TICK_RATE
ROUND_RESULT_TICKS = 3 * TICK_RATE
ROUNDS_TO_WIN = 2
MAX_ROUNDS = 7

INPUT_UP = 1
INPUT_DOWN = 2
INPUT_LEFT = 4
INPUT_RIGHT = 8
INPUT_DASH = 16
INPUT_BRACE = 32
VALID_INPUT_MASK = (
    INPUT_UP
    | INPUT_DOWN
    | INPUT_LEFT
    | INPUT_RIGHT
    | INPUT_DASH
    | INPUT_BRACE
)

MAP_ROTATION = "rotation"
MAP_MOON_STATION = "moon_station"
MAP_CROSS_BRIDGE = "cross_bridge"
MAP_PULSE_FACTORY = "pulse_factory"
MAP_KEYS = (MAP_MOON_STATION, MAP_CROSS_BRIDGE, MAP_PULSE_FACTORY)
MAP_OPTIONS = {MAP_ROTATION, *MAP_KEYS}

PLAYER_COLORS = ("#5ce1e6", "#ff6f91", "#ffd166", "#a78bfa")

RoundStage = Literal["countdown", "active", "round_result"]


@dataclass
class PixelPushPlayerState:
    player_id: str
    seat: int
    x: int = WORLD_CENTER_X
    y: int = WORLD_CENTER_Y
    previous_x: int = WORLD_CENTER_X
    previous_y: int = WORLD_CENTER_Y
    velocity_x: int = 0
    velocity_y: int = 0
    facing_x: int = 1_000
    facing_y: int = 0
    input_mask: int = 0
    last_input_sequence: int = -1
    dash_requested: bool = False
    dash_ticks: int = 0
    dash_cooldown_ticks: int = 0
    dash_direction_x: int = 1_000
    dash_direction_y: int = 0
    dash_hit_ids: set[str] = field(default_factory=set)
    balance: int = 0
    balance_recovery_ticks: int = 0
    alive: bool = True
    outside_ticks: int = 0
    disconnected_ticks: int = 0
    last_hit_by: str | None = None
    last_hit_tick: int = -10_000
    eliminations: int = 0
    ring_outs: int = 0
    pulse_cycle: int = -1


@dataclass
class PixelPushEvent:
    event_id: int
    tick: int
    kind: str
    actor_id: str | None = None
    target_id: str | None = None
    value: int | None = None


@dataclass
class PixelPushState:
    tick: int = 0
    stage: RoundStage = "countdown"
    stage_ticks_remaining: int = COUNTDOWN_TICKS
    round_ticks_remaining: int = ACTIVE_ROUND_TICKS
    round_number: int = 1
    map_sequence: list[str] = field(default_factory=list)
    current_map: str = MAP_MOON_STATION
    players: dict[str, PixelPushPlayerState] = field(default_factory=dict)
    round_wins: dict[str, int] = field(default_factory=dict)
    round_winner_id: str | None = None
    match_winner_id: str | None = None
    events: list[PixelPushEvent] = field(default_factory=list)
    next_event_id: int = 1
    frozen: bool = False


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return min(maximum, max(minimum, value))


def _approach_zero(value: int, amount: int) -> int:
    if value > 0:
        return max(0, value - amount)
    if value < 0:
        return min(0, value + amount)
    return 0


def _approach(value: int, target: int, amount: int) -> int:
    if value < target:
        return min(target, value + amount)
    if value > target:
        return max(target, value - amount)
    return value


def _normalized_direction(x: int, y: int) -> tuple[int, int]:
    if x == 0 and y == 0:
        return 0, 0
    if x != 0 and y != 0:
        return (707 if x > 0 else -707), (707 if y > 0 else -707)
    return (1_000 if x > 0 else -1_000 if x < 0 else 0), (
        1_000 if y > 0 else -1_000 if y < 0 else 0
    )


def _input_direction(mask: int) -> tuple[int, int]:
    horizontal = int(bool(mask & INPUT_RIGHT)) - int(bool(mask & INPUT_LEFT))
    vertical = int(bool(mask & INPUT_DOWN)) - int(bool(mask & INPUT_UP))
    return _normalized_direction(horizontal, vertical)


def _inside_rounded_rectangle(
    x: int,
    y: int,
    half_width: int,
    half_height: int,
    corner_radius: int,
) -> bool:
    local_x = abs(x - WORLD_CENTER_X)
    local_y = abs(y - WORLD_CENTER_Y)
    if local_x > half_width or local_y > half_height:
        return False
    inner_x = half_width - corner_radius
    inner_y = half_height - corner_radius
    if local_x <= inner_x or local_y <= inner_y:
        return True
    corner_x = local_x - inner_x
    corner_y = local_y - inner_y
    return corner_x * corner_x + corner_y * corner_y <= corner_radius**2


def _shrink_progress(state: PixelPushState) -> int:
    if state.stage != "active":
        return 0
    elapsed_sudden_ticks = SUDDEN_DEATH_TICKS - min(
        SUDDEN_DEATH_TICKS,
        state.round_ticks_remaining,
    )
    return _clamp(elapsed_sudden_ticks * 1_000 // SUDDEN_DEATH_TICKS, 0, 1_000)


def _inside_arena(state: PixelPushState, x: int, y: int) -> bool:
    progress = _shrink_progress(state)
    if state.current_map == MAP_MOON_STATION:
        half_width = 4_200 - progress * 2_150 // 1_000
        half_height = 2_700 - progress * 1_150 // 1_000
        return _inside_rounded_rectangle(x, y, half_width, half_height, 760)

    if state.current_map == MAP_CROSS_BRIDGE:
        central_half_width = 1_900
        central_half_height = 1_450
        arm_x = 2_250 * (1_000 - progress) // 1_000
        arm_y = 1_100 * (1_000 - progress) // 1_000
        local_x = abs(x - WORLD_CENTER_X)
        local_y = abs(y - WORLD_CENTER_Y)
        in_centre = (
            local_x <= central_half_width
            and local_y <= central_half_height
        )
        in_horizontal_arm = (
            local_x <= central_half_width + arm_x and local_y <= 720
        )
        in_vertical_arm = (
            local_x <= 720 and local_y <= central_half_height + arm_y
        )
        return in_centre or in_horizontal_arm or in_vertical_arm

    half_width = 4_250 - progress * 1_050 // 1_000
    half_height = 2_450 - progress * 1_150 // 1_000
    return _inside_rounded_rectangle(x, y, half_width, half_height, 420)


def _distance_from_center_squared(player: PixelPushPlayerState) -> int:
    return (player.x - WORLD_CENTER_X) ** 2 + (player.y - WORLD_CENTER_Y) ** 2


def _spawn_positions(count: int) -> list[tuple[int, int, int, int]]:
    if count == 2:
        return [
            (WORLD_CENTER_X - 1_900, WORLD_CENTER_Y, 1_000, 0),
            (WORLD_CENTER_X + 1_900, WORLD_CENTER_Y, -1_000, 0),
        ]
    if count == 3:
        return [
            (WORLD_CENTER_X, WORLD_CENTER_Y - 1_750, 0, 1_000),
            (WORLD_CENTER_X - 1_700, WORLD_CENTER_Y + 1_050, 707, -707),
            (WORLD_CENTER_X + 1_700, WORLD_CENTER_Y + 1_050, -707, -707),
        ]
    return [
        (WORLD_CENTER_X - 1_650, WORLD_CENTER_Y - 1_250, 707, 707),
        (WORLD_CENTER_X + 1_650, WORLD_CENTER_Y - 1_250, -707, 707),
        (WORLD_CENTER_X + 1_650, WORLD_CENTER_Y + 1_250, -707, -707),
        (WORLD_CENTER_X - 1_650, WORLD_CENTER_Y + 1_250, 707, -707),
    ]


class PixelPushEngine:
    key = "pixel_push"
    name = "像素推推王"
    min_players = 2
    max_players = 4
    public_rooms = True
    realtime_tick_rate = TICK_RATE
    realtime_snapshot_rate = SNAPSHOT_RATE

    def __init__(
        self,
        rng: random.Random | random.SystemRandom | None = None,
    ) -> None:
        self.rng = rng or random.SystemRandom()

    def initial_state(self) -> PixelPushState:
        return PixelPushState()

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        arena = options.get("arena", MAP_ROTATION)
        if not isinstance(arena, str) or arena not in MAP_OPTIONS:
            raise GameRuleError("请选择轮换擂台或一张有效地图")
        return {"arena": arena}

    def start(self, room: ArcadeRoom) -> None:
        active_players = [player for player in room.players if not player.left_room]
        if not self.min_players <= len(active_players) <= self.max_players:
            raise GameRuleError("像素推推王需要 2–4 名玩家")
        arena = str(room.options.get("arena", MAP_ROTATION))
        if arena == MAP_ROTATION:
            offset = self.rng.randrange(len(MAP_KEYS))
            sequence = [*MAP_KEYS[offset:], *MAP_KEYS[:offset]]
        else:
            sequence = [arena]
        state = PixelPushState(
            map_sequence=sequence,
            current_map=sequence[0],
            round_wins={player.id: 0 for player in active_players},
        )
        state.players = {
            player.id: PixelPushPlayerState(
                player_id=player.id,
                seat=player.seat,
            )
            for player in active_players
        }
        room.state = state
        room.phase = "playing"
        self._reset_round(state, active_players, first_round=True)

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if action == "resign":
            self.manual_forfeit(room, player)
            return
        if action != "input":
            raise GameRuleError("不支持这个推推王操作")
        sequence = payload.get("sequence")
        input_mask = payload.get("inputMask")
        self.apply_input(room, player, sequence, input_mask)

    def apply_input(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        sequence: Any,
        input_mask: Any,
    ) -> bool:
        if room.phase != "playing":
            raise GameRuleError("当前对局不接收移动输入")
        if (
            not isinstance(sequence, int)
            or isinstance(sequence, bool)
            or sequence < 0
            or sequence > 2_147_483_647
        ):
            raise GameRuleError("输入序号不正确")
        if (
            not isinstance(input_mask, int)
            or isinstance(input_mask, bool)
            or input_mask < 0
            or input_mask & ~VALID_INPUT_MASK
        ):
            raise GameRuleError("移动输入不正确")
        state: PixelPushState = room.state
        actor = state.players.get(player.id)
        if actor is None or player.left_room:
            raise GameRuleError("你已经不在当前对局中")
        if sequence <= actor.last_input_sequence:
            return False
        dash_pressed = bool(
            input_mask & INPUT_DASH and not actor.input_mask & INPUT_DASH
        )
        actor.last_input_sequence = sequence
        actor.input_mask = input_mask
        if dash_pressed:
            actor.dash_requested = True
        return True

    def tick(self, room: ArcadeRoom) -> bool:
        if room.phase != "playing":
            return False
        state: PixelPushState = room.state
        room_players = {
            player.id: player
            for player in room.players
            if not player.left_room and player.id in state.players
        }
        if not room_players:
            return False
        if not any(player.connected for player in room_players.values()):
            state.frozen = True
            return False
        state.frozen = False
        state.tick += 1
        self._update_connections(state, room_players)

        if state.stage == "countdown":
            for actor in state.players.values():
                actor.dash_requested = False
            state.stage_ticks_remaining -= 1
            if state.stage_ticks_remaining <= 0:
                state.stage = "active"
                state.stage_ticks_remaining = ACTIVE_ROUND_TICKS
                self._add_event(state, "round_started")
            return True

        if state.stage == "round_result":
            state.stage_ticks_remaining -= 1
            if state.stage_ticks_remaining <= 0:
                if state.match_winner_id is not None:
                    winner = room.player(state.match_winner_id)
                    score = state.round_wins[state.match_winner_id]
                    room.finish(
                        "last_standing",
                        [state.match_winner_id],
                        f"{winner.name} 以 {score} 个回合胜利成为推推王",
                    )
                    return True
                active_players = [
                    player
                    for player in room.players
                    if not player.left_room and player.id in state.players
                ]
                state.round_number += 1
                state.current_map = state.map_sequence[
                    (state.round_number - 1) % len(state.map_sequence)
                ]
                self._reset_round(state, active_players, first_round=False)
            return True

        self._advance_active_round(state, room_players)
        return True

    def _advance_active_round(
        self,
        state: PixelPushState,
        room_players: dict[str, ArcadePlayer],
    ) -> None:
        state.round_ticks_remaining = max(0, state.round_ticks_remaining - 1)
        state.stage_ticks_remaining = state.round_ticks_remaining
        actors = sorted(
            (actor for actor in state.players.values() if actor.alive),
            key=lambda actor: (actor.seat, actor.player_id),
        )
        for actor in actors:
            actor.previous_x = actor.x
            actor.previous_y = actor.y
            self._advance_player(actor)
        if state.current_map == MAP_PULSE_FACTORY:
            self._apply_factory_pulse(state, actors)
        maximum_component_speed = max(
            (
                max(abs(actor.velocity_x), abs(actor.velocity_y))
                for actor in actors
            ),
            default=0,
        )
        substeps = _clamp(
            math.ceil(maximum_component_speed / 120),
            1,
            MAX_SIMULATION_SUBSTEPS,
        )
        for substep in range(substeps):
            for actor in actors:
                actor.x += (
                    actor.velocity_x * (substep + 1) // substeps
                    - actor.velocity_x * substep // substeps
                )
                actor.y += (
                    actor.velocity_y * (substep + 1) // substeps
                    - actor.velocity_y * substep // substeps
                )
            self._resolve_player_collisions(state, actors)
        self._resolve_ring_outs(state, room_players)

        alive = [actor for actor in state.players.values() if actor.alive]
        if len(alive) <= 1:
            self._finish_round(state, alive[0].player_id if alive else None)
        elif state.round_ticks_remaining <= 0:
            self._finish_round(state, self._timeout_winner(alive))

    def _advance_player(self, actor: PixelPushPlayerState) -> None:
        if actor.dash_cooldown_ticks > 0:
            actor.dash_cooldown_ticks -= 1
        if actor.balance_recovery_ticks > 0:
            actor.balance_recovery_ticks -= 1
        elif actor.balance > 0 and actor.dash_ticks == 0:
            actor.balance -= 1
            actor.balance_recovery_ticks = BALANCE_RECOVERY_INTERVAL_TICKS

        direction_x, direction_y = _input_direction(actor.input_mask)
        bracing = bool(actor.input_mask & INPUT_BRACE)
        if direction_x or direction_y:
            actor.facing_x, actor.facing_y = direction_x, direction_y
        if (
            actor.dash_requested
            and actor.dash_cooldown_ticks == 0
            and not bracing
        ):
            dash_x = direction_x or actor.facing_x
            dash_y = direction_y or actor.facing_y
            dash_x, dash_y = _normalized_direction(dash_x, dash_y)
            actor.dash_direction_x = dash_x
            actor.dash_direction_y = dash_y
            actor.dash_ticks = DASH_TICKS
            actor.dash_cooldown_ticks = DASH_COOLDOWN_TICKS
            actor.dash_hit_ids.clear()
        actor.dash_requested = False

        if actor.dash_ticks > 0:
            actor.velocity_x = actor.dash_direction_x * DASH_SPEED // 1_000
            actor.velocity_y = actor.dash_direction_y * DASH_SPEED // 1_000
            actor.dash_ticks -= 1
            if actor.dash_ticks == 0:
                actor.dash_hit_ids.clear()
        elif direction_x or direction_y:
            max_speed = BRACE_MAX_SPEED if bracing else MOVE_MAX_SPEED
            actor.velocity_x = _approach(
                actor.velocity_x,
                direction_x * max_speed // 1_000,
                MOVE_ACCELERATION,
            )
            actor.velocity_y = _approach(
                actor.velocity_y,
                direction_y * max_speed // 1_000,
                MOVE_ACCELERATION,
            )
        else:
            friction = BRACE_FRICTION if bracing else MOVE_FRICTION
            actor.velocity_x = _approach_zero(actor.velocity_x, friction)
            actor.velocity_y = _approach_zero(actor.velocity_y, friction)

    def _resolve_player_collisions(
        self,
        state: PixelPushState,
        actors: list[PixelPushPlayerState],
    ) -> None:
        minimum_distance = PLAYER_RADIUS * 2
        for _ in range(2):
            for index, first in enumerate(actors):
                if not first.alive:
                    continue
                for second in actors[index + 1 :]:
                    if not second.alive:
                        continue
                    dx = second.x - first.x
                    dy = second.y - first.y
                    distance_squared = dx * dx + dy * dy
                    if distance_squared >= minimum_distance**2:
                        continue
                    if distance_squared == 0:
                        dx = 1 if first.player_id < second.player_id else -1
                        dy = 0
                        distance = 1
                    else:
                        distance = max(1, math.isqrt(distance_squared))
                    normal_x = dx * 1_000 // distance
                    normal_y = dy * 1_000 // distance
                    overlap = minimum_distance - distance
                    correction = overlap // 2 + 1
                    first.x -= normal_x * correction // 1_000
                    first.y -= normal_y * correction // 1_000
                    second.x += normal_x * correction // 1_000
                    second.y += normal_y * correction // 1_000
                    self._resolve_dash_hit(
                        state,
                        first,
                        second,
                        normal_x,
                        normal_y,
                    )
                    self._resolve_dash_hit(
                        state,
                        second,
                        first,
                        -normal_x,
                        -normal_y,
                    )
                    if first.dash_ticks == 0 and second.dash_ticks == 0:
                        relative = (
                            (first.velocity_x - second.velocity_x) * normal_x
                            + (first.velocity_y - second.velocity_y) * normal_y
                        ) // 1_000
                        if relative > 0:
                            exchange = min(30, relative // 3)
                            first.velocity_x -= normal_x * exchange // 1_000
                            first.velocity_y -= normal_y * exchange // 1_000
                            second.velocity_x += normal_x * exchange // 1_000
                            second.velocity_y += normal_y * exchange // 1_000

    def _resolve_dash_hit(
        self,
        state: PixelPushState,
        attacker: PixelPushPlayerState,
        target: PixelPushPlayerState,
        normal_x: int,
        normal_y: int,
    ) -> None:
        if attacker.dash_ticks <= 0 or target.player_id in attacker.dash_hit_ids:
            return
        approach = (
            attacker.dash_direction_x * normal_x
            + attacker.dash_direction_y * normal_y
        ) // 1_000
        if approach < 350:
            return
        attacker.dash_hit_ids.add(target.player_id)

        target_bracing = bool(target.input_mask & INPUT_BRACE)
        target_to_attacker_x = -normal_x
        target_to_attacker_y = -normal_y
        frontal = (
            target.facing_x * target_to_attacker_x
            + target.facing_y * target_to_attacker_y
        ) // 1_000 >= 250
        balance_gain = DASH_BALANCE_GAIN
        if not frontal:
            balance_gain += SIDE_HIT_BONUS
        target.balance = _clamp(
            target.balance + balance_gain,
            0,
            BALANCE_MAX,
        )
        target.balance_recovery_ticks = BALANCE_RECOVERY_DELAY_TICKS
        knockback = DASH_BASE_KNOCKBACK + target.balance * DASH_BALANCE_KNOCKBACK
        if target_bracing:
            factor = BRACE_FRONT_FACTOR if frontal else BRACE_REAR_FACTOR
            knockback = knockback * factor // 100
        target.velocity_x += normal_x * knockback // 1_000
        target.velocity_y += normal_y * knockback // 1_000
        target.velocity_x = _clamp(
            target.velocity_x,
            -MAX_KNOCKBACK_SPEED,
            MAX_KNOCKBACK_SPEED,
        )
        target.velocity_y = _clamp(
            target.velocity_y,
            -MAX_KNOCKBACK_SPEED,
            MAX_KNOCKBACK_SPEED,
        )
        target.last_hit_by = attacker.player_id
        target.last_hit_tick = state.tick
        if target_bracing and frontal:
            attacker.velocity_x -= normal_x * BRACE_RECOIL // 1_000
            attacker.velocity_y -= normal_y * BRACE_RECOIL // 1_000
            attacker.dash_ticks = 0
            attacker.balance = _clamp(attacker.balance + 4, 0, BALANCE_MAX)
            self._add_event(
                state,
                "braced",
                actor_id=target.player_id,
                target_id=attacker.player_id,
            )
        else:
            self._add_event(
                state,
                "hit",
                actor_id=attacker.player_id,
                target_id=target.player_id,
                value=balance_gain,
            )

    def _apply_factory_pulse(
        self,
        state: PixelPushState,
        actors: list[PixelPushPlayerState],
    ) -> None:
        cycle_ticks = 8 * TICK_RATE
        cycle = state.tick // cycle_ticks
        cycle_tick = state.tick % cycle_ticks
        active_start = 2 * TICK_RATE
        travel_ticks = 3 * TICK_RATE
        if not active_start <= cycle_tick < active_start + travel_ticks:
            return
        progress = (cycle_tick - active_start) * 1_000 // travel_ticks
        pulse_x = 1_050 + progress * 7_900 // 1_000
        for actor in actors:
            if actor.pulse_cycle == cycle or abs(actor.x - pulse_x) > 210:
                continue
            actor.pulse_cycle = cycle
            actor.velocity_x += 72
            actor.balance = _clamp(actor.balance + 3, 0, BALANCE_MAX)
            actor.balance_recovery_ticks = BALANCE_RECOVERY_DELAY_TICKS
            self._add_event(
                state,
                "pulse",
                target_id=actor.player_id,
                value=cycle,
            )

    def _update_connections(
        self,
        state: PixelPushState,
        room_players: dict[str, ArcadePlayer],
    ) -> None:
        for player_id, actor in state.players.items():
            player = room_players.get(player_id)
            if player is None or not player.connected:
                actor.input_mask = 0
                actor.dash_requested = False
                if actor.alive:
                    actor.disconnected_ticks += 1
                    if (
                        state.stage == "active"
                        and actor.disconnected_ticks >= DISCONNECT_KO_TICKS
                    ):
                        self._eliminate(state, actor, "disconnect")
            else:
                actor.disconnected_ticks = 0

    def _resolve_ring_outs(
        self,
        state: PixelPushState,
        room_players: dict[str, ArcadePlayer],
    ) -> None:
        del room_players
        for actor in state.players.values():
            if not actor.alive:
                continue
            if _inside_arena(state, actor.x, actor.y):
                actor.outside_ticks = 0
                continue
            actor.outside_ticks += 1
            if actor.outside_ticks >= RING_OUT_GRACE_TICKS:
                self._eliminate(state, actor, "ring_out")

    def _eliminate(
        self,
        state: PixelPushState,
        actor: PixelPushPlayerState,
        reason: str,
    ) -> None:
        if not actor.alive:
            return
        actor.alive = False
        actor.input_mask = 0
        actor.dash_ticks = 0
        if reason == "ring_out":
            actor.ring_outs += 1
        credited_to = None
        if (
            reason == "ring_out"
            and actor.last_hit_by is not None
            and state.tick - actor.last_hit_tick <= 3 * TICK_RATE
            and actor.last_hit_by in state.players
        ):
            credited_to = actor.last_hit_by
            state.players[credited_to].eliminations += 1
        self._add_event(
            state,
            reason,
            actor_id=credited_to,
            target_id=actor.player_id,
        )

    def _timeout_winner(
        self,
        alive: list[PixelPushPlayerState],
    ) -> str | None:
        ordered = sorted(
            alive,
            key=lambda actor: (
                actor.balance,
                _distance_from_center_squared(actor),
                actor.player_id,
            ),
        )
        if len(ordered) < 2:
            return ordered[0].player_id if ordered else None
        first, second = ordered[:2]
        if (
            first.balance == second.balance
            and _distance_from_center_squared(first)
            == _distance_from_center_squared(second)
        ):
            return None
        return first.player_id

    def _finish_round(
        self,
        state: PixelPushState,
        winner_id: str | None,
    ) -> None:
        if state.stage != "active":
            return
        state.stage = "round_result"
        state.stage_ticks_remaining = ROUND_RESULT_TICKS
        state.round_winner_id = winner_id
        if winner_id is not None:
            state.round_wins[winner_id] = state.round_wins.get(winner_id, 0) + 1
            if state.round_wins[winner_id] >= ROUNDS_TO_WIN:
                state.match_winner_id = winner_id
        elif state.round_number >= MAX_ROUNDS:
            leaders = sorted(
                state.round_wins,
                key=lambda player_id: (
                    state.round_wins[player_id],
                    state.players[player_id].eliminations,
                    player_id,
                ),
                reverse=True,
            )
            if leaders:
                state.match_winner_id = leaders[0]
        self._add_event(
            state,
            "round_won" if winner_id is not None else "round_draw",
            actor_id=winner_id,
            value=state.round_number,
        )

    def _reset_round(
        self,
        state: PixelPushState,
        room_players: list[ArcadePlayer],
        *,
        first_round: bool,
    ) -> None:
        del first_round
        active_players = sorted(room_players, key=lambda player: player.seat)
        positions = _spawn_positions(len(active_players))
        for player, (x, y, facing_x, facing_y) in zip(
            active_players,
            positions,
            strict=True,
        ):
            actor = state.players[player.id]
            actor.seat = player.seat
            actor.x = actor.previous_x = x
            actor.y = actor.previous_y = y
            actor.velocity_x = actor.velocity_y = 0
            actor.facing_x = facing_x
            actor.facing_y = facing_y
            actor.input_mask = 0
            actor.dash_requested = False
            actor.dash_ticks = 0
            actor.dash_cooldown_ticks = 0
            actor.dash_hit_ids.clear()
            actor.balance = 0
            actor.balance_recovery_ticks = 0
            actor.alive = True
            actor.outside_ticks = 0
            if player.connected:
                actor.disconnected_ticks = 0
            actor.last_hit_by = None
            actor.last_hit_tick = -10_000
            actor.pulse_cycle = -1
        state.stage = "countdown"
        state.stage_ticks_remaining = COUNTDOWN_TICKS
        state.round_ticks_remaining = ACTIVE_ROUND_TICKS
        state.round_winner_id = None
        self._add_event(state, "countdown", value=state.round_number)

    def manual_forfeit(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> bool:
        state: PixelPushState = room.state
        actor = state.players.get(player.id)
        if actor is None:
            return False
        self._eliminate(state, actor, "forfeit")
        remaining_ids = [
            candidate.id
            for candidate in room.players
            if candidate.id != player.id and not candidate.left_room
        ]
        if len(remaining_ids) == 1:
            winner_id = remaining_ids[0]
            state.match_winner_id = winner_id
            state.round_wins[winner_id] = max(
                ROUNDS_TO_WIN,
                state.round_wins.get(winner_id, 0),
            )
            room.finish(
                "last_standing",
                [winner_id],
                f"{player.name} 退出对局，另一名玩家获胜",
            )
        elif state.stage == "active":
            alive = [candidate for candidate in state.players.values() if candidate.alive]
            if len(alive) <= 1:
                self._finish_round(
                    state,
                    alive[0].player_id if alive else None,
                )
        return True

    def disconnect_timeout(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> bool:
        return self.manual_forfeit(room, player)

    def repair_restored_room(self, room: ArcadeRoom) -> None:
        if room.phase != "playing" or not isinstance(room.state, PixelPushState):
            return
        state: PixelPushState = room.state
        state.frozen = True
        for actor in state.players.values():
            actor.input_mask = 0
            actor.dash_requested = False
            actor.last_input_sequence = max(-1, actor.last_input_sequence)

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: PixelPushState = room.state
        player_names = {player.id: player.name for player in room.players}
        return {
            "tick": state.tick,
            "tickRate": TICK_RATE,
            "stage": state.stage,
            "stageTicksRemaining": state.stage_ticks_remaining,
            "roundTicksRemaining": state.round_ticks_remaining,
            "roundNumber": state.round_number,
            "roundsToWin": ROUNDS_TO_WIN,
            "currentMap": state.current_map,
            "mapSequence": state.map_sequence,
            "shrinkProgress": _shrink_progress(state),
            "roundWinnerId": state.round_winner_id,
            "matchWinnerId": state.match_winner_id,
            "frozen": state.frozen,
            "world": {
                "width": WORLD_WIDTH,
                "height": WORLD_HEIGHT,
                "playerRadius": PLAYER_RADIUS,
            },
            "players": [
                self._player_view(state, actor, player_names.get(actor.player_id, "玩家"))
                for actor in sorted(
                    state.players.values(),
                    key=lambda item: (item.seat, item.player_id),
                )
            ],
            "roundWins": dict(state.round_wins),
            "events": [
                {
                    "id": event.event_id,
                    "tick": event.tick,
                    "kind": event.kind,
                    "actorId": event.actor_id,
                    "targetId": event.target_id,
                    "value": event.value,
                }
                for event in state.events[-16:]
            ],
            "selfInputSequence": state.players.get(
                viewer.id,
                PixelPushPlayerState(viewer.id, viewer.seat),
            ).last_input_sequence,
        }

    def realtime_frame(
        self,
        room: ArcadeRoom,
        viewer: ArcadePlayer | None = None,
    ) -> dict[str, Any]:
        del viewer
        state: PixelPushState = room.state
        return {
            "roomCode": room.code,
            "revision": room.revision,
            "tick": state.tick,
            "stage": state.stage,
            "stageTicksRemaining": state.stage_ticks_remaining,
            "roundTicksRemaining": state.round_ticks_remaining,
            "roundNumber": state.round_number,
            "currentMap": state.current_map,
            "shrinkProgress": _shrink_progress(state),
            "roundWinnerId": state.round_winner_id,
            "matchWinnerId": state.match_winner_id,
            "roundWins": dict(state.round_wins),
            "frozen": state.frozen,
            "players": [
                {
                    "id": actor.player_id,
                    "x": actor.x,
                    "y": actor.y,
                    "vx": actor.velocity_x,
                    "vy": actor.velocity_y,
                    "facingX": actor.facing_x,
                    "facingY": actor.facing_y,
                    "balance": actor.balance,
                    "alive": actor.alive,
                    "dashing": actor.dash_ticks > 0,
                    "bracing": bool(actor.input_mask & INPUT_BRACE),
                    "dashCooldownTicks": actor.dash_cooldown_ticks,
                    "disconnectTicks": actor.disconnected_ticks,
                    "lastInputSequence": actor.last_input_sequence,
                }
                for actor in sorted(
                    state.players.values(),
                    key=lambda item: (item.seat, item.player_id),
                )
            ],
            "events": [
                {
                    "id": event.event_id,
                    "tick": event.tick,
                    "kind": event.kind,
                    "actorId": event.actor_id,
                    "targetId": event.target_id,
                    "value": event.value,
                }
                for event in state.events[-8:]
            ],
        }

    @staticmethod
    def _player_view(
        state: PixelPushState,
        actor: PixelPushPlayerState,
        name: str,
    ) -> dict[str, Any]:
        return {
            "id": actor.player_id,
            "name": name,
            "seat": actor.seat,
            "color": PLAYER_COLORS[actor.seat % len(PLAYER_COLORS)],
            "x": actor.x,
            "y": actor.y,
            "vx": actor.velocity_x,
            "vy": actor.velocity_y,
            "facingX": actor.facing_x,
            "facingY": actor.facing_y,
            "balance": actor.balance,
            "alive": actor.alive,
            "dashing": actor.dash_ticks > 0,
            "bracing": bool(actor.input_mask & INPUT_BRACE),
            "dashCooldownTicks": actor.dash_cooldown_ticks,
            "disconnectTicks": actor.disconnected_ticks,
            "roundWins": state.round_wins.get(actor.player_id, 0),
            "eliminations": actor.eliminations,
            "ringOuts": actor.ring_outs,
        }

    def player_result(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> tuple[str, str, bool]:
        return (
            f"seat_{player.seat + 1}",
            "contender",
            player.id in room.winner_player_ids,
        )

    def record_state(self, room: ArcadeRoom) -> dict[str, Any]:
        state: PixelPushState = room.state
        return {
            "mapSequence": state.map_sequence,
            "roundNumber": state.round_number,
            "roundWins": state.round_wins,
            "players": {
                player_id: {
                    "eliminations": actor.eliminations,
                    "ringOuts": actor.ring_outs,
                    "balance": actor.balance,
                }
                for player_id, actor in state.players.items()
            },
        }

    @staticmethod
    def _add_event(
        state: PixelPushState,
        kind: str,
        *,
        actor_id: str | None = None,
        target_id: str | None = None,
        value: int | None = None,
    ) -> None:
        state.events.append(
            PixelPushEvent(
                event_id=state.next_event_id,
                tick=state.tick,
                kind=kind,
                actor_id=actor_id,
                target_id=target_id,
                value=value,
            )
        )
        state.next_event_id += 1
        state.events = state.events[-24:]
