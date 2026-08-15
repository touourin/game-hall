export const BOARD_WIDTH = 10_000
export const BOARD_HEIGHT = 6_500
export const TICK_RATE = 60

export const PLAYER_RADIUS = 105
export const PLAYER_HIT_RADIUS = 32
export const PLAYER_SPEED = 160

export const PULSE_INTERVAL_TICKS = TICK_RATE
export const PULSE_WARNING_TICKS = 22
export const COLLISION_GRACE_TICKS = PULSE_WARNING_TICKS
export const PULSE_FRONT_SPEED = 160
export const PULSE_FRONT_HIT_RADIUS = 72
export const SAFE_GATE_RADIUS = 920

export const BOUNDARY_ZONE_X = 900
export const BOUNDARY_ZONE_Y = 585
export const BOUNDARY_PRESSURE_LIMIT = 30
export const BOUNDARY_PRESSURE_DECAY = 1
export const BOUNDARY_WALL_SPEED = 100
export const BOUNDARY_WALL_DEPTH = 1_000
export const BOUNDARY_PRESSURE_MAX = BOUNDARY_PRESSURE_LIMIT
  + BOUNDARY_WALL_DEPTH / BOUNDARY_WALL_SPEED

export const INPUT_UP = 1
export const INPUT_DOWN = 2
export const INPUT_LEFT = 4
export const INPUT_RIGHT = 8

export type BoundarySide = 'top' | 'right' | 'bottom' | 'left'
export type CollisionKind = 'pulse' | 'boundary'

export const BOUNDARY_SIDES: readonly BoundarySide[] = [
  'top',
  'right',
  'bottom',
  'left',
]

export interface PulseFront {
  side: BoundarySide
  position: number
  gate: number
}

export type BoundaryPressure = Record<BoundarySide, number>

