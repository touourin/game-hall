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

DIFFICULTIES: dict[str, dict[str, int | str]] = {
    "5s": {"label": "校准", "duration_seconds": 5},
    "8s": {"label": "过载", "duration_seconds": 8},
    "10s": {"label": "临界", "duration_seconds": 10},
}
DEFAULT_DIFFICULTY = "5s"

PLAYER_RADIUS = 105
PLAYER_HIT_RADIUS = 32
PLAYER_SPEED = 160

PULSE_INTERVAL_TICKS = TICKS_PER_SECOND
PULSE_WARNING_TICKS = 22
COLLISION_GRACE_TICKS = PULSE_WARNING_TICKS
PULSE_FRONT_SPEED = 160
PULSE_FRONT_HIT_RADIUS = 72
SAFE_GATE_RADIUS = 920

BOUNDARY_ZONE_X = 900
BOUNDARY_ZONE_Y = 585
BOUNDARY_PRESSURE_LIMIT = 30
BOUNDARY_PRESSURE_DECAY = 1
BOUNDARY_WALL_SPEED = 100
BOUNDARY_WALL_DEPTH = 1_000
BOUNDARY_PRESSURE_MAX = (
    BOUNDARY_PRESSURE_LIMIT + BOUNDARY_WALL_DEPTH // BOUNDARY_WALL_SPEED
)
BOUNDARY_SIDES = ("top", "right", "bottom", "left")

MIN_SUCCESS_SLACK_SECONDS = 0.3
SOLVABLE_SEEDS = (
    162_944_417,
    487_235_091,
    914_608_233,
    1_126_805_741,
    1_447_392_519,
    1_733_064_287,
    2_015_846_103,
    2_238_519_761,
    2_774_206_349,
    3_180_447_907,
)

UP = 1
DOWN = 2
LEFT = 4
RIGHT = 8
VALID_INPUT_MASK = UP | DOWN | LEFT | RIGHT

BoundarySide = Literal["top", "right", "bottom", "left"]
CollisionKind = Literal["pulse", "boundary"]


@dataclass(frozen=True)
class PulseFront:
    side: BoundarySide
    position: int
    gate: int


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


class Lcg:
    """Small cross-language PRNG shared with the browser simulation."""

    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF

    def next_u32(self) -> int:
        self.state = (
            1_664_525 * self.state + 1_013_904_223
        ) & 0xFFFFFFFF
        return self.state

    def integer(self, minimum: int, maximum: int) -> int:
        return minimum + self.next_u32() % (maximum - minimum + 1)


def _pulse_rng(seed: int, pulse_index: int) -> Lcg:
    return Lcg((seed ^ ((pulse_index + 1) * 2_654_435_761)) & 0xFFFFFFFF)


def pulse_safe_gate(seed: int, pulse_index: int, axis: str) -> int:
    """Return a deterministic opening center along one board axis."""

    axis_salt = 0 if axis == "x" else 2_246_822_519
    rng = Lcg(
        (_pulse_rng(seed, pulse_index).next_u32() ^ axis_salt) & 0xFFFFFFFF
    )
    if axis == "y":
        return (
            rng.integer(2_050, 2_450)
            if rng.integer(0, 1) == 0
            else rng.integer(4_050, 4_450)
        )
    return (
        rng.integer(3_000, 3_500)
        if rng.integer(0, 1) == 0
        else rng.integer(6_500, 7_000)
    )


def pulse_sides(pulse_index: int) -> tuple[BoundarySide, ...]:
    pattern = pulse_index % 3
    if pattern == 0:
        return ("left", "right")
    if pattern == 1:
        return ("top", "bottom")
    return BOUNDARY_SIDES


