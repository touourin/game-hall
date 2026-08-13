export const BOARD_WIDTH = 10_000
export const BOARD_HEIGHT = 6_500
export const TICK_RATE = 60
export const DURATION_TICKS = TICK_RATE * 3

export const PLAYER_RADIUS = 105
export const PLAYER_HIT_RADIUS = 32
export const PLAYER_SPEED = 160
export const BULLET_RADIUS = 44

export const WAVE_TICKS = TICK_RATE
export const WAVE_WARNING_TICKS = 18
export const COLLISION_GRACE_TICKS = WAVE_WARNING_TICKS
export const WAVE_BULLET_SPEED = 68
export const WAVE_LANE_COUNT = 18
export const WAVE_LANE_JITTER = 24
export const WAVE_FRONT_HIT_RADIUS = 72
export const SAFE_GAP_RADIUS = 850

export const EDGE_ZONE_X = 900
export const EDGE_ZONE_Y = 585
export const EDGE_PRESSURE_LIMIT = 36
export const EDGE_PRESSURE_DECAY = 1
export const EDGE_WALL_SPEED = 50
export const EDGE_WALL_DEPTH = 1_000
export const EDGE_WALL_HIT_RADIUS = 80
export const EDGE_PRESSURE_MAX = EDGE_PRESSURE_LIMIT + EDGE_WALL_DEPTH / EDGE_WALL_SPEED

export const INPUT_UP = 1
export const INPUT_DOWN = 2
export const INPUT_LEFT = 4
export const INPUT_RIGHT = 8

export type EdgeSide = 'top' | 'right' | 'bottom' | 'left'
export type CollisionKind = 'bullet' | 'edge_wall'

export const EDGE_SIDES: readonly EdgeSide[] = ['top', 'right', 'bottom', 'left']

export interface DodgeBullet {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
}

export interface WaveFront {
  side: EdgeSide
  position: number
  gap: number
}

export type EdgePressure = Record<EdgeSide, number>

