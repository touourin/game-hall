import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import TetrisGame from './TetrisGame.vue'

function snapshot(phase: ArcadeSnapshot['phase'] = 'playing'): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'DROP',
    gameKey: 'tetris',
    gameName: '落块挑战',
    options: { allowSpectators: false },
    phase,
    hostId: 'p1',
    self: { id: 'p1', accountId: 'account-1', name: '玩家一', seat: 0 },
    players: [{ id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true }],
    requiredPlayers: 1,
    roundNumber: 1,
    winner: phase === 'finished' ? 'completed' : null,
    winnerPlayerIds: phase === 'finished' ? ['p1'] : [],
    winReason: phase === 'finished' ? '最终得分 12,480 · 消除 24 行' : null,
    actions: {
      canStart: false,
      canRestart: phase === 'finished',
      canAct: phase === 'playing',
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
      score: phase === 'finished' ? 12_480 : 0,
      lines: phase === 'finished' ? 24 : 0,
      level: phase === 'finished' ? 3 : 1,
      pieces: phase === 'finished' ? 82 : 0,
      elapsedMs: phase === 'finished' ? 184_000 : 0,
    },
  }
}

describe('TetrisGame', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.spyOn(Math, 'random').mockReturnValue(0)
    vi.spyOn(window, 'requestAnimationFrame').mockReturnValue(1)
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => undefined)
  })

  afterEach(() => vi.restoreAllMocks())

  it('renders a 10 by 20 board and thumb-friendly mobile controls', () => {
    const wrapper = mount(TetrisGame, {
      props: { snapshot: snapshot() },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.tetris-cell')).toHaveLength(200)
    expect(wrapper.get('.mobile-tetris-controls').text()).toContain('拇指控制器')
    expect(wrapper.get('.hard-drop').text()).toContain('落底')
    expect(wrapper.findAll('.move-controls button')).toHaveLength(2)
    wrapper.unmount()
  })

  it('applies movement and a second-finger rotation as separate actions', async () => {
    const wrapper = mount(TetrisGame, {
      props: { snapshot: snapshot() },
      global: { plugins: [createPinia()] },
    })
    const activeIndices = () => wrapper.findAll('.tetris-cell')
      .map((cell, index) => cell.classes().includes('active') ? index : -1)
      .filter((index) => index >= 0)
    const occupiedBefore = activeIndices()

    const dispatchTouch = (element: Element, pointerId: number, isPrimary: boolean) => {
      const event = new Event('pointerdown', { bubbles: true, cancelable: true })
      Object.defineProperties(event, {
        pointerId: { value: pointerId },
        pointerType: { value: 'touch' },
        isPrimary: { value: isPrimary },
        button: { value: 0 },
      })
      element.dispatchEvent(event)
    }
    dispatchTouch(wrapper.get('.move-controls button').element, 1, true)
    await wrapper.vm.$nextTick()
    const occupiedAfterMove = activeIndices()
    expect(occupiedAfterMove).not.toEqual(occupiedBefore)

    dispatchTouch(wrapper.get('.rotate-main').element, 2, false)
    await wrapper.vm.$nextTick()

    expect(wrapper.findAll('.tetris-cell.active').length).toBeGreaterThan(0)
    expect(activeIndices()).not.toEqual(occupiedAfterMove)
    wrapper.unmount()
  })

  it('keeps an ended run frozen and retryable until score submission succeeds', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'actionWithResult').mockImplementation(async () => {
      arcade.error = '网络暂时不可用'
      return false
    })
    sessionStorage.setItem('game-hall:tetris:DROP', JSON.stringify({
      board: Array.from({ length: 20 }, () => Array(10).fill('T')),
      active: { type: 'T', rotation: 0, x: 3, y: -1 },
      queue: ['I', 'J', 'L', 'O', 'S', 'T', 'Z'],
      held: null,
      holdUsed: false,
      score: 4321,
      lines: 12,
      pieces: 40,
      elapsedMs: 60_000,
      ended: true,
    }))
    const wrapper = mount(TetrisGame, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.get('.tetris-overlay').text()).toContain('重新保存成绩')
    expect(wrapper.get('[aria-label="向左移动"]').attributes()).toHaveProperty('disabled')
    await wrapper.get('.tetris-overlay button').trigger('click')

    expect(action).toHaveBeenCalledWith('finish', {
      score: 4321,
      lines: 12,
      level: 2,
      pieces: 40,
      elapsedMs: 60_000,
    })
    expect(wrapper.get('.tetris-overlay').text()).toContain('网络暂时不可用')
    expect(sessionStorage.getItem('game-hall:tetris:DROP')).toContain('"ended":true')

    action.mockResolvedValueOnce(true)
    await wrapper.get('.tetris-overlay button').trigger('click')
    expect(sessionStorage.getItem('game-hall:tetris:DROP')).toBeNull()
    wrapper.unmount()
    expect(sessionStorage.getItem('game-hall:tetris:DROP')).toBeNull()
  })

  it('shows the shared result card with the server-recorded score', () => {
    const wrapper = mount(TetrisGame, {
      props: { snapshot: snapshot('finished') },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.solo-result-card').text()).toContain('12,480')
    expect(wrapper.get('.solo-result-card').text()).toContain('消除行数')
    expect(wrapper.find('.mobile-tetris-controls').exists()).toBe(false)
    wrapper.unmount()
  })
})
