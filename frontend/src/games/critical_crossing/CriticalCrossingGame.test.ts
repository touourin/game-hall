import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import CriticalCrossingGame from './CriticalCrossingGame.vue'

function spectatorSnapshot(): ArcadeSnapshot {
  return {
    revision: 2,
    roomCode: 'GATE',
    gameKey: 'critical_crossing',
    gameName: '临界穿越',
    options: { difficulty: '5s', allowSpectators: true },
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', name: '挑战者', seat: 0 },
    viewer: {
      mode: 'spectator',
      id: 'watcher-1',
      name: '观众',
      targetPlayerId: 'p1',
    },
    players: [{
      id: 'p1',
      name: '挑战者',
      seat: 0,
      connected: true,
      isHost: true,
    }],
    requiredPlayers: 1,
    roundNumber: 1,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: {
      canStart: false,
      canRestart: false,
      canAct: false,
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
      difficulty: '5s',
      difficultyLabel: '校准',
      seed: 42,
      durationMs: 5_000,
      tickRate: 60,
      pulseCount: 5,
      collisionGraceMs: 367,
      pulseWarningMs: 367,
      boundaryPressureMs: 500,
      elapsedMs: 0,
      crossed: null,
      collisionTick: null,
      collisionKind: null,
    },
  }
}

describe('CriticalCrossingGame spectator view', () => {
  beforeEach(() => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
    vi.spyOn(window, 'requestAnimationFrame').mockReturnValue(1)
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => undefined)
  })

  afterEach(() => vi.restoreAllMocks())

  it('renders the target local frame without accepting movement', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const wrapper = mount(CriticalCrossingGame, {
      props: { snapshot: spectatorSnapshot() },
      global: { plugins: [pinia] },
    })

    arcade.spectatorFrame = {
      roomCode: 'GATE',
      gameKey: 'critical_crossing',
      roundNumber: 1,
      targetPlayerId: 'p1',
      sequence: 1,
      state: {
        phase: 'playing',
        readyCount: 1,
        localElapsedMs: 2_000,
        crossingState: {
          tick: 120,
          playerX: 6_200,
          playerY: 3_100,
          boundaryPressure: { top: 0, right: 0, bottom: 0, left: 0 },
          collisionTick: null,
          collisionKind: null,
        },
      },
    }
    await wrapper.vm.$nextTick()

    expect(wrapper.get('.arena-timer').text()).toContain('3.00')
    for (const button of wrapper.findAll('.crossing-controls button')) {
      expect(button.attributes()).toHaveProperty('disabled')
    }
    wrapper.unmount()
  })
})
