import { describe, expect, it } from 'vitest'
import {
  INPUT_RIGHT,
  INPUT_UP,
  advanceCrossingState,
  boundaryCollision,
  buildPulsePlan,
  buildSafeRoute,
  createCrossingState,
  durationTicks,
  pulseFronts,
  replayCrossingRun,
  updateBoundaryPressure,
  type CrossingProfile,
} from './crossingEngine'

const CALIBRATION: CrossingProfile = {
  pulseWarningTicks: 28,
  pulseFrontSpeed: 180,
  safeGateRadius: 1_050,
  boundaryPressureLimit: 36,
}

const OVERLOAD: CrossingProfile = {
  pulseWarningTicks: 23,
  pulseFrontSpeed: 175,
  safeGateRadius: 920,
  boundaryPressureLimit: 30,
}

const CRITICAL: CrossingProfile = {
  pulseWarningTicks: 18,
  pulseFrontSpeed: 170,
  safeGateRadius: 820,
  boundaryPressureLimit: 26,
}

describe('临界穿越确定性模拟', () => {
  it('与服务端共享同一组固定脉冲计划向量', () => {
    expect(buildPulsePlan(3_000_000_005, 5)).toEqual([
      { xGate: 6_728, yGate: 4_303 },
      { xGate: 3_106, yGate: 4_276 },
      { xGate: 6_748, yGate: 2_295 },
      { xGate: 6_704, yGate: 2_147 },
      { xGate: 6_540, yGate: 4_350 },
    ])
  })

  it('随机安全交点覆盖棋盘四个象限', () => {
    const quadrants = [0, 0, 0, 0]
    for (let seed = 1; seed <= 1_024; seed += 1) {
      for (const pulse of buildPulsePlan(seed, 10)) {
        const quadrant = Number(pulse.xGate > 5_000) * 2
          + Number(pulse.yGate > 3_250)
        quadrants[quadrant]! += 1
      }
    }
    expect(quadrants.every(count => count > 2_300 && count < 2_800)).toBe(true)
  })

  it('先显示预警，再让带安全缺口的首轮脉冲进入场地', () => {
    const plan = buildPulsePlan(162_944_417, 5)
    expect(pulseFronts(plan, CALIBRATION.pulseWarningTicks - 1, CALIBRATION))
      .toEqual([])

    const fronts = pulseFronts(plan, CALIBRATION.pulseWarningTicks, CALIBRATION)
    expect(fronts.map(front => front.side)).toEqual([
      'top',
      'right',
      'bottom',
      'left',
    ])
    expect(fronts.map(front => front.gate)).toEqual([
      plan[0]!.xGate,
      plan[0]!.yGate,
      plan[0]!.xGate,
      plan[0]!.yGate,
    ])
    expect(fronts.map(front => front.position)).toEqual([
      585 + CALIBRATION.pulseFrontSpeed,
      9_100 - CALIBRATION.pulseFrontSpeed,
      5_915 - CALIBRATION.pulseFrontSpeed,
      900 + CALIBRATION.pulseFrontSpeed,
    ])
  })

  it('每帧根据方向输入移动导航核心并保留边界压力', () => {
    const plan = buildPulsePlan(162_944_417, 5)
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
    let pressure = { top: 0, right: 0, bottom: 0, left: 0 }
    for (let tick = 0; tick < CALIBRATION.boundaryPressureLimit; tick += 1) {
      pressure = updateBoundaryPressure(pressure, 105, 3_250, CALIBRATION)
    }
    expect(boundaryCollision(105, 3_250, pressure, CALIBRATION)).toBe(false)

    pressure = updateBoundaryPressure(pressure, 105, 3_250, CALIBRATION)
    expect(boundaryCollision(105, 3_250, pressure, CALIBRATION)).toBe(true)
  })

  it('离开边缘后压力逐帧消退', () => {
    const plan = buildPulsePlan(42, 5)
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
