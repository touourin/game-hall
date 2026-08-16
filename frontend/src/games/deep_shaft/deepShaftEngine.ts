export const TICK_RATE = 60
export const MAX_TICKS = TICK_RATE * 180
export const TARGET_FLOOR = 100
export const WORLD_WIDTH = 10_000
export const VIEW_HEIGHT = 7_000
export const PLATFORM_START_Y = 1_500
export const PLATFORM_GAP = 540

export const PLAYER_HALF_WIDTH = 210
export const PLAYER_HALF_HEIGHT = 260
export const HORIZONTAL_ACCELERATION = 18
export const HORIZONTAL_FRICTION = 12
export const MAX_HORIZONTAL_SPEED = 95
export const GRAVITY = 8
export const MAX_FALL_SPEED = 130
export const SPRING_SPEED = -140
export const CONVEYOR_SPEED = 28

export const STARTING_HEALTH = 10
export const MAX_HEALTH = 10
export const SPIKE_DAMAGE = 3
export const CEILING_DAMAGE = 3
export const CEILING_DEPTH = 230
export const CEILING_HIT_COOLDOWN = 42
export const CRUMBLE_DELAY_TICKS = 28
export const CAMERA_BASE_SPEED = 18
export const CAMERA_FLOOR_STEP = 2
export const CAMERA_FLOOR_INTERVAL = 20
export const CAMERA_FOLLOW_OFFSET = 2_450
export const MAX_CAMERA_CATCH_UP = 90

export const INPUT_LEFT = 1
export const INPUT_RIGHT = 2

export type PlatformKind =
  | 'normal'
  | 'spikes'
  | 'crumble'
  | 'conveyor_left'
  | 'conveyor_right'
  | 'spring'
export type ShaftEndReason = 'completed' | 'fell' | 'health' | 'timeout'

export interface ShaftPlatform {
  floor: number
  x: number
  y: number
  width: number
  kind: PlatformKind
}

export interface ShaftState {
  seed: number
  tick: number
  playerX: number
  playerY: number
  velocityX: number
  velocityY: number
  cameraY: number
  health: number
  deepestFloor: number
  groundedFloor: number | null
  endReason: ShaftEndReason | null
  visitedFloors: Set<number>
  crumbleDue: Map<number, number>
  brokenFloors: Set<number>
  ceilingCooldown: number
  lastLandedKind: PlatformKind
}

class Lcg {
  private state: number

  constructor(seed: number) {
    this.state = seed >>> 0
  }

  nextU32(): number {
    this.state = (Math.imul(1_664_525, this.state) + 1_013_904_223) >>> 0
    return this.state
  }

  integer(minimum: number, maximum: number): number {
    return minimum + this.nextU32() % (maximum - minimum + 1)
  }
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value))
}

function approachZero(value: number, amount: number): number {
  if (value > 0) return Math.max(0, value - amount)
  if (value < 0) return Math.min(0, value + amount)
  return 0
}

function platformKind(
  floor: number,
  roll: number,
  recentPlatforms: ShaftPlatform[],
): PlatformKind {
  if (floor <= 5 || floor === TARGET_FLOOR) return 'normal'
  if (
    roll < 11
    && recentPlatforms.slice(-3).every(platform => platform.kind !== 'spikes')
  ) return 'spikes'
  if (roll < 21) return 'crumble'
  if (roll < 29) return 'spring'
  if (roll < 39) return 'conveyor_left'
  if (roll < 49) return 'conveyor_right'
  return 'normal'
}

export function generatePlatforms(seed: number): ShaftPlatform[] {
  const rng = new Lcg((seed ^ 0xA5B35705) >>> 0)
  const platforms: ShaftPlatform[] = [
    { floor: 0, x: 3_800, y: PLATFORM_START_Y, width: 2_400, kind: 'normal' },
  ]
  let previousCenter = WORLD_WIDTH / 2
  for (let floor = 1; floor <= TARGET_FLOOR + 4; floor += 1) {
    const width = clamp(2_480 - floor * 7 + rng.integer(-220, 220), 1_520, 2_600)
    const maxShift = Math.min(1_650, 880 + floor * 6)
    const center = clamp(
      previousCenter + rng.integer(-maxShift, maxShift),
      420 + Math.floor(width / 2),
      WORLD_WIDTH - 420 - Math.floor(width / 2),
    )
    platforms.push({
      floor,
      x: center - Math.floor(width / 2),
      y: PLATFORM_START_Y + floor * PLATFORM_GAP,
      width,
      kind: platformKind(floor, rng.integer(0, 99), platforms),
    })
    previousCenter = center
  }
  return platforms
}

export function createShaftState(seed: number): ShaftState {
  const start = generatePlatforms(seed)[0]!
  return {
    seed,
    tick: 0,
    playerX: start.x + Math.floor(start.width / 2),
    playerY: start.y - PLAYER_HALF_HEIGHT,
    velocityX: 0,
    velocityY: 0,
    cameraY: 0,
    health: STARTING_HEALTH,
    deepestFloor: 0,
    groundedFloor: 0,
    endReason: null,
    visitedFloors: new Set([0]),
    crumbleDue: new Map(),
    brokenFloors: new Set(),
    ceilingCooldown: 0,
    lastLandedKind: 'normal',
  }
}

