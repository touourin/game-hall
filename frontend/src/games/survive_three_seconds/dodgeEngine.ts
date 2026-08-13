export const BOARD_WIDTH = 10_000
export const BOARD_HEIGHT = 6_500
export const TICK_RATE = 60
export const DURATION_TICKS = TICK_RATE * 3
export const PLAYER_RADIUS = 105
export const PLAYER_HIT_RADIUS = 32
export const PLAYER_SPEED = 160
export const BULLET_RADIUS = 44
export const BULLET_HIT_RADIUS = 12
export const BULLETS_PER_TICK = 2
export const COLLISION_GRACE_TICKS = 45

export const INPUT_UP = 1
export const INPUT_DOWN = 2
export const INPUT_LEFT = 4
export const INPUT_RIGHT = 8

export interface DodgeBullet {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
}

export interface DodgeState {
  tick: number
  playerX: number
  playerY: number
  bullets: DodgeBullet[]
  collisionTick: number | null
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

export function spawnBullets(seed: number, tick: number): DodgeBullet[] {
  const mixedSeed = (seed ^ Math.imul(tick + 1, 2_654_435_761)) >>> 0
  const rng = new Lcg(mixedSeed)
  const bullets: DodgeBullet[] = []
  for (let index = 0; index < BULLETS_PER_TICK; index += 1) {
    const side = (tick * BULLETS_PER_TICK + index) % 4
    let x: number
    let y: number
    if (side === 0 || side === 2) {
      x = rng.integer(350, BOARD_WIDTH - 350)
      y = side === 0 ? -120 : BOARD_HEIGHT + 120
    } else {
      x = side === 1 ? BOARD_WIDTH + 120 : -120
      y = rng.integer(350, BOARD_HEIGHT - 350)
    }

    const targetX = BOARD_WIDTH / 2 + rng.integer(-4_000, 4_000)
    const targetY = BOARD_HEIGHT / 2 + rng.integer(-2_600, 2_600)
    const dx = targetX - x
    const dy = targetY - y
    const magnitude = Math.max(Math.abs(dx), Math.abs(dy), 1)
    const speed = rng.integer(80, 105)
    bullets.push({
      x,
      y,
      vx: Math.trunc(dx * speed / magnitude),
      vy: Math.trunc(dy * speed / magnitude),
      radius: BULLET_RADIUS,
    })
  }
  return bullets
}

export function createDodgeState(): DodgeState {
  return {
    tick: 0,
    playerX: BOARD_WIDTH / 2,
    playerY: BOARD_HEIGHT / 2,
    bullets: [],
    collisionTick: null,
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

  const bullets = [...current.bullets, ...spawnBullets(seed, current.tick)]
    .filter(bullet => (
      bullet.x >= -500
      && bullet.x <= BOARD_WIDTH + 500
      && bullet.y >= -500
      && bullet.y <= BOARD_HEIGHT + 500
    ))
    .map(bullet => ({
      ...bullet,
      x: bullet.x + bullet.vx,
      y: bullet.y + bullet.vy,
    }))
  const collided = current.tick >= COLLISION_GRACE_TICKS && bullets.some((bullet) => {
    const radius = PLAYER_HIT_RADIUS + BULLET_HIT_RADIUS
    return (bullet.x - playerX) ** 2 + (bullet.y - playerY) ** 2 <= radius ** 2
  })

  return {
    tick: current.tick + 1,
    playerX,
    playerY,
    bullets,
    collisionTick: collided ? current.tick : null,
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
