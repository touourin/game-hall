import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import GomokuBoard from './GomokuBoard.vue'

function snapshot(
  game: Partial<{
    turnPlayerId: string | null
    winRule: 'freestyle' | 'exact_five' | 'renju'
    forbiddenPoints: Array<{ row: number; column: number; reason: string }>
    openingMove: { row: number; column: number } | null
    lastMove: { pass?: boolean; seat?: number } | null
    consecutivePasses: number
    swap2: {
      enabled: boolean
      stage: 'place_three' | 'second_choice' | 'place_two' | 'first_choice' | null
      actorPlayerId: string | null
      initialPlayerId: string
      expectedColor: 'black' | 'white' | null
      resolved: boolean
    }
    clock: {
      limitMs: number
      remainingMs: Record<string, number>
      activePlayerId: string | null
      serverNowMs: number
    } | null
  }> = {},
): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'TEST',
    gameKey: 'gomoku',
    gameName: '五子棋',
    options: { winRule: 'renju' },
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', name: '玩家一', seat: 0 },
    players: [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '玩家二', seat: 1, connected: true, isHost: false },
    ],
    requiredPlayers: 2,
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
      canRequestUndo: true,
      canRequestDraw: true,
      canResolveRequest: false,
    },
    rematchReadyPlayerIds: [],
    request: null,
    chat: { maxLength: 300, messages: [] },
    game: {
      board: Array.from({ length: 15 }, () => Array<number>(15).fill(0)),
      turnPlayerId: 'p1',
      lastMove: null,
      colors: { p1: 'black', p2: 'white' },
      winRule: 'renju',
      forbiddenPoints: [],
      openingMove: null,
      consecutivePasses: 0,
      swap2: {
        enabled: false,
        stage: null,
        actorPlayerId: 'p1',
        initialPlayerId: 'p1',
        expectedColor: null,
        resolved: true,
      },
      clock: null,
      ...game,
    },
  }
}

function pointAt(wrapper: ReturnType<typeof mount>, row: number, column: number) {
  return wrapper.findAll('.board-point')[row * 15 + column]
}

describe('GomokuBoard', () => {
  it('previews a touch move before submitting it on the second tap', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(GomokuBoard, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })
    const point = pointAt(wrapper, 7, 7)
    const touchClick = () => {
      const event = new MouseEvent('click', { bubbles: true, cancelable: true })
      Object.defineProperty(event, 'pointerType', { value: 'touch' })
      point?.element.dispatchEvent(event)
    }

    touchClick()
    await nextTick()

    expect(action).not.toHaveBeenCalled()
    expect(point?.find('.stone-preview').classes()).toContain('active')
    expect(wrapper.get('.gomoku-board-hint').text()).toContain('再轻点一次确认')

    touchClick()
    await nextTick()

    expect(action).toHaveBeenCalledWith('place', { row: 7, column: 7 })
  })

  it('marks forbidden points, explains them, and does not submit the move', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(GomokuBoard, {
      props: {
        snapshot: snapshot({
          forbiddenPoints: [{ row: 7, column: 7, reason: '三三' }],
        }),
      },
      global: { plugins: [pinia] },
    })

    const forbidden = pointAt(wrapper, 7, 7)
    expect(forbidden?.find('.forbidden-mark').text()).toBe('×')
    expect(forbidden?.attributes('aria-label')).toContain('三三禁手')

    await forbidden?.trigger('click')

    expect(wrapper.get('[role="status"]').text()).toContain('三三禁手')
    expect(action).not.toHaveBeenCalled()

    await pointAt(wrapper, 0, 0)?.trigger('click')
    expect(action).toHaveBeenCalledWith('place', { row: 0, column: 0 })
  })

  it('guides the first black move to the center point', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(GomokuBoard, {
      props: {
        snapshot: snapshot({ openingMove: { row: 7, column: 7 } }),
      },
      global: { plugins: [pinia] },
    })

    expect(pointAt(wrapper, 7, 7)?.find('.opening-mark').exists()).toBe(true)

    await pointAt(wrapper, 0, 0)?.trigger('click')
    expect(wrapper.get('[role="status"]').text()).toContain('首手必须落在棋盘中心')
    expect(action).not.toHaveBeenCalled()

    await pointAt(wrapper, 7, 7)?.trigger('click')
    expect(action).toHaveBeenCalledWith('place', { row: 7, column: 7 })
  })

  it('shows the Swap2 choices and blocks board moves while choosing', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(GomokuBoard, {
      props: {
        snapshot: snapshot({
          swap2: {
            enabled: true,
            stage: 'second_choice',
            actorPlayerId: 'p1',
            initialPlayerId: 'p2',
            expectedColor: null,
            resolved: false,
          },
        }),
      },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('双方颜色尚未最终确定')
    expect(
      wrapper.findAll('.board-point').every(
        (point) => point.attributes('disabled') !== undefined,
      ),
    ).toBe(true)

    const addTwo = wrapper
      .findAll('.swap2-choice-panel button')
      .find((button) => button.text().includes('再摆两子'))
    await addTwo?.trigger('click')
    expect(action).toHaveBeenCalledWith('swap2_choose', { choice: 'add' })
  })

  it('shows clocks and allows a normal turn to pass', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(GomokuBoard, {
      props: {
        snapshot: snapshot({
          lastMove: { pass: true, seat: 1 },
          consecutivePasses: 1,
          clock: {
            limitMs: 180_000,
            remainingMs: { p1: 90_000, p2: 120_000 },
            activePlayerId: 'p1',
            serverNowMs: Date.now(),
          },
        }),
      },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('1:30')
    expect(wrapper.text()).toContain('你若也停一手则本局和棋')
    await wrapper.get('.gomoku-pass-button').trigger('click')
    expect(action).toHaveBeenCalledWith('pass')
  })
})
