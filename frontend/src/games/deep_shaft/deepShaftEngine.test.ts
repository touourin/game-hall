import { describe, expect, it } from 'vitest'
import {
  MAX_TICKS,
  TARGET_FLOOR,
  advanceShaftState,
  createShaftState,
  generatePlatforms,
  replayShaftRun,
} from './deepShaftEngine'

describe('百层深井固定步长规则', () => {
  it('相同种子生成一致、相邻可达且尖刺留有恢复间隔的平台', () => {
    for (let seed = 1; seed <= 100; seed += 1) {
      const platforms = generatePlatforms(seed)
      expect(platforms).toEqual(generatePlatforms(seed))
      expect(platforms[TARGET_FLOOR]?.kind).toBe('normal')
      for (let index = 1; index < platforms.length; index += 1) {
        const current = platforms[index - 1]!
        const following = platforms[index]!
        expect(current.x).toBeLessThan(following.x + following.width)
        expect(following.x).toBeLessThan(current.x + current.width)
      }
      const spikeFloors = platforms
        .filter(platform => platform.kind === 'spikes')
        .map(platform => platform.floor)
      for (let index = 1; index < spikeFloors.length; index += 1) {
        expect(spikeFloors[index]! - spikeFloors[index - 1]!).toBeGreaterThanOrEqual(4)
      }
    }
  })

  it('与服务端保持相同的确定性失败回放', () => {
    const state = replayShaftRun(42, Array(MAX_TICKS).fill(0))

    expect(state.tick).toBe(246)
    expect(state.deepestFloor).toBe(6)
    expect(state.health).toBe(0)
    expect(state.endReason).toBe('health')
    expect(state.playerX).toBe(5_000)
    expect(state.playerY).toBe(4_918)
  })

  it('在最长三分钟处产生可提交的超时结果', () => {
    const state = createShaftState(42)
    state.tick = MAX_TICKS - 1
    state.cameraY = -5_000

    advanceShaftState(state, 0)

    expect(state.tick).toBe(MAX_TICKS)
    expect(state.endReason).toBe('timeout')
  })
})
