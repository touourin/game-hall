import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { useArcadeStore } from '../../stores/arcade'
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
    vi.useFakeTimers()
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
    vi.spyOn(window, 'requestAnimationFrame').mockReturnValue(1)
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => undefined)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('提供倒计时、键盘暂停和视口内双拇指控制', async () => {
    const wrapper = mount(DeepShaftGame, {
      props: { snapshot: snapshot() },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.ready-overlay').text()).toContain('准备下潜')
    expect(wrapper.findAll('.shaft-console .shaft-controls button')).toHaveLength(2)
    expect(wrapper.get('.shaft-instruments').text()).toContain('垂直观测仪')
    window.dispatchEvent(new KeyboardEvent('keydown', { code: 'ArrowLeft' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.ready-overlay').exists()).toBe(false)
    expect(wrapper.get('.countdown-overlay').text()).toContain('3')
    await vi.advanceTimersByTimeAsync(2_700)
    await wrapper.vm.$nextTick()

    expect(wrapper.get('.pause-button').text()).toContain('暂停')
    await wrapper.get('.pause-button').trigger('click')
    expect(wrapper.get('.shaft-overlay').text()).toContain('探测暂停')
    wrapper.unmount()
  })

  it('renders the watched player local simulation as a read-only view', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const watched = snapshot()
    watched.viewer = {
      mode: 'spectator',
      id: 'watcher-1',
      name: '观众',
      targetPlayerId: 'p1',
    }
    watched.actions.canAct = false
    const wrapper = mount(DeepShaftGame, {
      props: { snapshot: watched },
      global: { plugins: [pinia] },
    })

    arcade.spectatorFrame = {
      roomCode: 'DOWN',
      gameKey: 'deep_shaft',
      roundNumber: 1,
      targetPlayerId: 'p1',
      sequence: 1,
      state: {
        phase: 'playing',
        countdown: 1,
        shaftState: {
          seed: 42,
          tick: 600,
          playerX: 5_000,
          playerY: 12_000,
          velocityX: 0,
          velocityY: 12,
          cameraY: 10_000,
          health: 7,
          deepestFloor: 42,
          groundedFloor: null,
          endReason: null,
          visitedFloors: [0, 42],
          crumbleDue: [],
          brokenFloors: [],
          ceilingCooldown: 0,
          lastLandedKind: 'normal',
        },
      },
    }
    await wrapper.vm.$nextTick()

    expect(wrapper.get('.depth-instrument').text()).toContain('42')
    expect(wrapper.get('.pause-button').attributes()).toHaveProperty('disabled')
    expect(wrapper.find('.ready-overlay').exists()).toBe(false)
    wrapper.unmount()
  })
})
