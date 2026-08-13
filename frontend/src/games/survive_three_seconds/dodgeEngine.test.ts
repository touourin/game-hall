import { describe, expect, it } from 'vitest'
import {
  DURATION_TICKS,
  INPUT_RIGHT,
  INPUT_UP,
  advanceDodgeState,
  createDodgeState,
  replayDodgeRun,
  spawnBullets,
} from './dodgeEngine'

describe('坚持三秒确定性弹幕', () => {
  it('与服务端为相同种子生成相同弹幕', () => {
    expect(spawnBullets(123_456_789, 0)).toEqual([
      { x: 3_616, y: -120, vx: 33, vy: 92, radius: 44 },
      { x: 10_120, y: 1_340, vx: -86, vy: 29, radius: 44 },
    ])
    expect(spawnBullets(123_456_789, 73)).toEqual([
      { x: 8_593, y: 6_620, vx: -83, vy: -54, radius: 44 },
      { x: -120, y: 3_560, vx: 99, vy: 11, radius: 44 },
    ])
  })

  it('每帧根据方向输入移动玩家并生成弹幕', () => {
    const next = advanceDodgeState(createDodgeState(), 42, INPUT_RIGHT)
    expect(next.tick).toBe(1)
    expect(next.playerX).toBe(5_160)
    expect(next.playerY).toBe(3_250)
    expect(next.bullets).toHaveLength(2)
  })

  it('重放静止轨迹时在与服务端相同的帧发生碰撞', () => {
    const result = replayDodgeRun(123_456_789, Array(DURATION_TICKS).fill(0))
    expect(result.collisionTick).toBe(103)
    expect(result.tick).toBe(104)
  })

  it('可以验证完整的三秒存活轨迹', () => {
    const result = replayDodgeRun(
      123_456_789,
      Array(DURATION_TICKS).fill(INPUT_RIGHT | INPUT_UP),
    )
    expect(result.collisionTick).toBeNull()
    expect(result.tick).toBe(DURATION_TICKS)
  })
})