export interface CrossingState {
  tick: number
  playerX: number
  playerY: number
  boundaryPressure: BoundaryPressure
  collisionTick: number | null
  collisionKind: CollisionKind | null
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

function pulseRng(seed: number, pulseIndex: number): Lcg {
  return new Lcg((seed ^ Math.imul(pulseIndex + 1, 2_654_435_761)) >>> 0)
}

export function pulseSafeGate(
  seed: number,
  pulseIndex: number,
  axis: 'x' | 'y',
): number {
  const axisSalt = axis === 'x' ? 0 : 2_246_822_519
  const rng = new Lcg((pulseRng(seed, pulseIndex).nextU32() ^ axisSalt) >>> 0)
  if (axis === 'y') {
    return rng.integer(0, 1) === 0
      ? rng.integer(2_050, 2_450)
      : rng.integer(4_050, 4_450)
  }
  return rng.integer(0, 1) === 0
    ? rng.integer(3_000, 3_500)
    : rng.integer(6_500, 7_000)
}

export function pulseSides(pulseIndex: number): readonly BoundarySide[] {
  const pattern = pulseIndex % 3
  if (pattern === 0) return ['left', 'right']
  if (pattern === 1) return ['top', 'bottom']
  return BOUNDARY_SIDES
}

export function pulseFronts(
  seed: number,
  tick: number,
  pulseCount: number,
): PulseFront[] {
  const fronts: PulseFront[] = []
  const activeCount = Math.min(
    pulseCount,
    Math.floor(tick / PULSE_INTERVAL_TICKS) + 1,
  )
  for (let pulseIndex = 0; pulseIndex < activeCount; pulseIndex += 1) {
    const elapsed = tick
      - (pulseIndex * PULSE_INTERVAL_TICKS + PULSE_WARNING_TICKS)
    if (elapsed < 0) continue
    const distance = (elapsed + 1) * PULSE_FRONT_SPEED
    for (const side of pulseSides(pulseIndex)) {
      const verticalEdge = side === 'left' || side === 'right'
      const gate = pulseSafeGate(
        seed,
        pulseIndex,
        verticalEdge ? 'y' : 'x',
      )
      const position = side === 'left'
        ? BOUNDARY_ZONE_X + distance
        : side === 'right'
          ? BOARD_WIDTH - BOUNDARY_ZONE_X - distance
          : side === 'top'
            ? BOUNDARY_ZONE_Y + distance
            : BOARD_HEIGHT - BOUNDARY_ZONE_Y - distance
      const span = verticalEdge ? BOARD_WIDTH : BOARD_HEIGHT
      if (position >= -500 && position <= span + 500) {
        fronts.push({ side, position, gate })
      }
    }
  }
  return fronts
}

export function pulseCollision(
  seed: number,
  tick: number,
  playerX: number,
  playerY: number,
  pulseCount: number,
): boolean {
  return pulseFronts(seed, tick, pulseCount).some(({ side, position, gate }) => {
    const verticalEdge = side === 'left' || side === 'right'
    const frontDistance = Math.abs((verticalEdge ? playerX : playerY) - position)
    const gateDistance = Math.abs((verticalEdge ? playerY : playerX) - gate)
    return frontDistance <= PLAYER_HIT_RADIUS + PULSE_FRONT_HIT_RADIUS
      && gateDistance > SAFE_GATE_RADIUS
  })
}

export function boundaryZoneSides(
  playerX: number,
  playerY: number,
): BoundarySide[] {
  const sides: BoundarySide[] = []
  if (playerY <= BOUNDARY_ZONE_Y) sides.push('top')
  if (playerX >= BOARD_WIDTH - BOUNDARY_ZONE_X) sides.push('right')
  if (playerY >= BOARD_HEIGHT - BOUNDARY_ZONE_Y) sides.push('bottom')
  if (playerX <= BOUNDARY_ZONE_X) sides.push('left')
  return sides
}

export function updateBoundaryPressure(
  pressure: BoundaryPressure,
  playerX: number,
  playerY: number,
): BoundaryPressure {
  const activeSides = new Set(boundaryZoneSides(playerX, playerY))
  return Object.fromEntries(BOUNDARY_SIDES.map(side => [
    side,
    activeSides.has(side)
      ? Math.min(BOUNDARY_PRESSURE_MAX, pressure[side] + 1)
      : Math.max(0, pressure[side] - BOUNDARY_PRESSURE_DECAY),
  ])) as BoundaryPressure
}

export function boundaryWallDepth(pressure: number): number {
  if (pressure <= BOUNDARY_PRESSURE_LIMIT) return 0
  return Math.min(
    BOUNDARY_WALL_DEPTH,
    (pressure - BOUNDARY_PRESSURE_LIMIT) * BOUNDARY_WALL_SPEED,
  )
}

export function boundaryCollision(
  playerX: number,
  playerY: number,
  pressure: BoundaryPressure,
): boolean {
  return BOUNDARY_SIDES.some((side) => {
    const depth = boundaryWallDepth(pressure[side])
    if (depth === 0) return false
    if (side === 'top') return playerY - PLAYER_HIT_RADIUS <= depth
    if (side === 'right') {
      return playerX + PLAYER_HIT_RADIUS >= BOARD_WIDTH - depth
    }
    if (side === 'bottom') {
      return playerY + PLAYER_HIT_RADIUS >= BOARD_HEIGHT - depth
    }
    return playerX - PLAYER_HIT_RADIUS <= depth
  })
}

export function durationTicks(durationSeconds: number): number {
  return durationSeconds * TICK_RATE
}

export function createCrossingState(): CrossingState {
  return {
    tick: 0,
    playerX: BOARD_WIDTH / 2,
    playerY: BOARD_HEIGHT / 2,
    boundaryPressure: { top: 0, right: 0, bottom: 0, left: 0 },
    collisionTick: null,
    collisionKind: null,
  }
}

export function advanceCrossingState(
  current: CrossingState,
  seed: number,
  inputMask: number,
  pulseCount: number,
): CrossingState {
  const horizontal = Number(Boolean(inputMask & INPUT_RIGHT))
    - Number(Boolean(inputMask & INPUT_LEFT))
  const vertical = Number(Boolean(inputMask & INPUT_DOWN))
    - Number(Boolean(inputMask & INPUT_UP))
  const step = horizontal && vertical ? 113 : PLAYER_SPEED
  const playerX = Math.min(
    BOARD_WIDTH - PLAYER_RADIUS,
    Math.max(PLAYER_RADIUS, current.playerX + horizontal * step),
  )
  const playerY = Math.min(
    BOARD_HEIGHT - PLAYER_RADIUS,
    Math.max(PLAYER_RADIUS, current.playerY + vertical * step),
  )
  const boundaryPressure = updateBoundaryPressure(
    current.boundaryPressure,
    playerX,
    playerY,
  )

  let collisionKind: CollisionKind | null = null
  if (
    current.tick >= COLLISION_GRACE_TICKS
    && boundaryCollision(playerX, playerY, boundaryPressure)
  ) {
    collisionKind = 'boundary'
  } else if (
    current.tick >= COLLISION_GRACE_TICKS
    && pulseCollision(seed, current.tick, playerX, playerY, pulseCount)
  ) {
    collisionKind = 'pulse'
  }

  return {
    tick: current.tick + 1,
    playerX,
    playerY,
    boundaryPressure,
    collisionTick: collisionKind ? current.tick : null,
    collisionKind,
  }
}

export function replayCrossingRun(
  seed: number,
  inputs: number[],
  durationSeconds: number,
): CrossingState {
  let state = createCrossingState()
  const targetTicks = durationTicks(durationSeconds)
  for (const input of inputs.slice(0, targetTicks)) {
    state = advanceCrossingState(state, seed, input, durationSeconds)
    if (state.collisionTick !== null) break
  }
  return state
}

export function buildSafeRoute(seed: number, durationSeconds: number): number[] {
  let playerX = BOARD_WIDTH / 2
  let playerY = BOARD_HEIGHT / 2
  const inputs: number[] = []

  for (let tick = 0; tick < durationTicks(durationSeconds); tick += 1) {
    const pulseIndex = Math.min(
      Math.floor(tick / PULSE_INTERVAL_TICKS),
      durationSeconds - 1,
    )
    const pattern = pulseIndex % 3
    const targetX = pattern === 1 || pattern === 2
      ? pulseSafeGate(seed, pulseIndex, 'x')
      : playerX
    const targetY = pattern === 0 || pattern === 2
      ? pulseSafeGate(seed, pulseIndex, 'y')
      : playerY
    const horizontal = playerX < targetX - PLAYER_SPEED / 2
      ? INPUT_RIGHT
      : playerX > targetX + PLAYER_SPEED / 2 ? INPUT_LEFT : 0
    const vertical = playerY < targetY - PLAYER_SPEED / 2
      ? INPUT_DOWN
      : playerY > targetY + PLAYER_SPEED / 2 ? INPUT_UP : 0
    const inputMask = horizontal | vertical
    inputs.push(inputMask)

    const step = horizontal && vertical ? 113 : PLAYER_SPEED
    playerX += step * (
      Number(Boolean(horizontal & INPUT_RIGHT))
      - Number(Boolean(horizontal & INPUT_LEFT))
    )
    playerY += step * (
      Number(Boolean(vertical & INPUT_DOWN))
      - Number(Boolean(vertical & INPUT_UP))
    )
  }
  return inputs
}
