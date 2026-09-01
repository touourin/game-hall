export const TICK_RATE = 60

export const INPUT_UP = 1
export const INPUT_DOWN = 2
export const INPUT_LEFT = 4
export const INPUT_RIGHT = 8

export const SECTION_INTERVAL_TICKS = TICK_RATE
export const FIRST_SECTION_TICK = 50
export const LANE_CHANGE_TICKS = 12
export const JUMP_DURATION_TICKS = 42
export const SLIDE_DURATION_TICKS = 36
export const FORWARD_METERS_PER_SECOND = 18

const BRANCH_CYCLE_SALT = 0xB31D6A2F
const BRANCH_PAIR_SALT = 0x7A61F0C9
const SAFE_LANE_SALT = 0xC8013EA4
const ACTION_CYCLE_SALT = 0x4F1B7D93

export const RUNNER_LANES = [-1, 0, 1] as const

export type RunnerLane = typeof RUNNER_LANES[number]
export type RunnerPose = 'run' | 'jump' | 'slide'
export type ObstacleKind = 'clear' | 'ground' | 'overhead' | 'barrier' | 'gap'
export type CollisionKind = Exclude<ObstacleKind, 'clear'>

export interface CrossingProfile {
  sectionIntervalTicks: number
  firstSectionTick: number
  laneChangeTicks: number
  jumpDurationTicks: number
  slideDurationTicks: number
  forwardMetersPerSecond: number
}

export interface CourseSection {
  impactTick: number
  branchCount: 2 | 3
  activeLanes: readonly RunnerLane[]
  obstacles: readonly [ObstacleKind, ObstacleKind, ObstacleKind]
  safeLane: RunnerLane
}

export interface CrossingState {
  tick: number
  lane: RunnerLane
  laneChangeFrom: RunnerLane
  laneChangeTicks: number
  pose: RunnerPose
  poseTicks: number
  previousInputMask: number
  passedSections: number
  collisionTick: number | null
  collisionKind: CollisionKind | null
}

export const DEFAULT_CROSSING_PROFILE: CrossingProfile = {
  sectionIntervalTicks: SECTION_INTERVAL_TICKS,
  firstSectionTick: FIRST_SECTION_TICK,
  laneChangeTicks: LANE_CHANGE_TICKS,
  jumpDurationTicks: JUMP_DURATION_TICKS,
  slideDurationTicks: SLIDE_DURATION_TICKS,
  forwardMetersPerSecond: FORWARD_METERS_PER_SECOND,
}

function mixU32(input: number): number {
  let value = input >>> 0
  value = (value ^ (value >>> 16)) >>> 0
  value = Math.imul(value, 0x7FEB352D) >>> 0
  value = (value ^ (value >>> 15)) >>> 0
  value = Math.imul(value, 0x846CA68B) >>> 0
  return (value ^ (value >>> 16)) >>> 0
}

function randomWord(seed: number, sectionIndex: number, salt: number): number {
  const indexKey = Math.imul(sectionIndex + 1, 0x9E3779B9) >>> 0
  return mixU32((seed ^ indexKey ^ salt) >>> 0)
}

function laneIndex(lane: RunnerLane): number {
  return lane + 1
}

function safeObstacle(seed: number, sectionIndex: number): ObstacleKind {
  const cycleOffset = randomWord(seed, 0, ACTION_CYCLE_SALT) % 3
  return (sectionIndex + cycleOffset) % 3 === 1
    ? 'ground'
    : (sectionIndex + cycleOffset) % 3 === 2 ? 'overhead' : 'clear'
}

export function buildCoursePlan(
  seed: number,
  sectionCount: number,
  profile: CrossingProfile = DEFAULT_CROSSING_PROFILE,
): CourseSection[] {
  const branchOffset = randomWord(seed, 0, BRANCH_CYCLE_SALT) % 3

  return Array.from({ length: sectionCount }, (_, sectionIndex) => {
    const branchCount: 2 | 3 = (sectionIndex + branchOffset) % 3 === 0 ? 2 : 3
    const pairOnRight = Boolean(
      randomWord(seed, sectionIndex, BRANCH_PAIR_SALT) % 2,
    )
    const activeLanes: readonly RunnerLane[] = branchCount === 3
      ? RUNNER_LANES
      : pairOnRight ? [0, 1] : [-1, 0]
    const safeLane = activeLanes[
      randomWord(seed, sectionIndex, SAFE_LANE_SALT) % activeLanes.length
    ]!
    const obstacles = RUNNER_LANES.map((lane): ObstacleKind => {
      if (!activeLanes.includes(lane)) return 'gap'
      if (lane === safeLane) return safeObstacle(seed, sectionIndex)
      return 'barrier'
    }) as [ObstacleKind, ObstacleKind, ObstacleKind]

    return {
      impactTick: profile.firstSectionTick
        + sectionIndex * profile.sectionIntervalTicks,
      branchCount,
      activeLanes,
      obstacles,
      safeLane,
    }
  })
}

export function durationTicks(durationSeconds: number): number {
  return durationSeconds * TICK_RATE
}

export function runnerDistanceMeters(
  tick: number,
  profile: CrossingProfile = DEFAULT_CROSSING_PROFILE,
): number {
  return Math.round(tick * profile.forwardMetersPerSecond / TICK_RATE)
}