export interface DodgeState {
  tick: number
  playerX: number
  playerY: number
  bullets: DodgeBullet[]
  edgePressure: EdgePressure
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

function waveRng(seed: number, waveIndex: number): Lcg {
  return new Lcg((seed ^ Math.imul(waveIndex + 1, 2_654_435_761)) >>> 0)
}

export function waveSafeGap(seed: number, waveIndex: number, axis: 'x' | 'y'): number {
  const axisSalt = axis === 'x' ? 0 : 2_246_822_519
  const rng = new Lcg((waveRng(seed, waveIndex).nextU32() ^ axisSalt) >>> 0)
  if (axis === 'y') {
    return rng.integer(0, 1) === 0
      ? rng.integer(2_050, 2_450)
      : rng.integer(4_050, 4_450)
  }
  return rng.integer(0, 1) === 0
    ? rng.integer(3_000, 3_500)
    : rng.integer(6_500, 7_000)
}

export function waveSides(waveIndex: number): readonly EdgeSide[] {
  if (waveIndex === 0) return ['left', 'right']
  if (waveIndex === 1) return ['top', 'bottom']
  return EDGE_SIDES
}

export function spawnBullets(seed: number, tick: number): DodgeBullet[] {
  const waveIndex = Math.min(Math.floor(tick / WAVE_TICKS), 2)
  const waveTick = tick % WAVE_TICKS
  if (waveTick !== WAVE_WARNING_TICKS) return []

  const rng = new Lcg((
    seed
    ^ Math.imul(waveIndex + 1, 2_654_435_761)
    ^ Math.imul(waveTick + 1, 2_246_822_519)
  ) >>> 0)
  const bullets: DodgeBullet[] = []

  for (const side of waveSides(waveIndex)) {
    const verticalEdge = side === 'left' || side === 'right'
    const span = verticalEdge ? BOARD_HEIGHT : BOARD_WIDTH
    const gap = waveIndex === 2
      ? waveSafeGap(seed, verticalEdge ? 0 : 1, verticalEdge ? 'y' : 'x')
      : waveSafeGap(seed, waveIndex, verticalEdge ? 'y' : 'x')
    for (let lane = 0; lane < WAVE_LANE_COUNT; lane += 1) {
      const position = Math.floor((lane + 1) * span / (WAVE_LANE_COUNT + 1))
        + rng.integer(-WAVE_LANE_JITTER, WAVE_LANE_JITTER)
      if (Math.abs(position - gap) <= SAFE_GAP_RADIUS) continue

      if (side === 'left') {
        bullets.push({ x: EDGE_ZONE_X, y: position, vx: WAVE_BULLET_SPEED, vy: 0, radius: BULLET_RADIUS })
      } else if (side === 'right') {
        bullets.push({ x: BOARD_WIDTH - EDGE_ZONE_X, y: position, vx: -WAVE_BULLET_SPEED, vy: 0, radius: BULLET_RADIUS })
      } else if (side === 'top') {
        bullets.push({ x: position, y: EDGE_ZONE_Y, vx: 0, vy: WAVE_BULLET_SPEED, radius: BULLET_RADIUS })
      } else {
        bullets.push({ x: position, y: BOARD_HEIGHT - EDGE_ZONE_Y, vx: 0, vy: -WAVE_BULLET_SPEED, radius: BULLET_RADIUS })
      }
    }
  }
  return bullets
}

export function waveFronts(seed: number, tick: number): WaveFront[] {
  const fronts: WaveFront[] = []
  for (let waveIndex = 0; waveIndex < 3; waveIndex += 1) {
    const elapsed = tick - (waveIndex * WAVE_TICKS + WAVE_WARNING_TICKS)
    if (elapsed < 0) continue
    const distance = (elapsed + 1) * WAVE_BULLET_SPEED
    for (const side of waveSides(waveIndex)) {
      const verticalEdge = side === 'left' || side === 'right'
      const gapWave = waveIndex === 2 ? (verticalEdge ? 0 : 1) : waveIndex
      const gap = waveSafeGap(seed, gapWave, verticalEdge ? 'y' : 'x')
      const position = side === 'left'
        ? EDGE_ZONE_X + distance
        : side === 'right'
          ? BOARD_WIDTH - EDGE_ZONE_X - distance
          : side === 'top'
            ? EDGE_ZONE_Y + distance
            : BOARD_HEIGHT - EDGE_ZONE_Y - distance
      const span = verticalEdge ? BOARD_WIDTH : BOARD_HEIGHT
      if (position >= -500 && position <= span + 500) fronts.push({ side, position, gap })
    }
  }
  return fronts
}

export function waveCurtainCollision(
  seed: number,
  tick: number,
  playerX: number,
  playerY: number,
): boolean {
  return waveFronts(seed, tick).some(({ side, position, gap }) => {
    const verticalEdge = side === 'left' || side === 'right'
    const frontDistance = Math.abs((verticalEdge ? playerX : playerY) - position)
    const gapDistance = Math.abs((verticalEdge ? playerY : playerX) - gap)
    return frontDistance <= PLAYER_HIT_RADIUS + WAVE_FRONT_HIT_RADIUS
      && gapDistance > SAFE_GAP_RADIUS
  })
}

export function edgeZoneSides(playerX: number, playerY: number): EdgeSide[] {
  const sides: EdgeSide[] = []
  if (playerY <= EDGE_ZONE_Y) sides.push('top')
  if (playerX >= BOARD_WIDTH - EDGE_ZONE_X) sides.push('right')
  if (playerY >= BOARD_HEIGHT - EDGE_ZONE_Y) sides.push('bottom')
  if (playerX <= EDGE_ZONE_X) sides.push('left')
  return sides
}

export function updateEdgePressure(
  pressure: EdgePressure,
  playerX: number,
  playerY: number,
): EdgePressure {
  const activeSides = new Set(edgeZoneSides(playerX, playerY))
  return Object.fromEntries(EDGE_SIDES.map(side => [
    side,
    activeSides.has(side)
      ? Math.min(EDGE_PRESSURE_MAX, pressure[side] + 1)
      : Math.max(0, pressure[side] - EDGE_PRESSURE_DECAY),
  ])) as EdgePressure
}

export function edgeWallDepth(pressure: number): number {
  if (pressure <= EDGE_PRESSURE_LIMIT) return 0
  return Math.min(
    EDGE_WALL_DEPTH,
    (pressure - EDGE_PRESSURE_LIMIT) * EDGE_WALL_SPEED,
  )
}

export function edgeWallCollision(
  playerX: number,
  playerY: number,
  pressure: EdgePressure,
): boolean {
  return EDGE_SIDES.some((side) => {
    const depth = edgeWallDepth(pressure[side])
    if (depth === 0) return false
    if (side === 'top') return playerY - PLAYER_HIT_RADIUS <= depth
    if (side === 'right') return playerX + PLAYER_HIT_RADIUS >= BOARD_WIDTH - depth
    if (side === 'bottom') return playerY + PLAYER_HIT_RADIUS >= BOARD_HEIGHT - depth
    return playerX - PLAYER_HIT_RADIUS <= depth
  })
}

export function createDodgeState(): DodgeState {
  return {
    tick: 0,
    playerX: BOARD_WIDTH / 2,
    playerY: BOARD_HEIGHT / 2,
    bullets: [],
    edgePressure: { top: 0, right: 0, bottom: 0, left: 0 },
    collisionTick: null,
    collisionKind: null,
  }
}

export function advanceDodgeState(
  current: DodgeState,
  seed: number,
  inputMask: number,
): DodgeState {
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
  const edgePressure = updateEdgePressure(current.edgePressure, playerX, playerY)

  const bullets = [...current.bullets, ...spawnBullets(seed, current.tick)]
    .filter(bullet => (
      bullet.x >= -500
      && bullet.x <= BOARD_WIDTH + 500
      && bullet.y >= -500
      && bullet.y <= BOARD_HEIGHT + 500
    ))
    .map(bullet => ({ ...bullet, x: bullet.x + bullet.vx, y: bullet.y + bullet.vy }))

  let collisionKind: CollisionKind | null = null
  if (current.tick >= COLLISION_GRACE_TICKS && edgeWallCollision(playerX, playerY, edgePressure)) {
    collisionKind = 'edge_wall'
  } else if (
    current.tick >= COLLISION_GRACE_TICKS
    && waveCurtainCollision(seed, current.tick, playerX, playerY)
  ) {
    collisionKind = 'bullet'
  }

  return {
    tick: current.tick + 1,
    playerX,
    playerY,
    bullets,
    edgePressure,
    collisionTick: collisionKind ? current.tick : null,
    collisionKind,
  }
}

export function replayDodgeRun(seed: number, inputs: number[]): DodgeState {
  let state = createDodgeState()
  for (const input of inputs.slice(0, DURATION_TICKS)) {
    state = advanceDodgeState(state, seed, input)
    if (state.collisionTick !== null) break
  }
  return state
}

export function buildSafeRoute(seed: number): number[] {
  let playerX = BOARD_WIDTH / 2
  let playerY = BOARD_HEIGHT / 2
  const inputs: number[] = []
  const firstGapY = waveSafeGap(seed, 0, 'y')
  const secondGapX = waveSafeGap(seed, 1, 'x')

  for (let tick = 0; tick < DURATION_TICKS; tick += 1) {
    const [targetX, targetY] = tick < WAVE_TICKS
      ? [BOARD_WIDTH / 2, firstGapY]
      : tick < WAVE_TICKS * 2
        ? [secondGapX, firstGapY]
        : [secondGapX, firstGapY]
    const horizontal = playerX < targetX - PLAYER_SPEED / 2
      ? INPUT_RIGHT
      : playerX > targetX + PLAYER_SPEED / 2 ? INPUT_LEFT : 0
    const vertical = playerY < targetY - PLAYER_SPEED / 2
      ? INPUT_DOWN
      : playerY > targetY + PLAYER_SPEED / 2 ? INPUT_UP : 0
    const inputMask = horizontal | vertical
    inputs.push(inputMask)

    const diagonal = Boolean(horizontal && vertical)
    const step = diagonal ? 113 : PLAYER_SPEED
    playerX += step * (Number(Boolean(horizontal & INPUT_RIGHT)) - Number(Boolean(horizontal & INPUT_LEFT)))
    playerY += step * (Number(Boolean(vertical & INPUT_DOWN)) - Number(Boolean(vertical & INPUT_UP)))
  }
  return inputs
}
