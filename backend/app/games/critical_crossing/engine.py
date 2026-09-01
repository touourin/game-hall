from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Literal, cast

from backend.app.arcade.models import ArcadePlayer, ArcadeRoom
from backend.app.games.base import GameRuleError


TICKS_PER_SECOND = 60

UP = 1
DOWN = 2
LEFT = 4
RIGHT = 8
VALID_INPUT_MASK = UP | DOWN | LEFT | RIGHT

SECTION_INTERVAL_TICKS = TICKS_PER_SECOND
FIRST_SECTION_TICK = 50
LANE_CHANGE_TICKS = 12
JUMP_DURATION_TICKS = 42
SLIDE_DURATION_TICKS = 36
FORWARD_METERS_PER_SECOND = 18

MIN_SUCCESS_SLACK_SECONDS = 0.3
UINT32_MASK = 0xFFFFFFFF
BRANCH_CYCLE_SALT = 0xB31D6A2F
BRANCH_PAIR_SALT = 0x7A61F0C9
SAFE_LANE_SALT = 0xC8013EA4
ACTION_CYCLE_SALT = 0x4F1B7D93

RUNNER_LANES = (-1, 0, 1)

RunnerLane = Literal[-1, 0, 1]
RunnerPose = Literal["run", "jump", "slide"]
ObstacleKind = Literal["clear", "ground", "overhead", "barrier", "gap"]
CollisionKind = Literal["ground", "overhead", "barrier", "gap"]


@dataclass(frozen=True)
class DifficultyConfig:
    label: str
    duration_seconds: int

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError("Math Runner duration must be positive")

    @property
    def section_count(self) -> int:
        return self.duration_seconds


DIFFICULTIES: dict[str, DifficultyConfig] = {
    "5s": DifficultyConfig(label="校准", duration_seconds=5),
    "8s": DifficultyConfig(label="疾行", duration_seconds=8),
    "10s": DifficultyConfig(label="极限", duration_seconds=10),
}
DEFAULT_DIFFICULTY = "5s"


@dataclass(frozen=True)
class CourseSection:
    impact_tick: int
    branch_count: Literal[2, 3]
    active_lanes: tuple[RunnerLane, ...]
    obstacles: tuple[ObstacleKind, ObstacleKind, ObstacleKind]
    safe_lane: RunnerLane


@dataclass(frozen=True)
class SimulationResult:
    crossed: bool
    ticks: int
    collision_tick: int | None
    collision_kind: CollisionKind | None
    player_lane: RunnerLane
    passed_sections: int


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
    distance_meters: int = 0
    passed_sections: int = 0


def _mix_u32(value: int) -> int:
    """Avalanche a 32-bit value identically in Python and JavaScript."""

    value &= UINT32_MASK
    value ^= value >> 16
    value = (value * 0x7FEB352D) & UINT32_MASK
    value ^= value >> 15
    value = (value * 0x846CA68B) & UINT32_MASK
    value ^= value >> 16
    return value & UINT32_MASK


def _random_word(seed: int, section_index: int, salt: int) -> int:
    index_key = ((section_index + 1) * 0x9E3779B9) & UINT32_MASK
    return _mix_u32(seed ^ index_key ^ salt)


def _safe_obstacle(seed: int, section_index: int) -> ObstacleKind:
    cycle_offset = _random_word(seed, 0, ACTION_CYCLE_SALT) % 3
    cycle = (section_index + cycle_offset) % 3
    if cycle == 1:
        return "ground"
    if cycle == 2:
        return "overhead"
    return "clear"


