export const BOARD_WIDTH = 10_000
export const BOARD_HEIGHT = 6_500
export const TICK_RATE = 60

export const PLAYER_RADIUS = 105
export const PLAYER_HIT_RADIUS = 32
export const PLAYER_SPEED = 160

export const PULSE_INTERVAL_TICKS = TICK_RATE
export const PULSE_FRONT_HIT_RADIUS = 72

export const BOUNDARY_ZONE_X = 900
export const BOUNDARY_ZONE_Y = 585
export const BOUNDARY_PRESSURE_DECAY = 1
export const BOUNDARY_WALL_SPEED = 100
export const BOUNDARY_WALL_DEPTH = 1_000

export const INPUT_UP = 1
export const INPUT_DOWN = 2
export const INPUT_LEFT = 4
export const INPUT_RIGHT = 8

const PULSE_KIND_SALT = 0xA341316C
const GATE_LANE_SALT = 0xC8013EA4
const GATE_OFFSET_SALT = 0xAD90777D
const AXIS_Y_SALT = 0x7E95761E

export type BoundarySide = 'top' | 'right' | 'bottom' | 'left'
export type CollisionKind = 'pulse' | 'boundary'
export type PulseKind = 'horizontal' | 'vertical' | 'cross'

export const BOUNDARY_SIDES: readonly BoundarySide[] = [
  'top',
  'right',
  'bottom',
  'left',
]

export const PULSE_KINDS: readonly PulseKind[] = [
  'horizontal',
  'vertical',
  'cross',
]

export type PulseWeights = Record<PulseKind, number>

export interface CrossingProfile {
  pulseWeights: PulseWeights
  pulseWarningTicks: number
  pulseFrontSpeed: number
  safeGateRadius: number
  boundaryPressureLimit: number
}

export interface PulsePlanEntry {
  kind: PulseKind
  xGate: number
  yGate: number
}

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

function mixU32(input: number): number {
  let value = input >>> 0
  value = (value ^ (value >>> 16)) >>> 0
  value = Math.imul(value, 0x7FEB352D) >>> 0
  value = (value ^ (value >>> 15)) >>> 0
  value = Math.imul(value, 0x846CA68B) >>> 0
  return (value ^ (value >>> 16)) >>> 0
}

function randomWord(seed: number, pulseIndex: number, salt: number): number {
  const indexKey = Math.imul(pulseIndex + 1, 0x9E3779B9) >>> 0
  return mixU32((seed ^ indexKey ^ salt) >>> 0)
}

export function pulseSafeGate(
  seed: number,
  pulseIndex: number,
  axis: 'x' | 'y',
): number {
  const axisSalt = axis === 'x' ? 0 : AXIS_Y_SALT
  const ranges: readonly (readonly [number, number])[] = axis === 'x'
    ? [[3_000, 3_500], [6_500, 7_000]]
    : [[2_050, 2_450], [4_050, 4_450]]
  const lane = randomWord(
    seed,
    pulseIndex,
    GATE_LANE_SALT ^ axisSalt,
  ) % ranges.length
  const [minimum, maximum] = ranges[lane]!
  const offset = randomWord(
    seed,
    pulseIndex,
    GATE_OFFSET_SALT ^ axisSalt,
  ) % (maximum - minimum + 1)
  return minimum + offset
}

export function pulseSequence(
  seed: number,
  pulseCount: number,
  weights: PulseWeights,
): PulseKind[] {
  const sequence: PulseKind[] = []
  for (let pulseIndex = 0; pulseIndex < pulseCount; pulseIndex += 1) {
    const previous = sequence.at(-1)
    const choices = PULSE_KINDS
      .filter(kind => kind !== previous && weights[kind] > 0)
      .map(kind => [kind, weights[kind]] as const)
    const totalWeight = choices.reduce((total, [, weight]) => total + weight, 0)
    let roll = randomWord(seed, pulseIndex, PULSE_KIND_SALT) % totalWeight
    for (const [kind, weight] of choices) {
      if (roll < weight) {
        sequence.push(kind)
        break
      }
      roll -= weight
    }
  }
  return sequence
}

export function buildPulsePlan(
  seed: number,
  pulseCount: number,
  profile: CrossingProfile,
): PulsePlanEntry[] {
  return pulseSequence(seed, pulseCount, profile.pulseWeights).map(
    (kind, pulseIndex) => ({
      kind,
      xGate: pulseSafeGate(seed, pulseIndex, 'x'),
      yGate: pulseSafeGate(seed, pulseIndex, 'y'),
    }),
  )
}