def pulse_fronts(seed: int, tick: int, pulse_count: int) -> list[PulseFront]:
    fronts: list[PulseFront] = []
    active_count = min(pulse_count, tick // PULSE_INTERVAL_TICKS + 1)
    for pulse_index in range(active_count):
        elapsed = tick - (
            pulse_index * PULSE_INTERVAL_TICKS + PULSE_WARNING_TICKS
        )
        if elapsed < 0:
            continue
        distance = (elapsed + 1) * PULSE_FRONT_SPEED
        for side in pulse_sides(pulse_index):
            vertical_edge = side in {"left", "right"}
            gate = pulse_safe_gate(
                seed,
                pulse_index,
                "y" if vertical_edge else "x",
            )
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
    seed: int,
    tick: int,
    player_x: int,
    player_y: int,
    pulse_count: int,
) -> bool:
    for front in pulse_fronts(seed, tick, pulse_count):
        vertical_edge = front.side in {"left", "right"}
        front_distance = abs(
            (player_x if vertical_edge else player_y) - front.position
        )
        gate_distance = abs(
            (player_y if vertical_edge else player_x) - front.gate
        )
        if (
            front_distance <= PLAYER_HIT_RADIUS + PULSE_FRONT_HIT_RADIUS
            and gate_distance > SAFE_GATE_RADIUS
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
) -> dict[BoundarySide, int]:
    active_sides = set(boundary_zone_sides(player_x, player_y))
    return {
        side: (
            min(BOUNDARY_PRESSURE_MAX, pressure[side] + 1)
            if side in active_sides
            else max(0, pressure[side] - BOUNDARY_PRESSURE_DECAY)
        )
        for side in BOUNDARY_SIDES
    }


def boundary_wall_depth(pressure: int) -> int:
    if pressure <= BOUNDARY_PRESSURE_LIMIT:
        return 0
    return min(
        BOUNDARY_WALL_DEPTH,
        (pressure - BOUNDARY_PRESSURE_LIMIT) * BOUNDARY_WALL_SPEED,
    )


def boundary_collision(
    player_x: int,
    player_y: int,
    pressure: dict[BoundarySide, int],
) -> bool:
    for side in BOUNDARY_SIDES:
        depth = boundary_wall_depth(pressure[side])
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
    duration_seconds: int,
) -> SimulationResult:
    target_ticks = duration_ticks(duration_seconds)
    pulse_count = duration_seconds
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
        )
        max_boundary_pressure = max(
            max_boundary_pressure,
            max(boundary_pressure.values()),
        )

        collision_kind: CollisionKind | None = None
        if tick >= COLLISION_GRACE_TICKS and boundary_collision(
            player_x,
            player_y,
            boundary_pressure,
        ):
            collision_kind = "boundary"
        elif tick >= COLLISION_GRACE_TICKS and pulse_collision(
            seed,
            tick,
            player_x,
            player_y,
            pulse_count,
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


def build_safe_route(seed: int, duration_seconds: int) -> list[int]:
    """Build a reference route that keeps every generated field playable."""

    target_ticks = duration_ticks(duration_seconds)
    player_x = BOARD_WIDTH // 2
    player_y = BOARD_HEIGHT // 2
    inputs: list[int] = []

    for tick in range(target_ticks):
        pulse_index = min(tick // PULSE_INTERVAL_TICKS, duration_seconds - 1)
        pattern = pulse_index % 3
        target_x = player_x
        target_y = player_y
        if pattern in {1, 2}:
            target_x = pulse_safe_gate(seed, pulse_index, "x")
        if pattern in {0, 2}:
            target_y = pulse_safe_gate(seed, pulse_index, "y")

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
        duration_seconds = int(DIFFICULTIES[difficulty]["duration_seconds"])
        room.state = CriticalCrossingState(
            difficulty=difficulty,
            duration_seconds=duration_seconds,
            seed=self._solvable_seed(duration_seconds),
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
        target_ticks = duration_ticks(state.duration_seconds)
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

        result = simulate_run(state.seed, raw_inputs, state.duration_seconds)
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
        return {
            "difficulty": state.difficulty,
            "difficultyLabel": DIFFICULTIES[state.difficulty]["label"],
            "seed": state.seed,
            "durationMs": state.duration_seconds * 1_000,
            "tickRate": TICKS_PER_SECOND,
            "pulseCount": state.duration_seconds,
            "collisionGraceMs": round(
                COLLISION_GRACE_TICKS * 1_000 / TICKS_PER_SECOND
            ),
            "pulseWarningMs": round(
                PULSE_WARNING_TICKS * 1_000 / TICKS_PER_SECOND
            ),
            "boundaryPressureMs": round(
                BOUNDARY_PRESSURE_LIMIT * 1_000 / TICKS_PER_SECOND
            ),
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

    def _solvable_seed(self, duration_seconds: int) -> int:
        seed = SOLVABLE_SEEDS[self.rng.randrange(len(SOLVABLE_SEEDS))]
        assert simulate_run(
            seed,
            build_safe_route(seed, duration_seconds),
            duration_seconds,
        ).crossed
        return seed