export function createCrossingState(): CrossingState {
  return {
    tick: 0,
    lane: 0,
    laneChangeFrom: 0,
    laneChangeTicks: 0,
    pose: 'run',
    poseTicks: 0,
    previousInputMask: 0,
    passedSections: 0,
    collisionTick: null,
    collisionKind: null,
  }
}

function nextLane(lane: RunnerLane, direction: -1 | 1): RunnerLane {
  return Math.max(-1, Math.min(1, lane + direction)) as RunnerLane
}

function collisionAtSection(
  state: Pick<CrossingState, 'lane' | 'pose'>,
  section: CourseSection,
): CollisionKind | null {
  const obstacle = section.obstacles[laneIndex(state.lane)]
  if (obstacle === 'clear') return null
  if (obstacle === 'ground' && state.pose === 'jump') return null
  if (obstacle === 'overhead' && state.pose === 'slide') return null
  return obstacle
}

export function advanceCrossingState(
  current: CrossingState,
  inputMask: number,
  plan: readonly CourseSection[],
  profile: CrossingProfile = DEFAULT_CROSSING_PROFILE,
): CrossingState {
  if (current.collisionTick !== null) return current

  const pressed = inputMask & ~current.previousInputMask
  const horizontalPressed = pressed & (INPUT_LEFT | INPUT_RIGHT)
  const verticalPressed = pressed & (INPUT_UP | INPUT_DOWN)
  let lane = current.lane
  let laneChangeFrom = current.laneChangeFrom
  let laneChangeTicks = Math.max(0, current.laneChangeTicks - 1)
  let pose = current.pose
  let poseTicks = Math.max(0, current.poseTicks - 1)

  if (poseTicks === 0) pose = 'run'

  if (horizontalPressed === INPUT_LEFT || horizontalPressed === INPUT_RIGHT) {
    const direction = horizontalPressed === INPUT_LEFT ? -1 : 1
    const target = nextLane(lane, direction)
    if (target !== lane) {
      laneChangeFrom = lane
      lane = target
      laneChangeTicks = profile.laneChangeTicks
    }
  }

  if (pose === 'run') {
    if (verticalPressed === INPUT_UP) {
      pose = 'jump'
      poseTicks = profile.jumpDurationTicks
    } else if (verticalPressed === INPUT_DOWN) {
      pose = 'slide'
      poseTicks = profile.slideDurationTicks
    }
  }

  const tick = current.tick + 1
  const section = plan.find(candidate => candidate.impactTick === tick)
  const collisionKind = section
    ? collisionAtSection({ lane, pose }, section)
    : null

  return {
    tick,
    lane,
    laneChangeFrom,
    laneChangeTicks,
    pose,
    poseTicks,
    previousInputMask: inputMask,
    passedSections: plan.filter(candidate => (
      candidate.impactTick < tick
      || (candidate.impactTick === tick && collisionKind === null)
    )).length,
    collisionTick: collisionKind ? tick : null,
    collisionKind,
  }
}

export function runnerLanePosition(
  state: CrossingState,
  profile: CrossingProfile = DEFAULT_CROSSING_PROFILE,
): number {
  if (state.laneChangeTicks <= 0) return state.lane
  const progress = 1 - state.laneChangeTicks / profile.laneChangeTicks
  const eased = progress * progress * (3 - 2 * progress)
  return state.laneChangeFrom + (state.lane - state.laneChangeFrom) * eased
}

export function runnerPoseProgress(
  state: CrossingState,
  profile: CrossingProfile = DEFAULT_CROSSING_PROFILE,
): number {
  if (state.pose === 'run') return 0
  const duration = state.pose === 'jump'
    ? profile.jumpDurationTicks
    : profile.slideDurationTicks
  return Math.max(0, Math.min(1, 1 - state.poseTicks / duration))
}

export function replayCrossingRun(
  seed: number,
  inputs: number[],
  durationSeconds: number,
  profile: CrossingProfile = DEFAULT_CROSSING_PROFILE,
): CrossingState {
  let state = createCrossingState()
  const targetTicks = durationTicks(durationSeconds)
  const plan = buildCoursePlan(seed, durationSeconds, profile)
  for (const input of inputs.slice(0, targetTicks)) {
    state = advanceCrossingState(state, input, plan, profile)
    if (state.collisionTick !== null) break
  }
  return state
}

export function buildSafeRoute(
  seed: number,
  durationSeconds: number,
  profile: CrossingProfile = DEFAULT_CROSSING_PROFILE,
): number[] {
  const inputs = Array<number>(durationTicks(durationSeconds)).fill(0)
  const plan = buildCoursePlan(seed, durationSeconds, profile)
  let lane: RunnerLane = 0

  for (const section of plan) {
    let cursor = Math.max(0, section.impactTick - 44)
    while (lane !== section.safeLane) {
      const direction = lane > section.safeLane ? INPUT_LEFT : INPUT_RIGHT
      inputs[cursor] = direction
      cursor += 2
      lane = nextLane(lane, direction === INPUT_LEFT ? -1 : 1)
    }

    const obstacle = section.obstacles[laneIndex(section.safeLane)]
    const actionTick = Math.max(0, section.impactTick - 20)
    if (obstacle === 'ground') inputs[actionTick] = INPUT_UP
    if (obstacle === 'overhead') inputs[actionTick] = INPUT_DOWN
  }

  return inputs
}
