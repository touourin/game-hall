from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


TICKS_PER_SECOND = 60
MAX_DURATION_SECONDS = 180
MAX_TICKS = TICKS_PER_SECOND * MAX_DURATION_SECONDS
TARGET_FLOOR = 100
WORLD_WIDTH = 10_000
VIEW_HEIGHT = 7_000
PLATFORM_START_Y = 1_500
PLATFORM_GAP = 540

PLAYER_HALF_WIDTH = 210
PLAYER_HALF_HEIGHT = 260
HORIZONTAL_ACCELERATION = 18
HORIZONTAL_FRICTION = 12
MAX_HORIZONTAL_SPEED = 95
GRAVITY = 8
MAX_FALL_SPEED = 130
SPRING_SPEED = -140
CONVEYOR_SPEED = 28

STARTING_HEALTH = 10
MAX_HEALTH = 10
SPIKE_DAMAGE = 3
CEILING_DAMAGE = 3
CEILING_DEPTH = 230
CEILING_HIT_COOLDOWN = 42
CRUMBLE_DELAY_TICKS = 28
CAMERA_BASE_SPEED = 18
CAMERA_FLOOR_STEP = 2
CAMERA_FLOOR_INTERVAL = 20
CAMERA_FOLLOW_OFFSET = 2_450
MAX_CAMERA_CATCH_UP = 90
MIN_COMPLETION_SECONDS = 12

INPUT_LEFT = 1
INPUT_RIGHT = 2
VALID_INPUT_MASK = INPUT_LEFT | INPUT_RIGHT

PlatformKind = Literal[
    "normal",
    "spikes",
    "crumble",
    "conveyor_left",
    "conveyor_right",
    "spring",
]
EndReason = Literal["completed", "fell", "health", "timeout"]


@dataclass(frozen=True)
class Platform:
    floor: int
    x: int
    y: int
    width: int
    kind: PlatformKind


@dataclass
class ShaftSimulation:
    seed: int
    tick: int
    player_x: int
    player_y: int
    velocity_x: int = 0
    velocity_y: int = 0
    camera_y: int = 0
    health: int = STARTING_HEALTH
    deepest_floor: int = 0
    grounded_floor: int | None = 0
    end_reason: EndReason | None = None
    visited_floors: set[int] = field(default_factory=lambda: {0})
    crumble_due: dict[int, int] = field(default_factory=dict)
    broken_floors: set[int] = field(default_factory=set)
    ceiling_cooldown: int = 0
    last_landed_floor: int = 0
    last_landed_kind: PlatformKind = "normal"


@dataclass(frozen=True)
class SimulationResult:
    completed: bool
    ticks: int
    deepest_floor: int
    health: int
    end_reason: EndReason | None
    player_x: int
    player_y: int


@dataclass
class DeepShaftState:
    seed: int = 0
    started_monotonic: float = 0.0
    deepest_floor: int = 0
    health: int = STARTING_HEALTH
    elapsed_ms: int = 0
    end_reason: EndReason | None = None
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


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return min(maximum, max(minimum, value))


def _approach_zero(value: int, amount: int) -> int:
    if value > 0:
        return max(0, value - amount)
    if value < 0:
        return min(0, value + amount)
    return 0


def _platform_kind(
    floor: int,
    roll: int,
    recent_platforms: list[Platform],
) -> PlatformKind:
    if floor <= 5 or floor == TARGET_FLOOR:
        return "normal"
    if roll < 11 and all(
        platform.kind != "spikes" for platform in recent_platforms[-3:]
    ):
        return "spikes"
    if roll < 21:
        return "crumble"
    if roll < 29:
        return "spring"
    if roll < 39:
        return "conveyor_left"
    if roll < 49:
        return "conveyor_right"
    return "normal"


def generate_platforms(seed: int) -> list[Platform]:
    rng = Lcg(seed ^ 0xA5B35705)
    platforms = [
        Platform(0, 3_800, PLATFORM_START_Y, 2_400, "normal")
    ]
    previous_center = WORLD_WIDTH // 2
    for floor in range(1, TARGET_FLOOR + 5):
        width = _clamp(
            2_480 - floor * 7 + rng.integer(-220, 220),
            1_520,
            2_600,
        )
        max_shift = min(1_650, 880 + floor * 6)
        center = _clamp(
            previous_center + rng.integer(-max_shift, max_shift),
            420 + width // 2,
            WORLD_WIDTH - 420 - width // 2,
        )
        platforms.append(
            Platform(
                floor=floor,
                x=center - width // 2,
                y=PLATFORM_START_Y + floor * PLATFORM_GAP,
                width=width,
                kind=_platform_kind(
                    floor,
                    rng.integer(0, 99),
                    platforms,
                ),
            )
        )
        previous_center = center
    return platforms


