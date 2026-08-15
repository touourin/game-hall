import { describe, expect, it } from 'vitest'
import {
  BOUNDARY_PRESSURE_LIMIT,
  INPUT_RIGHT,
  INPUT_UP,
  PULSE_FRONT_SPEED,
  PULSE_WARNING_TICKS,
  advanceCrossingState,
  buildSafeRoute,
  createCrossingState,
  durationTicks,
  pulseFronts,
  pulseSafeGate,
  replayCrossingRun,
} from './crossingEngine'

describe('临界穿越确定性模拟', () => {
  it('先显示预警，再让带安全缺口的横向脉冲进入场地', () => {
    expect(pulseFronts(162_944_417, PULSE_WARNING_TICKS - 1, 5)).toEqual([])

    const fronts = pulseFronts(162_944_417, PULSE_WARNING_TICKS, 5)
    const gate = pulseSafeGate(162_944_417, 0, 'y')
    expect(fronts.map(front => front.side)).toEqual(['left', 'right'])
    expect(fronts.every(front => front.gate === gate)).toBe(true)
    expect(fronts.map(front => front.position)).toEqual([
      900 + PULSE_FRONT_SPEED,
      9_100 - PULSE_FRONT_SPEED,
    ])
  })

  it('每帧根据方向输入移动导航核心并保留边界压力', () => {
    const next = advanceCrossingState(
      createCrossingState(),
      162_944_417,
      INPUT_RIGHT,
      5,
    )
    expect(next.tick).toBe(1)
    expect(next.playerX).toBe(5_160)
    expect(next.playerY).toBe(3_250)
    expect(next.boundaryPressure).toEqual({
      top: 0,
      right: 0,
      bottom: 0,
      left: 0,
    })
  })

  it('持续贴边会在可见压力累计后触发边界封锁', () => {
    const result = replayCrossingRun(
      162_944_417,
      Array(durationTicks(5)).fill(INPUT_UP),
      5,
    )
    expect(result.collisionKind).toBe('boundary')
    expect(result.collisionTick).toBeGreaterThanOrEqual(BOUNDARY_PRESSURE_LIMIT)
    expect(result.tick).toBeLessThan(durationTicks(5))
  })

  it('离开边缘后压力逐帧消退', () => {
    let state = createCrossingState()
    state = {
      ...state,
      playerX: 500,
      boundaryPressure: { ...state.boundaryPressure, left: 20 },
    }
    state = advanceCrossingState(state, 42, INPUT_RIGHT, 5)
    expect(state.boundaryPressure.left).toBe(21)

    state = { ...state, playerX: 2_000 }
    state = advanceCrossingState(state, 42, 0, 5)
    expect(state.boundaryPressure.left).toBe(20)
  })

  it.each([5, 8, 10])('预先验证的路线能完成 %s 秒挑战', (seconds) => {
    const seed = 162_944_417
    const result = replayCrossingRun(
      seed,
      buildSafeRoute(seed, seconds),
      seconds,
    )
    expect(result.collisionKind).toBeNull()
    expect(result.collisionTick).toBeNull()
    expect(result.tick).toBe(durationTicks(seconds))
  })
})
