import { createPinia } from 'pinia'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import ReactionTest from './ReactionTest.vue'

function snapshot(phase: 'playing' | 'finished' = 'playing'): ArcadeSnapshot {
  const finished = phase === 'finished'
  return {
    revision: finished ? 5 : 2,
    roomCode: 'SOLO',
    gameKey: 'reaction',
    gameName: '反应时间',
    options: {},
    phase,
    hostId: 'p1',
    self: { id: 'p1', name: '测试者', seat: 0 },
    players: [{ id: 'p1', name: '测试者', seat: 0, connected: true, isHost: true }],
    requiredPlayers: 1,
    roundNumber: 1,
    winner: finished ? 'completed' : null,
    winnerPlayerIds: finished ? ['p1'] : [],
    winReason: finished ? '三轮平均反应时间 210 毫秒' : null,
    actions: {
      canStart: false,
      canRestart: finished,
      canAct: !finished,
      canKickPlayers: false,
      canDissolve: false,
      canEditRules: false,
      canRequestUndo: false,
      canRequestDraw: false,
      canResolveRequest: false,
    },
    rematchReadyPlayerIds: [],
    request: null,
    chat: { maxLength: 300, messages: [] },
    game: {
      roundsRequired: 3,
      resultsMs: finished ? [180, 240, 210] : [],
      roundNumber: finished ? 3 : 1,
      bestMs: finished ? 180 : null,
      averageMs: finished ? 210 : null,
    },
  }
}

describe('ReactionTest', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((callback) =>
      window.setTimeout(() => callback(performance.now()), 16),
    )
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation((frameId) =>
      window.clearTimeout(frameId),
    )
    vi.spyOn(window.crypto, 'getRandomValues').mockImplementation((array) => {
      if (array instanceof Uint32Array) array[0] = 0
      return array
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('records the elapsed time after the signal turns ready', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(ReactionTest, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    wrapper.get('.reaction-trigger').element.dispatchEvent(
      new MouseEvent('pointerdown', { bubbles: true, button: 0 }),
    )
    await nextTick()
    wrapper.get('.reaction-trigger').element.dispatchEvent(
      new MouseEvent('click', { bubbles: true, detail: 1 }),
    )
    await nextTick()
    expect(wrapper.get('.reaction-trigger').classes()).toContain('waiting')
    await vi.advanceTimersByTimeAsync(1_516)
    expect(wrapper.get('.reaction-trigger').classes()).toContain('ready')
    await vi.advanceTimersByTimeAsync(236)
    wrapper.get('.reaction-trigger').element.dispatchEvent(
      new MouseEvent('pointerdown', { bubbles: true, button: 0 }),
    )
    await nextTick()

    expect(action).toHaveBeenCalledWith('record', { elapsedMs: 236 })
    wrapper.unmount()
  })

  it('treats input before the color change as a false start', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(ReactionTest, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    wrapper.get('.reaction-trigger').element.dispatchEvent(
      new MouseEvent('pointerdown', { bubbles: true, button: 0 }),
    )
    await nextTick()
    wrapper.get('.reaction-trigger').element.dispatchEvent(
      new MouseEvent('pointerdown', { bubbles: true, button: 0 }),
    )
    await nextTick()

    expect(wrapper.text()).toContain('抢跑了')
    expect(wrapper.text()).toContain('三轮已重新开始')
    expect(action).toHaveBeenCalledWith('false_start')
    wrapper.unmount()
  })

  it('shows all three results and can restart', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const restart = vi.spyOn(arcade, 'restartGame').mockResolvedValue(true)
    const wrapper = mount(ReactionTest, {
      props: { snapshot: snapshot('finished') },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('210 ms')
    expect(wrapper.text()).toContain('180 ms')
    await wrapper.get('.reaction-result .primary-button').trigger('click')
    expect(restart).toHaveBeenCalledOnce()
    wrapper.unmount()
  })
})