def create_simulation(seed: int) -> ShaftSimulation:
    start = generate_platforms(seed)[0]
    return ShaftSimulation(
        seed=seed,
        tick=0,
        player_x=start.x + start.width // 2,
        player_y=start.y - PLAYER_HALF_HEIGHT,
    )


def _landing_platform(
    simulation: ShaftSimulation,
    platforms: list[Platform],
    old_bottom: int,
    new_bottom: int,
) -> Platform | None:
    if simulation.velocity_y < 0:
        return None
    candidates = [
        platform
        for platform in platforms
        if platform.floor not in simulation.broken_floors
        and old_bottom <= platform.y <= new_bottom
        and simulation.player_x + PLAYER_HALF_WIDTH > platform.x
        and simulation.player_x - PLAYER_HALF_WIDTH < platform.x + platform.width
    ]
    return min(candidates, key=lambda platform: platform.y) if candidates else None


def advance_simulation(
    current: ShaftSimulation,
    input_mask: int,
    platforms: list[Platform] | None = None,
) -> ShaftSimulation:
    if current.end_reason is not None:
        return current
    if input_mask < 0 or input_mask > VALID_INPUT_MASK:
        raise ValueError("invalid shaft input")

    platforms = platforms or generate_platforms(current.seed)
    direction = int(bool(input_mask & INPUT_RIGHT)) - int(
        bool(input_mask & INPUT_LEFT)
    )
    if direction:
        current.velocity_x = _clamp(
            current.velocity_x + direction * HORIZONTAL_ACCELERATION,
            -MAX_HORIZONTAL_SPEED,
            MAX_HORIZONTAL_SPEED,
        )
    else:
        current.velocity_x = _approach_zero(
            current.velocity_x, HORIZONTAL_FRICTION
        )

    for floor, due_tick in list(current.crumble_due.items()):
        if current.tick >= due_tick:
            current.broken_floors.add(floor)
            current.crumble_due.pop(floor, None)
            if current.grounded_floor == floor:
                current.grounded_floor = None

    current.player_x = _clamp(
        current.player_x + current.velocity_x,
        PLAYER_HALF_WIDTH,
        WORLD_WIDTH - PLAYER_HALF_WIDTH,
    )
    current.velocity_y = min(MAX_FALL_SPEED, current.velocity_y + GRAVITY)
    old_bottom = current.player_y + PLAYER_HALF_HEIGHT
    next_y = current.player_y + current.velocity_y
    new_bottom = next_y + PLAYER_HALF_HEIGHT
    current.player_y = next_y
    landing = _landing_platform(current, platforms, old_bottom, new_bottom)

    if landing is not None:
        current.player_y = landing.y - PLAYER_HALF_HEIGHT
        current.grounded_floor = landing.floor
        current.last_landed_floor = landing.floor
        current.last_landed_kind = landing.kind
        if landing.kind == "spring":
            current.velocity_y = SPRING_SPEED
            current.grounded_floor = None
        else:
            current.velocity_y = 0
        if landing.kind == "conveyor_left":
            current.player_x = max(
                PLAYER_HALF_WIDTH, current.player_x - CONVEYOR_SPEED
            )
        elif landing.kind == "conveyor_right":
            current.player_x = min(
                WORLD_WIDTH - PLAYER_HALF_WIDTH,
                current.player_x + CONVEYOR_SPEED,
            )
        elif landing.kind == "crumble":
            current.crumble_due.setdefault(
                landing.floor, current.tick + CRUMBLE_DELAY_TICKS
            )

        if landing.floor not in current.visited_floors:
            current.visited_floors.add(landing.floor)
            current.deepest_floor = min(
                TARGET_FLOOR,
                max(current.deepest_floor, landing.floor),
            )
            if landing.kind == "spikes":
                current.health = max(0, current.health - SPIKE_DAMAGE)
                current.velocity_y = -80
                current.grounded_floor = None
            else:
                current.health = min(MAX_HEALTH, current.health + 1)
            if landing.floor >= TARGET_FLOOR:
                current.end_reason = "completed"
    else:
        current.grounded_floor = None

    scroll_speed = CAMERA_BASE_SPEED + (
        current.deepest_floor // CAMERA_FLOOR_INTERVAL
    ) * CAMERA_FLOOR_STEP
    follow_camera_y = current.player_y - CAMERA_FOLLOW_OFFSET
    current.camera_y = max(
        current.camera_y + scroll_speed,
        min(follow_camera_y, current.camera_y + MAX_CAMERA_CATCH_UP),
    )
    if current.ceiling_cooldown > 0:
        current.ceiling_cooldown -= 1
    player_top = current.player_y - PLAYER_HALF_HEIGHT
    ceiling_y = current.camera_y + CEILING_DEPTH
    if player_top <= ceiling_y and current.ceiling_cooldown == 0:
        current.health = max(0, current.health - CEILING_DAMAGE)
        current.player_y = ceiling_y + PLAYER_HALF_HEIGHT
        current.velocity_y = max(250, current.velocity_y)
        current.grounded_floor = None
        current.ceiling_cooldown = CEILING_HIT_COOLDOWN

    if current.health <= 0:
        current.end_reason = "health"
    elif current.player_y - PLAYER_HALF_HEIGHT > current.camera_y + VIEW_HEIGHT:
        current.end_reason = "fell"
    current.tick += 1
    if current.tick >= MAX_TICKS and current.end_reason is None:
        current.end_reason = "timeout"
    return current


