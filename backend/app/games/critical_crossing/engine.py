from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Literal

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


BOARD_WIDTH = 10_000
BOARD_HEIGHT = 6_500
TICKS_PER_SECOND = 60

PLAYER_RADIUS = 105
PLAYER_HIT_RADIUS = 32
PLAYER_SPEED = 160

PULSE_INTERVAL_TICKS = TICKS_PER_SECOND
PULSE_FRONT_HIT_RADIUS = 72

BOUNDARY_ZONE_X = 900
BOUNDARY_ZONE_Y = 585
BOUNDARY_PRESSURE_DECAY = 1
BOUNDARY_WALL_SPEED = 100
BOUNDARY_WALL_DEPTH = 1_000
BOUNDARY_SIDES = ("top", "right", "bottom", "left")

MIN_SUCCESS_SLACK_SECONDS = 0.3
UINT32_MASK = 0xFFFFFFFF
GATE_LANE_SALT = 0xC8013EA4
GATE_OFFSET_SALT = 0xAD90777D
AXIS_Y_SALT = 0x7E95761E

UP = 1
DOWN = 2
LEFT = 4
RIGHT = 8
VALID_INPUT_MASK = UP | DOWN | LEFT | RIGHT

BoundarySide = Literal["top", "right", "bottom", "left"]
CollisionKind = Literal["pulse", "boundary"]
Axis = Literal["x", "y"]


@dataclass(frozen=True)
class DifficultyConfig:
    label: str
    duration_seconds: int
    pulse_warning_ticks: int
    pulse_front_speed: int
    safe_gate_radius: int
    boundary_pressure_limit: int

    def __post_init__(self) -> None:
        if min(
            self.duration_seconds,
            self.pulse_warning_ticks,
            self.pulse_front_speed,
            self.safe_gate_radius,
            self.boundary_pressure_limit,
        ) <= 0:
            raise ValueError("Critical Crossing tuning values must be positive")

    @property
    def pulse_count(self) -> int:
        return self.duration_seconds


DIFFICULTIES: dict[str, DifficultyConfig] = {
    "5s": DifficultyConfig(
        label="校准",
        duration_seconds=5,
        pulse_warning_ticks=28,
        pulse_front_speed=180,
        safe_gate_radius=1_050,
        boundary_pressure_limit=36,
    ),
    "8s": DifficultyConfig(
        label="过载",
        duration_seconds=8,
        pulse_warning_ticks=23,
        pulse_front_speed=175,
        safe_gate_radius=920,
        boundary_pressure_limit=30,
    ),
    "10s": DifficultyConfig(
        label="临界",
        duration_seconds=10,
        pulse_warning_ticks=18,
        pulse_front_speed=170,
        safe_gate_radius=820,
        boundary_pressure_limit=26,
    ),
}
DEFAULT_DIFFICULTY = "5s"


@dataclass(frozen=True)
class PulseFront:
    side: BoundarySide
    position: int
    gate: int


@dataclass(frozen=True)
class PulsePlanEntry:
    x_gate: int
    y_gate: int


@dataclass(frozen=True)
class SimulationResult:
    crossed: bool
    ticks: int
    collision_tick: int | None
    collision_kind: CollisionKind | None
    player_x: int
    player_y: int
    max_boundary_pressure: int


@dataclass
class CriticalCrossingState:
    difficulty: str = DEFAULT_DIFFICULTY
    duration_seconds: int = 5
    seed: int = 0
    started_monotonic: float = 0.0
    elapsed_ms: int = 0
    crossed: bool | None = None
    collision_tick: int | None = None
    collision_kind: CollisionKind | None = None
    input_count: int = 0


def _mix_u32(value: int) -> int:
    """Avalanche a 32-bit value identically in Python and JavaScript."""

    value &= UINT32_MASK
    value ^= value >> 16
    value = (value * 0x7FEB352D) & UINT32_MASK
    value ^= value >> 15
    value = (value * 0x846CA68B) & UINT32_MASK
    value ^= value >> 16
    return value & UINT32_MASK


