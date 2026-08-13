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
PLAYER_SPEED = 104
BULLET_RADIUS = 44
BULLETS_PER_TICK = 2
SOLVABLE_SEEDS = (
    797_605_564,
    1_848_070_633,
    461_793_307,
    1_534_017_789,
    100_221_012,
    253_343_592,
    2_824_825_279,
    2_872_178_668,
    3_721_996_133,
    384_786_075,
)
MIN_SUCCESS_SECONDS = 2.7

UP = 1
DOWN = 2
LEFT = 4
RIGHT = 8
VALID_INPUT_MASK = UP | DOWN | LEFT | RIGHT
SURVIVAL_PROBE_MASKS = (0, UP, DOWN, LEFT, RIGHT, UP | LEFT, UP | RIGHT, DOWN | LEFT, DOWN | RIGHT)


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
    player_x: int
    player_y: int


@dataclass
class SurviveThreeSecondsState:
    seed: int = 0
    started_monotonic: float = 0.0
    elapsed_ms: int = 0
    survived: bool | None = None
    collision_tick: int | None = None
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


def _trunc_div(numerator: int, denominator: int) -> int:
    quotient = abs(numerator) // denominator
    return -quotient if numerator < 0 else quotient


def spawn_bullets(seed: int, tick: int) -> list[Bullet]:
    """Generate one tick's barrage without depending on earlier game state."""

    rng = Lcg((seed ^ ((tick + 1) * 2_654_435_761)) & 0xFFFFFFFF)
    bullets: list[Bullet] = []
    for index in range(BULLETS_PER_TICK):
        # Rotate through all four edges every two ticks so the barrage is
        # visibly four-sided instead of depending on the PRNG's low bits.
        side = (tick * BULLETS_PER_TICK + index) % 4
        if side in {0, 2}:
            x = rng.integer(350, BOARD_WIDTH - 350)
            y = -120 if side == 0 else BOARD_HEIGHT + 120
        else:
            x = BOARD_WIDTH + 120 if side == 1 else -120
            y = rng.integer(350, BOARD_HEIGHT - 350)

        target_x = BOARD_WIDTH // 2 + rng.integer(-2_250, 2_250)
        target_y = BOARD_HEIGHT // 2 + rng.integer(-1_550, 1_550)
        dx = target_x - x
        dy = target_y - y
        magnitude = max(abs(dx), abs(dy), 1)
        speed = rng.integer(126, 178)
        vx = _trunc_div(dx * speed, magnitude)
        vy = _trunc_div(dy * speed, magnitude)
        bullets.append(Bullet(x=x, y=y, vx=vx, vy=vy))
    return bullets


def simulate_run(seed: int, inputs: list[int]) -> SimulationResult:
    player_x = BOARD_WIDTH // 2
    player_y = BOARD_HEIGHT // 2
    bullets: list[Bullet] = []

    for tick, input_mask in enumerate(inputs[:DURATION_TICKS]):
        horizontal = int(bool(input_mask & RIGHT)) - int(bool(input_mask & LEFT))
        vertical = int(bool(input_mask & DOWN)) - int(bool(input_mask & UP))
        if horizontal and vertical:
            step = 65
            player_x += horizontal * step
            player_y += vertical * step
        else:
            player_x += horizontal * PLAYER_SPEED
            player_y += vertical * PLAYER_SPEED
        player_x = min(BOARD_WIDTH - PLAYER_RADIUS, max(PLAYER_RADIUS, player_x))
        player_y = min(BOARD_HEIGHT - PLAYER_RADIUS, max(PLAYER_RADIUS, player_y))

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

        for bullet in bullets:
            radius = PLAYER_RADIUS + bullet.radius
            if (
                (bullet.x - player_x) ** 2 + (bullet.y - player_y) ** 2
                <= radius**2
            ):
                return SimulationResult(
                    survived=False,
                    ticks=tick + 1,
                    collision_tick=tick,
                    player_x=player_x,
                    player_y=player_y,
                )

    return SimulationResult(
        survived=len(inputs) >= DURATION_TICKS,
        ticks=min(len(inputs), DURATION_TICKS),
        collision_tick=None,
        player_x=player_x,
        player_y=player_y,
    )


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
        state.input_count = len(raw_inputs)
        if result.survived:
            room.finish("survived", [player.id], "你从弹幕中坚持了整整 3 秒")
        else:
            room.finish("hit", [], f"坚持了 {state.elapsed_ms / 1_000:.2f} 秒后被弹幕击中")

    def view(self, room: ArcadeRoom, viewer: ArcadePlayer) -> dict[str, Any]:
        state: SurviveThreeSecondsState = room.state
        return {
            "seed": state.seed,
            "durationMs": DURATION_SECONDS * 1_000,
            "tickRate": TICKS_PER_SECOND,
            "elapsedMs": state.elapsed_ms,
            "survived": state.survived,
            "collisionTick": state.collision_tick,
        }

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        return "dodger", "solo", player.id in room.winner_player_ids

    def record_state(self, room: ArcadeRoom) -> dict[str, int | bool | None]:
        state: SurviveThreeSecondsState = room.state
        return {
            "duration_ms": DURATION_SECONDS * 1_000,
            "elapsed_ms": state.elapsed_ms,
            "survived": state.survived,
            "collision_tick": state.collision_tick,
            "input_count": state.input_count,
        }

    def _solvable_seed(self) -> int:
        """Choose from patterns pre-verified to contain an escape lane."""

        seed = SOLVABLE_SEEDS[self.rng.randrange(len(SOLVABLE_SEEDS))]
        assert any(
            simulate_run(seed, [mask] * DURATION_TICKS).survived
            for mask in SURVIVAL_PROBE_MASKS
        )
        return seed