def simulate_run(seed: int, inputs: list[int]) -> SimulationResult:
    simulation = create_simulation(seed)
    platforms = generate_platforms(seed)
    for input_mask in inputs[:MAX_TICKS]:
        advance_simulation(simulation, input_mask, platforms)
        if simulation.end_reason is not None:
            break
    return SimulationResult(
        completed=simulation.end_reason == "completed",
        ticks=simulation.tick,
        deepest_floor=simulation.deepest_floor,
        health=simulation.health,
        end_reason=simulation.end_reason,
        player_x=simulation.player_x,
        player_y=simulation.player_y,
    )


class DeepShaftEngine:
    key = "deep_shaft"
    name = "百层深井"
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

    def initial_state(self) -> DeepShaftState:
        return DeepShaftState()

    def start(self, room: ArcadeRoom) -> None:
        room.state = DeepShaftState(
            seed=self.rng.randrange(1, 2**32),
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
            raise GameRuleError("只有挑战者本人可以提交深井轨迹")
        if action != "finish":
            raise GameRuleError("不支持这个深井挑战操作")
        raw_inputs = payload.get("inputs")
        if not isinstance(raw_inputs, list) or not raw_inputs:
            raise GameRuleError("下降轨迹不能为空")
        if len(raw_inputs) > MAX_TICKS:
            raise GameRuleError("下降轨迹超过最长挑战时间")
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            or value > VALID_INPUT_MASK
            for value in raw_inputs
        ):
            raise GameRuleError("下降轨迹数据不正确")

        state: DeepShaftState = room.state
        result = simulate_run(state.seed, raw_inputs)
        if result.end_reason is None or result.ticks != len(raw_inputs):
            raise GameRuleError("深井挑战尚未结束或轨迹长度不正确")
        if (
            result.completed
            and self.clock() - state.started_monotonic < MIN_COMPLETION_SECONDS
        ):
            raise GameRuleError("百层挑战完成得太快，请按正常流程进行")
        state.deepest_floor = result.deepest_floor
        state.health = result.health
        state.elapsed_ms = round(result.ticks * 1_000 / TICKS_PER_SECOND)
        state.end_reason = result.end_reason
        state.input_count = len(raw_inputs)
        if result.completed:
            room.finish(
                "completed",
                [player.id],
                f"抵达第 {TARGET_FLOOR} 层，用时 {self._duration(state.elapsed_ms)}",
            )
        elif result.end_reason == "health":
            room.finish(
                "health",
                [],
                f"生命耗尽，本轮最深抵达第 {result.deepest_floor} 层",
            )
        elif result.end_reason == "fell":
            room.finish(
                "fell",
                [],
                f"坠入深井，本轮最深抵达第 {result.deepest_floor} 层",
            )
        else:
            room.finish(
                "timeout",
                [],
                f"3 分钟挑战结束，本轮最深抵达第 {result.deepest_floor} 层",
            )

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: DeepShaftState = room.state
        return {
            "seed": state.seed,
            "targetFloor": TARGET_FLOOR,
            "tickRate": TICKS_PER_SECOND,
            "maxHealth": MAX_HEALTH,
            "deepestFloor": state.deepest_floor,
            "health": state.health,
            "elapsedMs": state.elapsed_ms,
            "endReason": state.end_reason,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        return "explorer", "solo", player.id in room.winner_player_ids

    def player_score(self, room: ArcadeRoom, player: ArcadePlayer) -> int | None:
        state: DeepShaftState = room.state
        return state.deepest_floor if room.phase == "finished" else None

    def record_state(self, room: ArcadeRoom) -> dict[str, Any]:
        state: DeepShaftState = room.state
        return {
            "target_floor": TARGET_FLOOR,
            "deepest_floor": state.deepest_floor,
            "health": state.health,
            "elapsed_ms": state.elapsed_ms,
            "end_reason": state.end_reason,
            "input_count": state.input_count,
        }

    @staticmethod
    def _duration(elapsed_ms: int) -> str:
        minutes, seconds = divmod(elapsed_ms // 1_000, 60)
        return f"{minutes} 分 {seconds} 秒" if minutes else f"{seconds} 秒"
