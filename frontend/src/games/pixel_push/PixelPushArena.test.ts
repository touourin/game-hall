import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import type { ArcadeSnapshot } from '../../types/arcade'
import { useArcadeStore } from '../../stores/arcade'
import { applyTheme } from '../../theme'
import PixelPushArena from './PixelPushArena.vue'
import PixelPushControls from './PixelPushControls.vue'

class ResizeObserverMock {
  observe() {}
  disconnect() {}
}

function snapshot(spectator = false): ArcadeSnapshot {
  return {
    revision: 4,
    roomCode: 'PUSH',
    gameKey: 'pixel_push',
    gameName: '像素推推王',
    options: { arena: 'rotation', allowGuests: true, allowSpectators: true },
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', accountId: 'a1', name: '青团', seat: 0 },
    viewer: {
      mode: spectator ? 'spectator' : 'player',
      id: spectator ? 'watcher' : 'p1',
      name: spectator ? '观众' : '青团',
      targetPlayerId: 'p1',
    },
    players: [
      { id: 'p1', name: '青团', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '红豆', seat: 1, connected: true, isHost: false },
    ],
    requiredPlayers: 4,
    minimumPlayers: 2,
    roundNumber: 1,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: {
      canStart: false,
      canRestart: false,
      canAct: !spectator,
      canKickPlayers: false,
      canDissolve: false,
      canEditRules: false,
      canRequestUndo: false,
      canRequestDraw: false,
      canRequestEndTable: true,
      canResolveRequest: false,
    },
    rematchReadyPlayerIds: [],
    request: null,
    chat: { maxLength: 300, messages: [] },
    game: {
      tick: 0,
      tickRate: 30,
      stage: 'countdown',
      stageTicksRemaining: 90,
      roundTicksRemaining: 1_350,
      roundNumber: 1,
      roundsToWin: 2,
      currentMap: 'moon_station',
      mapSequence: ['moon_station', 'cross_bridge', 'pulse_factory'],
      shrinkProgress: 0,
      roundWinnerId: null,
      matchWinnerId: null,
      frozen: false,
      world: { width: 10_000, height: 7_000, playerRadius: 330 },
      roundWins: { p1: 0, p2: 0 },
      events: [],
      selfInputSequence: -1,
      players: [
        {
          id: 'p1', name: '青团', seat: 0, color: '#5ce1e6',
          x: 3_100, y: 3_500, vx: 0, vy: 0, facingX: 1_000, facingY: 0,
          balance: 0, alive: true, dashing: false, bracing: false,
          dashCooldownTicks: 0, disconnectTicks: 0, roundWins: 0,
        },
        {
          id: 'p2', name: '红豆', seat: 1, color: '#ff6f91',
          x: 6_900, y: 3_500, vx: 0, vy: 0, facingX: -1_000, facingY: 0,
          balance: 0, alive: true, dashing: false, bracing: false,
          dashCooldownTicks: 0, disconnectTicks: 0, roundWins: 0,
        },
      ],
    },
  }
}