def build_course_plan(seed: int, config: DifficultyConfig) -> tuple[CourseSection, ...]:
    branch_offset = _random_word(seed, 0, BRANCH_CYCLE_SALT) % 3
    sections: list[CourseSection] = []

    for section_index in range(config.section_count):
        branch_count: Literal[2, 3] = (
            2 if (section_index + branch_offset) % 3 == 0 else 3
        )
        pair_on_right = bool(
            _random_word(seed, section_index, BRANCH_PAIR_SALT) % 2
        )
        active_lanes: tuple[RunnerLane, ...]
        if branch_count == 3:
            active_lanes = RUNNER_LANES
        elif pair_on_right:
            active_lanes = (0, 1)
        else:
            active_lanes = (-1, 0)

        safe_lane = active_lanes[
            _random_word(seed, section_index, SAFE_LANE_SALT)
            % len(active_lanes)
        ]
        obstacle_values: list[ObstacleKind] = []
        for lane in RUNNER_LANES:
            if lane not in active_lanes:
                obstacle_values.append("gap")
            elif lane == safe_lane:
                obstacle_values.append(_safe_obstacle(seed, section_index))
            else:
                obstacle_values.append("barrier")

        sections.append(
            CourseSection(
                impact_tick=(
                    FIRST_SECTION_TICK
                    + section_index * SECTION_INTERVAL_TICKS
                ),
                branch_count=branch_count,
                active_lanes=active_lanes,
                obstacles=cast(
                    tuple[ObstacleKind, ObstacleKind, ObstacleKind],
                    tuple(obstacle_values),
                ),
                safe_lane=safe_lane,
            )
        )
    return tuple(sections)


def duration_ticks(duration_seconds: int) -> int:
    return duration_seconds * TICKS_PER_SECOND


def runner_distance_meters(tick: int) -> int:
    return round(tick * FORWARD_METERS_PER_SECOND / TICKS_PER_SECOND)


def _next_lane(lane: RunnerLane, direction: Literal[-1, 1]) -> RunnerLane:
    return cast(RunnerLane, max(-1, min(1, lane + direction)))


def _section_collision(
    lane: RunnerLane,
    pose: RunnerPose,
    section: CourseSection,
) -> CollisionKind | None:
    obstacle = section.obstacles[lane + 1]
    if obstacle == "clear":
        return None
    if obstacle == "ground" and pose == "jump":
        return None
    if obstacle == "overhead" and pose == "slide":
        return None
    return cast(CollisionKind, obstacle)


def simulate_run(
    seed: int,
    inputs: list[int],
    config: DifficultyConfig,
) -> SimulationResult:
    target_ticks = duration_ticks(config.duration_seconds)
    plan = build_course_plan(seed, config)
    sections_by_tick = {section.impact_tick: section for section in plan}
    lane: RunnerLane = 0
    pose: RunnerPose = "run"
    pose_ticks = 0
    previous_input_mask = 0
    passed_sections = 0

    for input_index, input_mask in enumerate(inputs[:target_ticks]):
        pressed = input_mask & ~previous_input_mask
        horizontal_pressed = pressed & (LEFT | RIGHT)
        vertical_pressed = pressed & (UP | DOWN)
        pose_ticks = max(0, pose_ticks - 1)
        if pose_ticks == 0:
            pose = "run"

        if horizontal_pressed == LEFT:
            lane = _next_lane(lane, -1)
        elif horizontal_pressed == RIGHT:
            lane = _next_lane(lane, 1)

        if pose == "run":
            if vertical_pressed == UP:
                pose = "jump"
                pose_ticks = JUMP_DURATION_TICKS
            elif vertical_pressed == DOWN:
                pose = "slide"
                pose_ticks = SLIDE_DURATION_TICKS

        tick = input_index + 1
        section = sections_by_tick.get(tick)
        collision_kind = (
            _section_collision(lane, pose, section) if section else None
        )
        if section:
            passed_sections += 1
        previous_input_mask = input_mask

        if collision_kind is not None:
            return SimulationResult(
                crossed=False,
                ticks=tick,
                collision_tick=tick,
                collision_kind=collision_kind,
                player_lane=lane,
                passed_sections=passed_sections - 1,
            )

    ticks = min(len(inputs), target_ticks)
    return SimulationResult(
        crossed=len(inputs) >= target_ticks,
        ticks=ticks,
        collision_tick=None,
        collision_kind=None,
        player_lane=lane,
        passed_sections=passed_sections,
    )


def build_safe_route(seed: int, config: DifficultyConfig) -> list[int]:
    """Build a deterministic lane/action route for generated-course checks."""

    inputs = [0] * duration_ticks(config.duration_seconds)
    lane: RunnerLane = 0

    for section in build_course_plan(seed, config):
        cursor = max(0, section.impact_tick - 44)
        while lane != section.safe_lane:
            direction = LEFT if lane > section.safe_lane else RIGHT
            inputs[cursor] = direction
            cursor += 2
            lane = _next_lane(lane, -1 if direction == LEFT else 1)

        obstacle = section.obstacles[section.safe_lane + 1]
        action_tick = max(0, section.impact_tick - 20)
        if obstacle == "ground":
            inputs[action_tick] = UP
        elif obstacle == "overhead":
            inputs[action_tick] = DOWN

    return inputs


