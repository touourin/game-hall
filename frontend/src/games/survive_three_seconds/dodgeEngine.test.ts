import { describe, expect, it } from 'vitest'
import {
  DURATION_TICKS,
  EDGE_PRESSURE_LIMIT,
  INPUT_RIGHT,
  INPUT_UP,
  WAVE_BULLET_SPEED,
  WAVE_WARNING_TICKS,
  advanceDodgeState,
  buildSafeRoute,
  createDodgeState,
  replayDodgeRun,
  spawnBullets,
  waveSafeGap,
} from './dodgeEngine'

describe('坚持三秒确定性弹幕', () => {
  it('每波先预警，再生成带安全缺口的慢速弹幕帘', () => {
    expect(spawnBullets(123_456_789, WAVE_WARNING_TICKS - 1)).toEqual([])

    const bullets = spawnBullets(123_456_789, WAVE_WARNING_TICKS)
    const gap = waveSafeGap(123_456_789, 0, 'y')
    expect(bullets.length).toBeGreaterThan(20)
    expect(bullets.every(bullet => Math.abs(bullet.vx) === WAVE_BULLET_SPEED)).toBe(true)
    expect(bullets.every(bullet => bullet.vy === 0)).toBe(true)
    expect(bullets.every(bullet => Math.abs(bullet.y - gap) > 850)).toBe(true)
  })

  it('每帧根据方向输入移动玩家并保留边缘压力状态', () => {
    const next = advanceDodgeState(createDodgeState(), 42, INPUT_RIGHT)
    expect(next.tick).toBe(1)
    expect(next.playerX).toBe(5_160)
    expect(next.playerY).toBe(3_250)
    expect(next.edgePressure).toEqual({ top: 0, right: 0, bottom: 0, left: 0 })
  })

  it('角落滞留会在可见压力累计后触发清场墙', () => {
    const result = replayDodgeRun(
      123_456_789,
      Array(DURATION_TICKS).fill(INPUT_UP),
    )
    expect(result.collisionKind).toBe('edge_wall')
    expect(result.collisionTick).toBeGreaterThanOrEqual(EDGE_PRESSURE_LIMIT)
    expect(result.tick).toBeLessThan(DURATION_TICKS)
  })

  it('离开边缘后压力逐帧消退', () => {
    let state = createDodgeState()
    state = { ...state, playerX: 500, edgePressure: { ...state.edgePressure, left: 20 } }
    state = advanceDodgeState(state, 42, INPUT_RIGHT)
    expect(state.edgePressure.left).toBe(21)

    state = { ...state, playerX: 2_000 }
    state = advanceDodgeState(state, 42, 0)
    expect(state.edgePressure.left).toBe(20)
  })

  it('预先验证的引导路线能穿过三段波次', () => {
    const result = replayDodgeRun(123_456_789, buildSafeRoute(123_456_789))
    expect(result.collisionKind).toBeNull()
    expect(result.collisionTick).toBeNull()
    expect(result.tick).toBe(DURATION_TICKS)
  })
})
