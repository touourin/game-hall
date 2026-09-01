import { describe, expect, it } from 'vitest'
import {
  DEFAULT_CROSSING_PROFILE,
  INPUT_DOWN,
  INPUT_LEFT,
  INPUT_RIGHT,
  INPUT_UP,
  advanceCrossingState,
  buildCoursePlan,
  buildSafeRoute,
  createCrossingState,
  durationTicks,
  replayCrossingRun,
  runnerDistanceMeters,
  runnerLanePosition,
  type CourseSection,
} from './crossingEngine'

describe('算途疾行确定性跑酷模拟', () => {
  it('与服务端共享同一组固定云桥计划向量', () => {
    expect(buildCoursePlan(3_000_000_005, 5)).toEqual([
      {
        impactTick: 50,
        branchCount: 2,
        activeLanes: [0, 1],
        obstacles: ['gap', 'barrier', 'ground'],
        safeLane: 1,
      },
      {
        impactTick: 110,
        branchCount: 3,
        activeLanes: [-1, 0, 1],
        obstacles: ['barrier', 'overhead', 'barrier'],
        safeLane: 0,
      },
      {
        impactTick: 170,
        branchCount: 3,
        activeLanes: [-1, 0, 1],
        obstacles: ['clear', 'barrier', 'barrier'],
        safeLane: -1,
      },
      {
        impactTick: 230,
        branchCount: 2,
        activeLanes: [0, 1],
        obstacles: ['gap', 'barrier', 'ground'],
        safeLane: 1,
      },
      {
        impactTick: 290,
        branchCount: 3,
        activeLanes: [-1, 0, 1],
        obstacles: ['overhead', 'barrier', 'barrier'],
        safeLane: -1,
      },
    ])
  })

  it('每条短赛道都混合两路与三路分叉，并覆盖上下障碍', () => {
    for (let seed = 1; seed <= 256; seed += 1) {
      const plan = buildCoursePlan(seed, 5)
      expect(new Set(plan.map(section => section.branchCount))).toEqual(
        new Set([2, 3]),
      )
      const obstacles = plan.flatMap(section => section.obstacles)
      expect(obstacles).toContain('ground')
      expect(obstacles).toContain('overhead')
    }
  })

  it('A/D 按键以按下沿变道，长按不会连续跨越多条跑道', () => {
    const plan = buildCoursePlan(42, 5)
    let state = advanceCrossingState(
      createCrossingState(),
      INPUT_RIGHT,
      plan,
    )
    expect(state.lane).toBe(1)
    state = advanceCrossingState(state, INPUT_RIGHT, plan)
    expect(runnerLanePosition(state)).toBeGreaterThan(0)
    expect(runnerLanePosition(state)).toBeLessThan(1)

    expect(state.lane).toBe(1)
    state = advanceCrossingState(state, 0, plan)
    state = advanceCrossingState(state, INPUT_LEFT, plan)
    expect(state.lane).toBe(0)
  })

  it('W 跳过地面障碍，S 下蹲避开上方障碍', () => {
    const ground: CourseSection = {
      impactTick: 1,
      branchCount: 3,
      activeLanes: [-1, 0, 1],
      obstacles: ['barrier', 'ground', 'barrier'],
      safeLane: 0,
    }
    expect(advanceCrossingState(
      createCrossingState(),
      INPUT_UP,
      [ground],
    ).collisionKind).toBeNull()
    expect(advanceCrossingState(
      createCrossingState(),
      0,
      [ground],
    ).collisionKind).toBe('ground')

    const overhead: CourseSection = {
      ...ground,
      obstacles: ['barrier', 'overhead', 'barrier'],
    }
    expect(advanceCrossingState(
      createCrossingState(),
      INPUT_DOWN,
      [overhead],
    ).collisionKind).toBeNull()
    expect(advanceCrossingState(
      createCrossingState(),
      INPUT_UP,
      [overhead],
    ).collisionKind).toBe('overhead')
  })

  it('驶入未连接的分叉会判定为断桥碰撞', () => {
    const gap: CourseSection = {
      impactTick: 1,
      branchCount: 2,
      activeLanes: [-1, 1],
      obstacles: ['clear', 'gap', 'clear'],
      safeLane: -1,
    }
    const state = advanceCrossingState(createCrossingState(), 0, [gap])
    expect(state.collisionKind).toBe('gap')
    expect(state.collisionTick).toBe(1)
  })

  it.each([5, 8, 10])('批量种子都有可验证的 %s 秒安全路线', (seconds) => {
    for (let seed = 1; seed <= 1_000; seed += 1) {
      const result = replayCrossingRun(
        seed,
        buildSafeRoute(seed, seconds),
        seconds,
      )
      expect(result.collisionKind).toBeNull()
      expect(result.tick).toBe(durationTicks(seconds))
      expect(result.passedSections).toBe(seconds)
    }
  })

  it('人物按固定速度自动向前，方向键不再控制平面上下坐标', () => {
    const result = replayCrossingRun(
      3_000_000_005,
      buildSafeRoute(3_000_000_005, 5),
      5,
      DEFAULT_CROSSING_PROFILE,
    )
    expect(runnerDistanceMeters(result.tick)).toBe(90)
  })
})
