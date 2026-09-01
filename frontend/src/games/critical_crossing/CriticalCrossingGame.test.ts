import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import CriticalCrossingGame from './CriticalCrossingGame.vue'

function spectatorSnapshot(): ArcadeSnapshot {
  return {
    revision: 2,
    roomCode: 'GATE',
    gameKey: 'critical_crossing',
    gameName: '算途疾行',
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
      sectionCount: 5,
      profile: {
        sectionIntervalTicks: 60,
        firstSectionTick: 50,
        laneChangeTicks: 12,
        jumpDurationTicks: 42,
        slideDurationTicks: 36,
        forwardMetersPerSecond: 18,
      },
      elapsedMs: 0,
      distanceMeters: 0,
      passedSections: 0,
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
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', name: 'hall', component: { template: '<div />' } }],
    })
    await router.push('/')
    await router.isReady()
    const wrapper = mount(CriticalCrossingGame, {
      props: { snapshot: spectatorSnapshot() },
      global: { plugins: [pinia, router] },
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
          lane: 1,
          laneChangeFrom: 0,
          laneChangeTicks: 0,
          pose: 'run',
          poseTicks: 0,
          previousInputMask: 0,
          passedSections: 2,
          collisionTick: null,
          collisionKind: null,
        },
      },
    }
    await wrapper.vm.$nextTick()

    expect(wrapper.get('.arena-timer').text()).toContain('3.00')
    expect(wrapper.get('.return-main').text()).toContain('返回主界面')
    for (const button of wrapper.findAll('.runner-controls button')) {
      expect(button.attributes()).toHaveProperty('disabled')
    }
    wrapper.unmount()
  })
})