def _random_word(seed: int, pulse_index: int, salt: int) -> int:
    index_key = ((pulse_index + 1) * 0x9E3779B9) & UINT32_MASK
    return _mix_u32(seed ^ index_key ^ salt)


def pulse_safe_gate(seed: int, pulse_index: int, axis: Axis) -> int:
    """Return a deterministic opening center along one board axis."""

    axis_salt = 0 if axis == "x" else AXIS_Y_SALT
    ranges = (
        ((3_000, 3_500), (6_500, 7_000))
        if axis == "x"
        else ((2_050, 2_450), (4_050, 4_450))
    )
    lane = _random_word(
        seed,
        pulse_index,
        GATE_LANE_SALT ^ axis_salt,
    ) % len(ranges)
    minimum, maximum = ranges[lane]
    offset = _random_word(
        seed,
        pulse_index,
        GATE_OFFSET_SALT ^ axis_salt,
    ) % (maximum - minimum + 1)
    return minimum + offset


def build_pulse_plan(
    seed: int,
    config: DifficultyConfig,
) -> tuple[PulsePlanEntry, ...]:
    return tuple(
        PulsePlanEntry(
            x_gate=pulse_safe_gate(seed, pulse_index, "x"),
            y_gate=pulse_safe_gate(seed, pulse_index, "y"),
        )
        for pulse_index in range(config.pulse_count)
    )


