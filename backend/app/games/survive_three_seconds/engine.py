from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Callable

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


BOARD_WIDTH = 10_000
BOARD_HEIGHT = 6_500
TICKS_PER_SECOND = 60
DURATION_SECONDS = 3
DURATION_TICKS = TICKS_PER_SECOND * DURATION_SECONDS

PLAYER_RADIUS = 105
PLAYER_HIT_RADIUS = 32
PLAYER_SPEED = 160
BULLET_RADIUS = 44

WAVE_TICKS = TICKS_PER_SECOND
WAVE_WARNING_TICKS = 18
COLLISION_GRACE_TICKS = WAVE_WARNING_TICKS
WAVE_BULLET_SPEED = 68
WAVE_LANE_COUNT = 18
WAVE_LANE_JITTER = 24
WAVE_FRONT_HIT_RADIUS = 72
SAFE_GAP_RADIUS = 850

EDGE_ZONE_X = 900
EDGE_ZONE_Y = 585
EDGE_PRESSURE_LIMIT = 36
EDGE_PRESSURE_DECAY = 1
EDGE_WALL_SPEED = 50
EDGE_WALL_DEPTH = 1_000
EDGE_WALL_HIT_RADIUS = 80
EDGE_PRESSURE_MAX = EDGE_PRESSURE_LIMIT + EDGE_WALL_DEPTH // EDGE_WALL_SPEED
EDGE_SIDES = ("top", "right", "bottom", "left")

MIN_SUCCESS_SECONDS = 2.7
SOLVABLE_SEEDS = (
    87_966_395,
    291_219_901,
    2_058_505_406,
    303_201_956,
    1_088_969_554,
    1_226_030_622,
    1_984_722_195,
    616_775_800,
    112_337_843,
    298_175_658,
)

UP = 1
DOWN = 2
LEFT = 4
RIGHT = 8
VALID_INPUT_MASK = UP | DOWN | LEFT | RIGHT


@dataclass(frozen=True)
class Bullet:
    x: int
    y: int
    vx: int
    vy: int
    radius: int = BULLET_RADIUS


@dataclass(frozen=True)
class SimulationResult:
    survived: bool
    ticks: int
    collision_tick: int | None
    collision_kind: str | None
    player_x: int
    player_y: int
    max_edge_pressure: int


@dataclass
class SurviveThreeSecondsState:
    seed: int = 0
    started_monotonic: float = 0.0
    elapsed_ms: int = 0
    survived: bool | None = None
    collision_tick: int | None = None
    collision_kind: str | None = None
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
        span = maximum - minimum + 1
        return minimum + self.next_u32() % span


def _wave_rng(seed: int, wave_index: int) -> Lcg:
    return Lcg((seed ^ ((wave_index + 1) * 2_654_435_761)) & 0xFFFFFFFF)


def wave_safe_gap(seed: int, wave_index: int, axis: str) -> int:
    """Return the center of the readable opening for one scripted wave."""

    axis_salt = 0 if axis == "x" else 2_246_822_519
    rng = Lcg((_wave_rng(seed, wave_index).next_u32() ^ axis_salt) & 0xFFFFFFFF)
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


def wave_sides(wave_index: int) -> tuple[str, ...]:
    if wave_index == 0:
        return ("left", "right")
    if wave_index == 1:
        return ("top", "bottom")
    return EDGE_SIDES