function landingPlatform(
  state: ShaftState,
  platforms: ShaftPlatform[],
  oldBottom: number,
  newBottom: number,
): ShaftPlatform | undefined {
  if (state.velocityY < 0) return undefined
  return platforms
    .filter(platform => (
      !state.brokenFloors.has(platform.floor)
      && oldBottom <= platform.y
      && platform.y <= newBottom
      && state.playerX + PLAYER_HALF_WIDTH > platform.x
      && state.playerX - PLAYER_HALF_WIDTH < platform.x + platform.width
    ))
    .sort((first, second) => first.y - second.y)[0]
}

export function advanceShaftState(
  current: ShaftState,
  inputMask: number,
  platforms = generatePlatforms(current.seed),
): ShaftState {
  if (current.endReason) return current
  const direction = Number(Boolean(inputMask & INPUT_RIGHT)) - Number(Boolean(inputMask & INPUT_LEFT))
  current.velocityX = direction
    ? clamp(
        current.velocityX + direction * HORIZONTAL_ACCELERATION,
        -MAX_HORIZONTAL_SPEED,
        MAX_HORIZONTAL_SPEED,
      )
    : approachZero(current.velocityX, HORIZONTAL_FRICTION)

  for (const [floor, dueTick] of [...current.crumbleDue.entries()]) {
    if (current.tick >= dueTick) {
      current.brokenFloors.add(floor)
      current.crumbleDue.delete(floor)
      if (current.groundedFloor === floor) current.groundedFloor = null
    }
  }

  current.playerX = clamp(
    current.playerX + current.velocityX,
    PLAYER_HALF_WIDTH,
    WORLD_WIDTH - PLAYER_HALF_WIDTH,
  )
  current.velocityY = Math.min(MAX_FALL_SPEED, current.velocityY + GRAVITY)
  const oldBottom = current.playerY + PLAYER_HALF_HEIGHT
  const nextY = current.playerY + current.velocityY
  const newBottom = nextY + PLAYER_HALF_HEIGHT
  current.playerY = nextY
  const landing = landingPlatform(current, platforms, oldBottom, newBottom)

  if (landing) {
    current.playerY = landing.y - PLAYER_HALF_HEIGHT
    current.groundedFloor = landing.floor
    current.lastLandedKind = landing.kind
    if (landing.kind === 'spring') {
      current.velocityY = SPRING_SPEED
      current.groundedFloor = null
    } else current.velocityY = 0
    if (landing.kind === 'conveyor_left') {
      current.playerX = Math.max(PLAYER_HALF_WIDTH, current.playerX - CONVEYOR_SPEED)
    } else if (landing.kind === 'conveyor_right') {
      current.playerX = Math.min(WORLD_WIDTH - PLAYER_HALF_WIDTH, current.playerX + CONVEYOR_SPEED)
    } else if (landing.kind === 'crumble' && !current.crumbleDue.has(landing.floor)) {
      current.crumbleDue.set(landing.floor, current.tick + CRUMBLE_DELAY_TICKS)
    }

    if (!current.visitedFloors.has(landing.floor)) {
      current.visitedFloors.add(landing.floor)
      current.deepestFloor = Math.min(
        TARGET_FLOOR,
        Math.max(current.deepestFloor, landing.floor),
      )
      if (landing.kind === 'spikes') {
        current.health = Math.max(0, current.health - SPIKE_DAMAGE)
        current.velocityY = -80
        current.groundedFloor = null
      } else current.health = Math.min(MAX_HEALTH, current.health + 1)
      if (landing.floor >= TARGET_FLOOR) current.endReason = 'completed'
    }
  } else current.groundedFloor = null

  const scrollSpeed = CAMERA_BASE_SPEED
    + Math.floor(current.deepestFloor / CAMERA_FLOOR_INTERVAL) * CAMERA_FLOOR_STEP
  const followCameraY = current.playerY - CAMERA_FOLLOW_OFFSET
  current.cameraY = Math.max(
    current.cameraY + scrollSpeed,
    Math.min(followCameraY, current.cameraY + MAX_CAMERA_CATCH_UP),
  )
  if (current.ceilingCooldown > 0) current.ceilingCooldown -= 1
  const playerTop = current.playerY - PLAYER_HALF_HEIGHT
  const ceilingY = current.cameraY + CEILING_DEPTH
  if (playerTop <= ceilingY && current.ceilingCooldown === 0) {
    current.health = Math.max(0, current.health - CEILING_DAMAGE)
    current.playerY = ceilingY + PLAYER_HALF_HEIGHT
    current.velocityY = Math.max(250, current.velocityY)
    current.groundedFloor = null
    current.ceilingCooldown = CEILING_HIT_COOLDOWN
  }

  if (current.health <= 0) current.endReason = 'health'
  else if (current.playerY - PLAYER_HALF_HEIGHT > current.cameraY + VIEW_HEIGHT) {
    current.endReason = 'fell'
  }
  current.tick += 1
  if (current.tick >= MAX_TICKS && !current.endReason) current.endReason = 'timeout'
  return current
}

export function replayShaftRun(seed: number, inputs: number[]): ShaftState {
  const state = createShaftState(seed)
  const platforms = generatePlatforms(seed)
  for (const input of inputs.slice(0, MAX_TICKS)) {
    advanceShaftState(state, input, platforms)
    if (state.endReason) break
  }
  return state
}