def pulse_fronts(
    plan: tuple[PulsePlanEntry, ...],
    tick: int,
    config: DifficultyConfig,
) -> list[PulseFront]:
    fronts: list[PulseFront] = []
    active_count = min(len(plan), tick // PULSE_INTERVAL_TICKS + 1)
    for pulse_index, pulse in enumerate(plan[:active_count]):
        elapsed = tick - (
            pulse_index * PULSE_INTERVAL_TICKS
            + config.pulse_warning_ticks
        )
        if elapsed < 0:
            continue
        distance = (elapsed + 1) * config.pulse_front_speed
        for side in BOUNDARY_SIDES:
            vertical_edge = side in {"left", "right"}
            gate = pulse.y_gate if vertical_edge else pulse.x_gate
            if side == "left":
                position = BOUNDARY_ZONE_X + distance
            elif side == "right":
                position = BOARD_WIDTH - BOUNDARY_ZONE_X - distance
            elif side == "top":
                position = BOUNDARY_ZONE_Y + distance
            else:
                position = BOARD_HEIGHT - BOUNDARY_ZONE_Y - distance
            span = BOARD_WIDTH if vertical_edge else BOARD_HEIGHT
            if -500 <= position <= span + 500:
                fronts.append(PulseFront(side, position, gate))
    return fronts


def pulse_collision(
    plan: tuple[PulsePlanEntry, ...],
    tick: int,
    player_x: int,
    player_y: int,
    config: DifficultyConfig,
) -> bool:
    for front in pulse_fronts(plan, tick, config):
        vertical_edge = front.side in {"left", "right"}
        front_distance = abs(
            (player_x if vertical_edge else player_y) - front.position
        )
        gate_distance = abs(
            (player_y if vertical_edge else player_x) - front.gate
        )
        if (
            front_distance <= PLAYER_HIT_RADIUS + PULSE_FRONT_HIT_RADIUS
            and gate_distance > config.safe_gate_radius
        ):
            return True
    return False


def boundary_zone_sides(
    player_x: int,
    player_y: int,
) -> tuple[BoundarySide, ...]:
    sides: list[BoundarySide] = []
    if player_y <= BOUNDARY_ZONE_Y:
        sides.append("top")
    if player_x >= BOARD_WIDTH - BOUNDARY_ZONE_X:
        sides.append("right")
    if player_y >= BOARD_HEIGHT - BOUNDARY_ZONE_Y:
        sides.append("bottom")
    if player_x <= BOUNDARY_ZONE_X:
        sides.append("left")
    return tuple(sides)


def update_boundary_pressure(
    pressure: dict[BoundarySide, int],
    player_x: int,
    player_y: int,
    config: DifficultyConfig,
) -> dict[BoundarySide, int]:
    active_sides = set(boundary_zone_sides(player_x, player_y))
    pressure_max = (
        config.boundary_pressure_limit
        + BOUNDARY_WALL_DEPTH // BOUNDARY_WALL_SPEED
    )
    return {
        side: (
            min(pressure_max, pressure[side] + 1)
            if side in active_sides
            else max(0, pressure[side] - BOUNDARY_PRESSURE_DECAY)
        )
        for side in BOUNDARY_SIDES
    }


def boundary_wall_depth(pressure: int, config: DifficultyConfig) -> int:
    if pressure <= config.boundary_pressure_limit:
        return 0
    return min(
        BOUNDARY_WALL_DEPTH,
        (pressure - config.boundary_pressure_limit) * BOUNDARY_WALL_SPEED,
    )


def boundary_collision(
    player_x: int,
    player_y: int,
    pressure: dict[BoundarySide, int],
    config: DifficultyConfig,
) -> bool:
    for side in BOUNDARY_SIDES:
        depth = boundary_wall_depth(pressure[side], config)
        if depth == 0:
            continue
        if side == "top" and player_y - PLAYER_HIT_RADIUS <= depth:
            return True
        if (
            side == "right"
            and player_x + PLAYER_HIT_RADIUS >= BOARD_WIDTH - depth
        ):
            return True
        if (
            side == "bottom"
            and player_y + PLAYER_HIT_RADIUS >= BOARD_HEIGHT - depth
        ):
            return True
        if side == "left" and player_x - PLAYER_HIT_RADIUS <= depth:
            return True
    return False


def duration_ticks(duration_seconds: int) -> int:
    return duration_seconds * TICKS_PER_SECOND


def simulate_run(
    seed: int,
    inputs: list[int],
    config: DifficultyConfig,
) -> SimulationResult:
    target_ticks = duration_ticks(config.duration_seconds)
    plan = build_pulse_plan(seed, config)
    player_x = BOARD_WIDTH // 2
    player_y = BOARD_HEIGHT // 2
    boundary_pressure: dict[BoundarySide, int] = {
        side: 0 for side in BOUNDARY_SIDES
    }
    max_boundary_pressure = 0

    for tick, input_mask in enumerate(inputs[:target_ticks]):
        horizontal = int(bool(input_mask & RIGHT)) - int(bool(input_mask & LEFT))
        vertical = int(bool(input_mask & DOWN)) - int(bool(input_mask & UP))
        step = 113 if horizontal and vertical else PLAYER_SPEED
        player_x += horizontal * step
        player_y += vertical * step
        player_x = min(
            BOARD_WIDTH - PLAYER_RADIUS,
            max(PLAYER_RADIUS, player_x),
        )
        player_y = min(
            BOARD_HEIGHT - PLAYER_RADIUS,
            max(PLAYER_RADIUS, player_y),
        )

        boundary_pressure = update_boundary_pressure(
            boundary_pressure,
            player_x,
            player_y,
            config,
        )
        max_boundary_pressure = max(
            max_boundary_pressure,
            max(boundary_pressure.values()),
        )

        collision_kind: CollisionKind | None = None
        if tick >= config.pulse_warning_ticks and boundary_collision(
            player_x,
            player_y,
            boundary_pressure,
            config,
        ):
            collision_kind = "boundary"
        elif tick >= config.pulse_warning_ticks and pulse_collision(
            plan,
            tick,
            player_x,
            player_y,
            config,
        ):
            collision_kind = "pulse"

        if collision_kind is not None:
            return SimulationResult(
                crossed=False,
                ticks=tick + 1,
                collision_tick=tick,
                collision_kind=collision_kind,
                player_x=player_x,
                player_y=player_y,
                max_boundary_pressure=max_boundary_pressure,
            )

    return SimulationResult(
        crossed=len(inputs) >= target_ticks,
        ticks=min(len(inputs), target_ticks),
        collision_tick=None,
        collision_kind=None,
        player_x=player_x,
        player_y=player_y,
        max_boundary_pressure=max_boundary_pressure,
    )


def build_safe_route(seed: int, config: DifficultyConfig) -> list[int]:
    """Build a reference route that keeps every generated field playable."""

    target_ticks = duration_ticks(config.duration_seconds)
    plan = build_pulse_plan(seed, config)
    player_x = BOARD_WIDTH // 2
    player_y = BOARD_HEIGHT // 2
    inputs: list[int] = []

    for tick in range(target_ticks):
        pulse_index = min(tick // PULSE_INTERVAL_TICKS, len(plan) - 1)
        pulse = plan[pulse_index]
        target_x = pulse.x_gate
        target_y = pulse.y_gate

        horizontal = 0
        vertical = 0
        if player_x < target_x - PLAYER_SPEED // 2:
            horizontal = RIGHT
        elif player_x > target_x + PLAYER_SPEED // 2:
            horizontal = LEFT
        if player_y < target_y - PLAYER_SPEED // 2:
            vertical = DOWN
        elif player_y > target_y + PLAYER_SPEED // 2:
            vertical = UP

        input_mask = horizontal | vertical
        inputs.append(input_mask)
        step = 113 if horizontal and vertical else PLAYER_SPEED
        player_x += step * (
            int(bool(horizontal & RIGHT)) - int(bool(horizontal & LEFT))
        )
        player_y += step * (
            int(bool(vertical & DOWN)) - int(bool(vertical & UP))
        )
    return inputs


class CriticalCrossingEngine:
    key = "critical_crossing"
    name = "临界穿越"
    min_players = 1
    max_players = 1
    public_rooms = False

    def __init__(
        self,
        clock: Callable[[], float] | None = None,
        rng: random.Random | random.SystemRandom | None = None,
    ) -> None:
        self.clock = clock or time.monotonic
        self.rng = rng or random.SystemRandom()

    def initial_state(self) -> CriticalCrossingState:
        return CriticalCrossingState()

    def room_options(self, options: dict[str, Any]) -> dict[str, Any]:
        difficulty = options.get("difficulty", DEFAULT_DIFFICULTY)
        if not isinstance(difficulty, str) or difficulty not in DIFFICULTIES:
            raise GameRuleError("临界穿越难度不正确")
        return {"difficulty": difficulty}

    def start(self, room: ArcadeRoom) -> None:
        difficulty = room.options.get("difficulty", DEFAULT_DIFFICULTY)
        if not isinstance(difficulty, str) or difficulty not in DIFFICULTIES:
            raise GameRuleError("临界穿越难度不正确")
        config = DIFFICULTIES[difficulty]
        previous_seed = (
            room.state.seed
            if isinstance(room.state, CriticalCrossingState)
            and room.state.seed != 0
            else None
        )
        room.state = CriticalCrossingState(
            difficulty=difficulty,
            duration_seconds=config.duration_seconds,
            seed=self._verified_seed(config, previous_seed),
            started_monotonic=self.clock(),
        )
        room.phase = "playing"

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        if player.id != room.host_id:
            raise GameRuleError("只有挑战者本人可以提交穿越轨迹")
        if action != "finish":
            raise GameRuleError("不支持这个临界穿越操作")

        state: CriticalCrossingState = room.state
        config = DIFFICULTIES[state.difficulty]
        target_ticks = duration_ticks(config.duration_seconds)
        raw_inputs = payload.get("inputs")
        if not isinstance(raw_inputs, list) or not raw_inputs:
            raise GameRuleError("穿越轨迹不能为空")
        if len(raw_inputs) > target_ticks:
            raise GameRuleError("穿越轨迹超过本轮目标时间")
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            or value > VALID_INPUT_MASK
            for value in raw_inputs
        ):
            raise GameRuleError("穿越轨迹数据不正确")

        result = simulate_run(state.seed, raw_inputs, config)
        if result.collision_tick is not None and len(raw_inputs) != result.ticks:
            raise GameRuleError("碰撞后的轨迹数据不正确")
        if result.collision_tick is None and len(raw_inputs) != target_ticks:
            raise GameRuleError("挑战尚未达到目标时间")
        minimum_success_seconds = (
            state.duration_seconds - MIN_SUCCESS_SLACK_SECONDS
        )
        if (
            result.crossed
            and self.clock() - state.started_monotonic < minimum_success_seconds
        ):
            raise GameRuleError("挑战完成得太快，请按正常倒计时进行")

        state.elapsed_ms = (
            state.duration_seconds * 1_000
            if result.crossed
            else round(result.ticks * 1_000 / TICKS_PER_SECOND)
        )
        state.crossed = result.crossed
        state.collision_tick = result.collision_tick
        state.collision_kind = result.collision_kind
        state.input_count = len(raw_inputs)
        if result.crossed:
            room.finish(
                "crossed",
                [player.id],
                f"你穿过了 {state.duration_seconds} 秒临界场",
            )
        else:
            cause = (
                "边界封锁"
                if result.collision_kind == "boundary"
                else "脉冲屏障"
            )
            room.finish(
                "interrupted",
                [],
                f"穿越 {state.elapsed_ms / 1_000:.2f} 秒后触碰{cause}",
            )

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: CriticalCrossingState = room.state
        config = DIFFICULTIES[state.difficulty]
        return {
            "difficulty": state.difficulty,
            "difficultyLabel": config.label,
            "seed": state.seed,
            "durationMs": state.duration_seconds * 1_000,
            "tickRate": TICKS_PER_SECOND,
            "pulseCount": config.pulse_count,
            "collisionGraceMs": round(
                config.pulse_warning_ticks * 1_000 / TICKS_PER_SECOND
            ),
            "pulseWarningMs": round(
                config.pulse_warning_ticks * 1_000 / TICKS_PER_SECOND
            ),
            "boundaryPressureMs": round(
                config.boundary_pressure_limit * 1_000 / TICKS_PER_SECOND
            ),
            "profile": {
                "pulseWarningTicks": config.pulse_warning_ticks,
                "pulseFrontSpeed": config.pulse_front_speed,
                "safeGateRadius": config.safe_gate_radius,
                "boundaryPressureLimit": config.boundary_pressure_limit,
            },
            "elapsedMs": state.elapsed_ms,
            "crossed": state.crossed,
            "collisionTick": state.collision_tick,
            "collisionKind": state.collision_kind,
        }

    def player_result(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> tuple[str, str, bool]:
        return "navigator", "solo", player.id in room.winner_player_ids

    def record_state(self, room: ArcadeRoom) -> dict[str, Any]:
        state: CriticalCrossingState = room.state
        return {
            "difficulty": state.difficulty,
            "duration_ms": state.duration_seconds * 1_000,
            "elapsed_ms": state.elapsed_ms,
            "crossed": state.crossed,
            "collision_tick": state.collision_tick,
            "collision_kind": state.collision_kind,
            "input_count": state.input_count,
            "pulse_count": state.duration_seconds,
        }

    def _verified_seed(
        self,
        config: DifficultyConfig,
        previous_seed: int | None,
    ) -> int:
        previous_plan = (
            build_pulse_plan(previous_seed, config)
            if previous_seed is not None
            else None
        )
        for attempt in range(64):
            random_seed = self.rng.randrange(1, 2**32)
            seed = (
                (random_seed + attempt * 0x9E3779B9) & UINT32_MASK
            ) or 1
            if seed == previous_seed:
                continue
            if build_pulse_plan(seed, config) == previous_plan:
                continue
            if simulate_run(seed, build_safe_route(seed, config), config).crossed:
                return seed
        raise RuntimeError("无法生成可通关且不重复的临界穿越场")