describe('PixelPushArena', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('ResizeObserver', ResizeObserverMock)
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
    vi.spyOn(window, 'requestAnimationFrame').mockReturnValue(1)
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => undefined)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('renders the complete round HUD and sends dedicated realtime input', async () => {
    const arcade = useArcadeStore()
    const sendInput = vi.spyOn(arcade, 'realtimeInput').mockResolvedValue(true)
    const wrapper = mount(PixelPushArena, { props: { snapshot: snapshot() } })

    expect(wrapper.get('.pixel-push-match-header').text()).toContain('月台零号')
    expect(wrapper.findAll('.pixel-push-scoreboard article')).toHaveLength(2)
    expect(wrapper.get('.arena-overlay').text()).toContain('3')
    expect(wrapper.get('.desktop-control-legend').text()).toContain('稳住')

    wrapper.getComponent(PixelPushControls).vm.$emit('mask', 8)
    await wrapper.vm.$nextTick()

    expect(sendInput).toHaveBeenLastCalledWith(1, 8)
    wrapper.unmount()
  })

  it('applies authoritative frames to the timer, balance and score HUD', async () => {
    const arcade = useArcadeStore()
    vi.spyOn(arcade, 'realtimeInput').mockResolvedValue(true)
    const wrapper = mount(PixelPushArena, { props: { snapshot: snapshot() } })
    arcade.realtimeFrame = {
      roomCode: 'PUSH', revision: 22, tick: 330,
      stage: 'active', stageTicksRemaining: 300, roundTicksRemaining: 300,
      roundNumber: 2, currentMap: 'cross_bridge', shrinkProgress: 333,
      roundWinnerId: null, matchWinnerId: null, frozen: false,
      roundWins: { p1: 1, p2: 0 }, events: [],
      players: [
        {
          id: 'p1', x: 4_000, y: 3_500, vx: 20, vy: 0,
          facingX: 1_000, facingY: 0, balance: 72, alive: true,
          dashing: false, bracing: false, dashCooldownTicks: 10,
          disconnectTicks: 0, lastInputSequence: 5,
        },
        {
          id: 'p2', x: 6_000, y: 3_500, vx: -20, vy: 0,
          facingX: -1_000, facingY: 0, balance: 12, alive: true,
          dashing: false, bracing: true, dashCooldownTicks: 0,
          disconnectTicks: 0, lastInputSequence: 2,
        },
      ],
    }
    await wrapper.vm.$nextTick()

    expect(wrapper.get('.pixel-push-match-header').text()).toContain('十字断桥')
    expect(wrapper.get('.round-clock').text()).toContain('10')
    expect(wrapper.findAll('.round-pips .won')).toHaveLength(1)
    expect(wrapper.findAll('.balance-copy')[0]!.text()).toContain('72%')
    wrapper.unmount()
  })

  it('keeps spectators read-only', () => {
    const wrapper = mount(PixelPushArena, {
      props: { snapshot: snapshot(true) },
    })

    expect(wrapper.findComponent(PixelPushControls).exists()).toBe(false)
    expect(wrapper.get('.spectator-badge').text()).toContain('第一人称观战')
    wrapper.unmount()
  })

  it('does not send controller initialization after the match has finished', () => {
    const arcade = useArcadeStore()
    const sendInput = vi.spyOn(arcade, 'realtimeInput').mockResolvedValue(true)
    const finished = snapshot()
    finished.phase = 'finished'
    const wrapper = mount(PixelPushArena, { props: { snapshot: finished } })

    expect(sendInput).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('switches all four visual themes without resetting the live match', async () => {
    applyTheme('emerald')
    const arcade = useArcadeStore()
    const sendInput = vi.spyOn(arcade, 'realtimeInput').mockResolvedValue(true)
    const wrapper = mount(PixelPushArena, { props: { snapshot: snapshot() } })
    sendInput.mockClear()

    applyTheme('midnight')
    await wrapper.vm.$nextTick()
    applyTheme('royal')
    await wrapper.vm.$nextTick()
    applyTheme('amber')
    await wrapper.vm.$nextTick()

    expect(wrapper.get('.pixel-push-match-header').text()).toContain('月台零号')
    expect(wrapper.findAll('.pixel-push-scoreboard article')).toHaveLength(2)
    expect(sendInput).not.toHaveBeenCalled()
    wrapper.unmount()
  })
})

describe('PixelPushControls', () => {
  it('maps keyboard movement, dash and release into one input mask', async () => {
    const wrapper = mount(PixelPushControls, {
      props: { disabled: false, dashReady: true },
    })
    window.dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyW' }))
    window.dispatchEvent(new KeyboardEvent('keydown', { code: 'Space' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('mask')?.at(-1)).toEqual([17])

    window.dispatchEvent(new KeyboardEvent('keyup', { code: 'Space' }))
    window.dispatchEvent(new KeyboardEvent('keyup', { code: 'KeyW' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('mask')?.at(-1)).toEqual([0])
    wrapper.unmount()
  })
})
