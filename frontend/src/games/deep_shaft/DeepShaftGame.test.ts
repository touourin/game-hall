import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import type { ArcadeSnapshot } from '../../types/arcade'
import DeepShaftGame from './DeepShaftGame.vue'

function snapshot(): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'DOWN',
    gameKey: 'deep_shaft',
    gameName: '百层深井',
    options: { allowSpectators: false },
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', accountId: 'account-1', name: '玩家一', seat: 0 },
    players: [{ id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true }],
    requiredPlayers: 1,
    roundNumber: 1,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: {
      canStart: false,
      canRestart: false,
      canAct: true,
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
      seed: 42,
      targetFloor: 100,
      tickRate: 60,
      maxHealth: 10,
      deepestFloor: 0,
      health: 10,
      elapsedMs: 0,
      endReason: null,
    },
  }
}

describe('DeepShaftGame', () => {
  beforeEach(() => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
    vi.spyOn(window, 'requestAnimationFrame').mockReturnValue(1)
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => undefined)
  })

  afterEach(() => vi.restoreAllMocks())

  it('提供键盘启动、暂停和双拇指左右控制', async () => {
    const wrapper = mount(DeepShaftGame, {
      props: { snapshot: snapshot() },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.ready-overlay').text()).toContain('方向键 / A D')
    expect(wrapper.findAll('.shaft-controls button')).toHaveLength(2)
    window.dispatchEvent(new KeyboardEvent('keydown', { code: 'ArrowLeft' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.ready-overlay').exists()).toBe(false)
    expect(wrapper.get('.pause-button').text()).toContain('暂停')
    await wrapper.get('.pause-button').trigger('click')
    expect(wrapper.get('.shaft-overlay').text()).toContain('挑战暂停')
    wrapper.unmount()
  })
})