class CriticalCrossingEngine:
    key = "critical_crossing"
    name = "算途疾行"
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
            raise GameRuleError("算途疾行难度不正确")
        return {"difficulty": difficulty}

    def start(self, room: ArcadeRoom) -> None:
        difficulty = room.options.get("difficulty", DEFAULT_DIFFICULTY)
        if not isinstance(difficulty, str) or difficulty not in DIFFICULTIES:
            raise GameRuleError("算途疾行难度不正确")
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
            raise GameRuleError("只有挑战者本人可以提交疾行轨迹")
        if action != "finish":
            raise GameRuleError("不支持这个算途疾行操作")

        state: CriticalCrossingState = room.state
        config = DIFFICULTIES[state.difficulty]
        target_ticks = duration_ticks(config.duration_seconds)
        raw_inputs = payload.get("inputs")
        if not isinstance(raw_inputs, list) or not raw_inputs:
            raise GameRuleError("疾行轨迹不能为空")
        if len(raw_inputs) > target_ticks:
            raise GameRuleError("疾行轨迹超过本轮目标时间")
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            or value > VALID_INPUT_MASK
            for value in raw_inputs
        ):
            raise GameRuleError("疾行轨迹数据不正确")

        result = simulate_run(state.seed, raw_inputs, config)
        if result.collision_tick is not None and len(raw_inputs) != result.ticks:
            raise GameRuleError("碰撞后的疾行轨迹数据不正确")
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
        state.distance_meters = runner_distance_meters(result.ticks)
        state.passed_sections = result.passed_sections
        if result.crossed:
            room.finish(
                "crossed",
                [player.id],
                f"你在云桥上疾行了 {state.distance_meters} 米",
            )
        else:
            causes = {
                "gap": "断桥缺口",
                "barrier": "封路护栏",
                "ground": "地面障碍",
                "overhead": "上方障碍",
            }
            room.finish(
                "interrupted",
                [],
                f"疾行 {state.distance_meters} 米后撞上{causes[result.collision_kind]}",
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
            "sectionCount": config.section_count,
            "profile": {
                "sectionIntervalTicks": SECTION_INTERVAL_TICKS,
                "firstSectionTick": FIRST_SECTION_TICK,
                "laneChangeTicks": LANE_CHANGE_TICKS,
                "jumpDurationTicks": JUMP_DURATION_TICKS,
                "slideDurationTicks": SLIDE_DURATION_TICKS,
                "forwardMetersPerSecond": FORWARD_METERS_PER_SECOND,
            },
            "elapsedMs": state.elapsed_ms,
            "distanceMeters": state.distance_meters,
            "passedSections": state.passed_sections,
            "crossed": state.crossed,
            "collisionTick": state.collision_tick,
            "collisionKind": state.collision_kind,
        }

    def player_result(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
    ) -> tuple[str, str, bool]:
        return "runner", "solo", player.id in room.winner_player_ids

    def record_state(self, room: ArcadeRoom) -> dict[str, Any]:
        state: CriticalCrossingState = room.state
        return {
            "difficulty": state.difficulty,
            "duration_ms": state.duration_seconds * 1_000,
            "elapsed_ms": state.elapsed_ms,
            "distance_meters": state.distance_meters,
            "passed_sections": state.passed_sections,
            "crossed": state.crossed,
            "collision_tick": state.collision_tick,
            "collision_kind": state.collision_kind,
            "input_count": state.input_count,
            "section_count": state.duration_seconds,
            # Preserve this key so existing recorded matches still render.
            "pulse_count": state.duration_seconds,
        }

    def _verified_seed(
        self,
        config: DifficultyConfig,
        previous_seed: int | None,
    ) -> int:
        previous_plan = (
            build_course_plan(previous_seed, config)
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
            if build_course_plan(seed, config) == previous_plan:
                continue
            if simulate_run(seed, build_safe_route(seed, config), config).crossed:
                return seed
        raise RuntimeError("无法生成可通关且不重复的算途疾行路线")
