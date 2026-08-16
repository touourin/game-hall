import { describe, expect, it } from 'vitest'
import {
  INPUT_RIGHT,
  INPUT_UP,
  advanceCrossingState,
  buildPulsePlan,
  buildSafeRoute,
  createCrossingState,
  durationTicks,
  pulseFronts,
  pulseSequence,
  replayCrossingRun,
  type CrossingProfile,
} from './crossingEngine'

const CALIBRATION: CrossingProfile = {
  pulseWeights: { horizontal: 48, vertical: 48, cross: 4 },
  pulseWarningTicks: 28,
  pulseFrontSpeed: 180,
  safeGateRadius: 1_050,
  boundaryPressureLimit: 36,
}

const OVERLOAD: CrossingProfile = {
  pulseWeights: { horizontal: 38, vertical: 38, cross: 24 },
  pulseWarningTicks: 23,
  pulseFrontSpeed: 175,
  safeGateRadius: 920,
  boundaryPressureLimit: 30,
}

const CRITICAL: CrossingProfile = {
  pulseWeights: { horizontal: 25, vertical: 25, cross: 50 },
  pulseWarningTicks: 18,
  pulseFrontSpeed: 170,
  safeGateRadius: 820,
  boundaryPressureLimit: 26,
}

describe('临界穿越确定性模拟', () => {
  it('与服务端共享同一组固定脉冲计划向量', () => {
    expect(buildPulsePlan(3_000_000_005, 5, CALIBRATION)).toEqual([
      { kind: 'cross', xGate: 6_728, yGate: 4_303 },
      { kind: 'horizontal', xGate: 3_106, yGate: 4_276 },
      { kind: 'vertical', xGate: 6_748, yGate: 2_295 },
      { kind: 'horizontal', xGate: 6_704, yGate: 2_147 },
      { kind: 'vertical', xGate: 6_540, yGate: 4_350 },
    ])
  })

  it('按档位配比生成脉冲，且相邻类型不会重复', () => {
    for (const [count, profile] of [
      [5, CALIBRATION],
      [8, OVERLOAD],
      [10, CRITICAL],
    ] as const) {
      for (let seed = 1; seed <= 256; seed += 1) {
        const sequence = pulseSequence(seed, count, profile.pulseWeights)
        expect(sequence).toHaveLength(count)
        expect(sequence.every((kind, index) => (
          index === 0 || kind !== sequence[index - 1]
        ))).toBe(true)
      }
    }
  })

  it('先显示预警，再让带安全缺口的首轮脉冲进入场地', () => {
    const plan = buildPulsePlan(162_944_417, 5, CALIBRATION)
    expect(pulseFronts(plan, CALIBRATION.pulseWarningTicks - 1, CALIBRATION))
      .toEqual([])

    const fronts = pulseFronts(plan, CALIBRATION.pulseWarningTicks, CALIBRATION)
    expect(fronts.map(front => front.side)).toEqual(['top', 'bottom'])
    expect(fronts.every(front => front.gate === plan[0]!.xGate)).toBe(true)
    expect(fronts.map(front => front.position)).toEqual([
      585 + CALIBRATION.pulseFrontSpeed,
      5_915 - CALIBRATION.pulseFrontSpeed,
    ])
  })

  it('每帧根据方向输入移动导航核心并保留边界压力', () => {
    const plan = buildPulsePlan(162_944_417, 5, CALIBRATION)
    const next = advanceCrossingState(
      createCrossingState(),
      INPUT_RIGHT,
      plan,
      CALIBRATION,
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

  it('持续贴边会按当前档位的压力阈值触发边界封锁', () => {
    const result = replayCrossingRun(
      162_944_417,
      Array(durationTicks(5)).fill(INPUT_UP),
      5,
      CALIBRATION,
    )
    expect(result.collisionKind).toBe('boundary')
    expect(result.collisionTick).toBeGreaterThanOrEqual(
      CALIBRATION.boundaryPressureLimit,
    )
    expect(result.tick).toBeLessThan(durationTicks(5))
  })

  it('离开边缘后压力逐帧消退', () => {
    const plan = buildPulsePlan(42, 5, CALIBRATION)
    let state = createCrossingState()
    state = {
      ...state,
      playerX: 500,
      boundaryPressure: { ...state.boundaryPressure, left: 20 },
    }
    state = advanceCrossingState(state, INPUT_RIGHT, plan, CALIBRATION)
    expect(state.boundaryPressure.left).toBe(21)

    state = { ...state, playerX: 2_000 }
    state = advanceCrossingState(state, 0, plan, CALIBRATION)
    expect(state.boundaryPressure.left).toBe(20)
  })

  it.each([
    [5, CALIBRATION],
    [8, OVERLOAD],
    [10, CRITICAL],
  ] as const)('批量种子都有可验证的 %s 秒安全路线', (seconds, profile) => {
    for (let seed = 1; seed <= 256; seed += 1) {
      const result = replayCrossingRun(
        seed,
        buildSafeRoute(seed, seconds, profile),
        seconds,
        profile,
      )
      expect(result.collisionKind).toBeNull()
      expect(result.tick).toBe(durationTicks(seconds))
    }
  })
})