export function pulseSides(kind: PulseKind): readonly BoundarySide[] {
  if (kind === 'horizontal') return ['left', 'right']
  if (kind === 'vertical') return ['top', 'bottom']
  return BOUNDARY_SIDES
}

export function pulseFronts(
  plan: readonly PulsePlanEntry[],
  tick: number,
  profile: CrossingProfile,
): PulseFront[] {
  const fronts: PulseFront[] = []
  const activeCount = Math.min(
    plan.length,
    Math.floor(tick / PULSE_INTERVAL_TICKS) + 1,
  )
  for (let pulseIndex = 0; pulseIndex < activeCount; pulseIndex += 1) {
    const pulse = plan[pulseIndex]!
    const elapsed = tick
      - (pulseIndex * PULSE_INTERVAL_TICKS + profile.pulseWarningTicks)
    if (elapsed < 0) continue
    const distance = (elapsed + 1) * profile.pulseFrontSpeed
    for (const side of pulseSides(pulse.kind)) {
      const verticalEdge = side === 'left' || side === 'right'
      const gate = verticalEdge ? pulse.yGate : pulse.xGate
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
  plan: readonly PulsePlanEntry[],
  tick: number,
  playerX: number,
  playerY: number,
  profile: CrossingProfile,
): boolean {
  return pulseFronts(plan, tick, profile).some(({ side, position, gate }) => {
    const verticalEdge = side === 'left' || side === 'right'
    const frontDistance = Math.abs((verticalEdge ? playerX : playerY) - position)
    const gateDistance = Math.abs((verticalEdge ? playerY : playerX) - gate)
    return frontDistance <= PLAYER_HIT_RADIUS + PULSE_FRONT_HIT_RADIUS
      && gateDistance > profile.safeGateRadius
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
  profile: CrossingProfile,
): BoundaryPressure {
  const activeSides = new Set(boundaryZoneSides(playerX, playerY))
  const pressureMax = profile.boundaryPressureLimit
    + BOUNDARY_WALL_DEPTH / BOUNDARY_WALL_SPEED
  return Object.fromEntries(BOUNDARY_SIDES.map(side => [
    side,
    activeSides.has(side)
      ? Math.min(pressureMax, pressure[side] + 1)
      : Math.max(0, pressure[side] - BOUNDARY_PRESSURE_DECAY),
  ])) as BoundaryPressure
}

export function boundaryWallDepth(
  pressure: number,
  profile: CrossingProfile,
): number {
  if (pressure <= profile.boundaryPressureLimit) return 0
  return Math.min(
    BOUNDARY_WALL_DEPTH,
    (pressure - profile.boundaryPressureLimit) * BOUNDARY_WALL_SPEED,
  )
}

export function boundaryCollision(
  playerX: number,
  playerY: number,
  pressure: BoundaryPressure,
  profile: CrossingProfile,
): boolean {
  return BOUNDARY_SIDES.some((side) => {
    const depth = boundaryWallDepth(pressure[side], profile)
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
  inputMask: number,
  plan: readonly PulsePlanEntry[],
  profile: CrossingProfile,
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
    profile,
  )

  let collisionKind: CollisionKind | null = null
  if (
    current.tick >= profile.pulseWarningTicks
    && boundaryCollision(playerX, playerY, boundaryPressure, profile)
  ) {
    collisionKind = 'boundary'
  } else if (
    current.tick >= profile.pulseWarningTicks
    && pulseCollision(plan, current.tick, playerX, playerY, profile)
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
  profile: CrossingProfile,
): CrossingState {
  let state = createCrossingState()
  const targetTicks = durationTicks(durationSeconds)
  const plan = buildPulsePlan(seed, durationSeconds, profile)
  for (const input of inputs.slice(0, targetTicks)) {
    state = advanceCrossingState(state, input, plan, profile)
    if (state.collisionTick !== null) break
  }
  return state
}

export function buildSafeRoute(
  seed: number,
  durationSeconds: number,
  profile: CrossingProfile,
): number[] {
  let playerX = BOARD_WIDTH / 2
  let playerY = BOARD_HEIGHT / 2
  const inputs: number[] = []
  const plan = buildPulsePlan(seed, durationSeconds, profile)

  for (let tick = 0; tick < durationTicks(durationSeconds); tick += 1) {
    const pulseIndex = Math.min(
      Math.floor(tick / PULSE_INTERVAL_TICKS),
      plan.length - 1,
    )
    const pulse = plan[pulseIndex]!
    const targetX = pulse.kind === 'vertical' || pulse.kind === 'cross'
      ? pulse.xGate
      : playerX
    const targetY = pulse.kind === 'horizontal' || pulse.kind === 'cross'
      ? pulse.yGate
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