def spawn_bullets(seed: int, tick: int) -> list[Bullet]:
    """Generate one readable curtain when a wave's warning finishes."""

    wave_index = min(tick // WAVE_TICKS, 2)
    wave_tick = tick % WAVE_TICKS
    if wave_tick != WAVE_WARNING_TICKS:
        return []

    rng = Lcg(
        (
            seed
            ^ ((wave_index + 1) * 2_654_435_761)
            ^ ((wave_tick + 1) * 2_246_822_519)
        )
        & 0xFFFFFFFF
    )
    bullets: list[Bullet] = []
    for side in wave_sides(wave_index):
        vertical_edge = side in {"left", "right"}
        span = BOARD_HEIGHT if vertical_edge else BOARD_WIDTH
        if wave_index == 2:
            gap = wave_safe_gap(seed, 0 if vertical_edge else 1, "y" if vertical_edge else "x")
        else:
            gap = wave_safe_gap(seed, wave_index, "y" if vertical_edge else "x")
        for lane in range(WAVE_LANE_COUNT):
            position = (lane + 1) * span // (WAVE_LANE_COUNT + 1)
            position += rng.integer(-WAVE_LANE_JITTER, WAVE_LANE_JITTER)
            if abs(position - gap) <= SAFE_GAP_RADIUS:
                continue
            if side == "left":
                bullets.append(Bullet(EDGE_ZONE_X, position, WAVE_BULLET_SPEED, 0))
            elif side == "right":
                bullets.append(Bullet(BOARD_WIDTH - EDGE_ZONE_X, position, -WAVE_BULLET_SPEED, 0))
            elif side == "top":
                bullets.append(Bullet(position, EDGE_ZONE_Y, 0, WAVE_BULLET_SPEED))
            else:
                bullets.append(Bullet(position, BOARD_HEIGHT - EDGE_ZONE_Y, 0, -WAVE_BULLET_SPEED))
    return bullets


def wave_fronts(seed: int, tick: int) -> list[tuple[str, int, int]]:
    """Return active curtain fronts as ``(side, position, gap)`` tuples."""

    fronts: list[tuple[str, int, int]] = []
    for wave_index in range(3):
        elapsed = tick - (wave_index * WAVE_TICKS + WAVE_WARNING_TICKS)
        if elapsed < 0:
            continue
        distance = (elapsed + 1) * WAVE_BULLET_SPEED
        for side in wave_sides(wave_index):
            vertical_edge = side in {"left", "right"}
            gap_wave = (0 if vertical_edge else 1) if wave_index == 2 else wave_index
            gap = wave_safe_gap(seed, gap_wave, "y" if vertical_edge else "x")
            if side == "left":
                position = EDGE_ZONE_X + distance
            elif side == "right":
                position = BOARD_WIDTH - EDGE_ZONE_X - distance
            elif side == "top":
                position = EDGE_ZONE_Y + distance
            else:
                position = BOARD_HEIGHT - EDGE_ZONE_Y - distance
            if -500 <= position <= (BOARD_WIDTH if vertical_edge else BOARD_HEIGHT) + 500:
                fronts.append((side, position, gap))
    return fronts


def wave_curtain_collision(seed: int, tick: int, player_x: int, player_y: int) -> bool:
    for side, position, gap in wave_fronts(seed, tick):
        vertical_edge = side in {"left", "right"}
        front_distance = abs((player_x if vertical_edge else player_y) - position)
        gap_distance = abs((player_y if vertical_edge else player_x) - gap)
        if (
            front_distance <= PLAYER_HIT_RADIUS + WAVE_FRONT_HIT_RADIUS
            and gap_distance > SAFE_GAP_RADIUS
        ):
            return True
    return False


def edge_zone_sides(player_x: int, player_y: int) -> tuple[str, ...]:
    sides: list[str] = []
    if player_y <= EDGE_ZONE_Y:
        sides.append("top")
    if player_x >= BOARD_WIDTH - EDGE_ZONE_X:
        sides.append("right")
    if player_y >= BOARD_HEIGHT - EDGE_ZONE_Y:
        sides.append("bottom")
    if player_x <= EDGE_ZONE_X:
        sides.append("left")
    return tuple(sides)


def update_edge_pressure(
    pressure: dict[str, int], player_x: int, player_y: int
) -> dict[str, int]:
    active_sides = set(edge_zone_sides(player_x, player_y))
    return {
        side: (
            min(EDGE_PRESSURE_MAX, pressure[side] + 1)
            if side in active_sides
            else max(0, pressure[side] - EDGE_PRESSURE_DECAY)
        )
        for side in EDGE_SIDES
    }


def edge_wall_depth(pressure: int) -> int:
    if pressure <= EDGE_PRESSURE_LIMIT:
        return 0
    return min(
        EDGE_WALL_DEPTH,
        (pressure - EDGE_PRESSURE_LIMIT) * EDGE_WALL_SPEED,
    )


def edge_wall_collision(
    player_x: int, player_y: int, pressure: dict[str, int]
) -> bool:
    for side in EDGE_SIDES:
        depth = edge_wall_depth(pressure[side])
        if depth == 0:
            continue
        if side == "top" and player_y - PLAYER_HIT_RADIUS <= depth:
            return True
        if side == "right" and player_x + PLAYER_HIT_RADIUS >= BOARD_WIDTH - depth:
            return True
        if side == "bottom" and player_y + PLAYER_HIT_RADIUS >= BOARD_HEIGHT - depth:
            return True
        if side == "left" and player_x - PLAYER_HIT_RADIUS <= depth:
            return True
    return False


def simulate_run(seed: int, inputs: list[int]) -> SimulationResult:
    player_x = BOARD_WIDTH // 2
    player_y = BOARD_HEIGHT // 2
    bullets: list[Bullet] = []
    edge_pressure = {side: 0 for side in EDGE_SIDES}
    max_edge_pressure = 0

    for tick, input_mask in enumerate(inputs[:DURATION_TICKS]):
        horizontal = int(bool(input_mask & RIGHT)) - int(bool(input_mask & LEFT))
        vertical = int(bool(input_mask & DOWN)) - int(bool(input_mask & UP))
        step = 113 if horizontal and vertical else PLAYER_SPEED
        player_x += horizontal * step
        player_y += vertical * step
        player_x = min(BOARD_WIDTH - PLAYER_RADIUS, max(PLAYER_RADIUS, player_x))
        player_y = min(BOARD_HEIGHT - PLAYER_RADIUS, max(PLAYER_RADIUS, player_y))

        edge_pressure = update_edge_pressure(edge_pressure, player_x, player_y)
        max_edge_pressure = max(max_edge_pressure, max(edge_pressure.values()))

        bullets.extend(spawn_bullets(seed, tick))
        bullets = [
            Bullet(
                x=bullet.x + bullet.vx,
                y=bullet.y + bullet.vy,
                vx=bullet.vx,
                vy=bullet.vy,
                radius=bullet.radius,
            )
            for bullet in bullets
            if -500 <= bullet.x <= BOARD_WIDTH + 500
            and -500 <= bullet.y <= BOARD_HEIGHT + 500
        ]

        collision_kind: str | None = None
        if tick >= COLLISION_GRACE_TICKS and edge_wall_collision(
            player_x, player_y, edge_pressure
        ):
            collision_kind = "edge_wall"
        elif tick >= COLLISION_GRACE_TICKS and wave_curtain_collision(
            seed, tick, player_x, player_y
        ):
            collision_kind = "bullet"

        if collision_kind is not None:
            return SimulationResult(
                survived=False,
                ticks=tick + 1,
                collision_tick=tick,
                collision_kind=collision_kind,
                player_x=player_x,
                player_y=player_y,
                max_edge_pressure=max_edge_pressure,
            )

    return SimulationResult(
        survived=len(inputs) >= DURATION_TICKS,
        ticks=min(len(inputs), DURATION_TICKS),
        collision_tick=None,
        collision_kind=None,
        player_x=player_x,
        player_y=player_y,
        max_edge_pressure=max_edge_pressure,
    )


def build_safe_route(seed: int) -> list[int]:
    """Build the reference route used to verify that a seed remains playable."""

    player_x = BOARD_WIDTH // 2
    player_y = BOARD_HEIGHT // 2
    inputs: list[int] = []
    first_gap_y = wave_safe_gap(seed, 0, "y")
    second_gap_x = wave_safe_gap(seed, 1, "x")

    for tick in range(DURATION_TICKS):
        if tick < WAVE_TICKS:
            target_x, target_y = BOARD_WIDTH // 2, first_gap_y
        elif tick < WAVE_TICKS * 2:
            target_x, target_y = second_gap_x, first_gap_y
        else:
            target_x, target_y = second_gap_x, first_gap_y

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
        diagonal = bool(horizontal and vertical)
        player_x += (113 if diagonal else PLAYER_SPEED) * (
            int(bool(horizontal & RIGHT)) - int(bool(horizontal & LEFT))
        )
        player_y += (113 if diagonal else PLAYER_SPEED) * (
            int(bool(vertical & DOWN)) - int(bool(vertical & UP))
        )
    return inputs


class SurviveThreeSecondsEngine:
    key = "survive_three_seconds"
    name = "坚持三秒"
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

    def initial_state(self) -> SurviveThreeSecondsState:
        return SurviveThreeSecondsState()

    def start(self, room: ArcadeRoom) -> None:
        room.state = SurviveThreeSecondsState(
            seed=self._solvable_seed(),
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
            raise GameRuleError("只有挑战者本人可以提交躲避轨迹")
        if action != "finish":
            raise GameRuleError("不支持这个弹幕挑战操作")

        raw_inputs = payload.get("inputs")
        if not isinstance(raw_inputs, list) or not raw_inputs:
            raise GameRuleError("躲避轨迹不能为空")
        if len(raw_inputs) > DURATION_TICKS:
            raise GameRuleError("躲避轨迹超过三秒")
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            or value > VALID_INPUT_MASK
            for value in raw_inputs
        ):
            raise GameRuleError("躲避轨迹数据不正确")

        state: SurviveThreeSecondsState = room.state
        result = simulate_run(state.seed, raw_inputs)
        if result.collision_tick is not None and len(raw_inputs) != result.ticks:
            raise GameRuleError("碰撞后的轨迹数据不正确")
        if result.collision_tick is None and len(raw_inputs) != DURATION_TICKS:
            raise GameRuleError("挑战尚未完成三秒")
        if result.survived and self.clock() - state.started_monotonic < MIN_SUCCESS_SECONDS:
            raise GameRuleError("挑战完成得太快，请按正常倒计时进行")

        state.elapsed_ms = (
            DURATION_SECONDS * 1_000
            if result.survived
            else round(result.ticks * 1_000 / TICKS_PER_SECOND)
        )
        state.survived = result.survived
        state.collision_tick = result.collision_tick
        state.collision_kind = result.collision_kind
        state.input_count = len(raw_inputs)
        if result.survived:
            room.finish("survived", [player.id], "你从弹幕中坚持了整整 3 秒")
        else:
            cause = "边缘清场墙" if result.collision_kind == "edge_wall" else "弹幕"
            room.finish(
                "hit",
                [],
                f"坚持了 {state.elapsed_ms / 1_000:.2f} 秒后被{cause}命中",
            )

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: SurviveThreeSecondsState = room.state
        return {
            "seed": state.seed,
            "durationMs": DURATION_SECONDS * 1_000,
            "tickRate": TICKS_PER_SECOND,
            "collisionGraceMs": round(
                COLLISION_GRACE_TICKS * 1_000 / TICKS_PER_SECOND
            ),
            "waveWarningMs": round(WAVE_WARNING_TICKS * 1_000 / TICKS_PER_SECOND),
            "edgePressureMs": round(EDGE_PRESSURE_LIMIT * 1_000 / TICKS_PER_SECOND),
            "elapsedMs": state.elapsed_ms,
            "survived": state.survived,
            "collisionTick": state.collision_tick,
            "collisionKind": state.collision_kind,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        return "dodger", "solo", player.id in room.winner_player_ids

    def record_state(self, room: ArcadeRoom) -> dict[str, int | bool | None | str]:
        state: SurviveThreeSecondsState = room.state
        return {
            "duration_ms": DURATION_SECONDS * 1_000,
            "elapsed_ms": state.elapsed_ms,
            "survived": state.survived,
            "collision_tick": state.collision_tick,
            "collision_kind": state.collision_kind,
            "input_count": state.input_count,
        }

    def _solvable_seed(self) -> int:
        """Choose from scripted patterns with a pre-verified readable route."""

        seed = SOLVABLE_SEEDS[self.rng.randrange(len(SOLVABLE_SEEDS))]
        assert simulate_run(seed, build_safe_route(seed)).survived
        return seed
