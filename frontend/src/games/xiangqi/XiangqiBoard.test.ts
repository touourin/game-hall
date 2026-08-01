import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import XiangqiBoard from './XiangqiBoard.vue'

function snapshot(turnPlayerId: string): ArcadeSnapshot {
  const board = Array.from({ length: 10 }, () =>
    Array<string | null>(9).fill(null),
  )
  board[9][4] = 'rK'
  return {
    revision: 1,
    roomCode: 'TEST',
    gameKey: 'xiangqi',
    gameName: '中国象棋',
    options: {},
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
      canRequestUndo: false,
      canRequestDraw: true,
      canResolveRequest: false,
    },
    rematchReadyPlayerIds: [],
    request: null,
    chat: { maxLength: 300, messages: [] },
    game: {
      board,
      turnPlayerId,
      colors: { p1: 'red', p2: 'black' },
      viewerColor: 'red',
      lastMove: null,
      moveHistory: [],
      capturedPieces: [],
      legalMoves: [
        { fromRow: 9, fromColumn: 4, toRow: 8, toColumn: 4 },
      ],
      redInCheck: false,
      blackInCheck: false,
      checkedColor: null,
    },
  }
}

describe('XiangqiBoard', () => {
  it('visibly selects a piece, supports cancelling, and shows board details', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(XiangqiBoard, {
      props: { snapshot: snapshot('p1') },
      global: { plugins: [pinia] },
    })
    const king = wrapper.findAll('.xiangqi-cell')[9 * 9 + 4]

    expect(wrapper.find('.palace-lines').exists()).toBe(true)
    expect(wrapper.findAll('.river-bank-top')).toHaveLength(9)
    await king?.trigger('click')

    expect(king?.classes()).toContain('selected')
    expect(king?.find('.xiangqi-piece').exists()).toBe(true)
    expect(wrapper.text()).toContain('已选帅 · 请选择落点')

    await king?.trigger('click')
    expect(king?.classes()).not.toContain('selected')
    expect(action).not.toHaveBeenCalled()
  })

  it('disables the whole board while waiting for the opponent', async () => {
    const wrapper = mount(XiangqiBoard, {
      props: { snapshot: snapshot('p2') },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.xiangqi-cell')).toHaveLength(90)
    expect(
      wrapper.findAll('.xiangqi-cell').every((cell) => cell.attributes('disabled') !== undefined),
    ).toBe(true)

    await wrapper.setProps({ snapshot: snapshot('p1') })
    expect(
      wrapper.findAll('.xiangqi-cell').every((cell) => cell.attributes('disabled') === undefined),
    ).toBe(true)
  })

  it('shows legal targets and submits only a legal move', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(XiangqiBoard, {
      props: { snapshot: snapshot('p1') },
      global: { plugins: [pinia] },
    })

    const cells = wrapper.findAll('.xiangqi-cell')
    await cells[9 * 9 + 4]?.trigger('click')
    expect(cells[8 * 9 + 4]?.classes()).toContain('legal')
    await cells[8 * 9 + 4]?.trigger('click')
    expect(action).toHaveBeenCalledWith('move', {
      fromRow: 9,
      fromColumn: 4,
      toRow: 8,
      toColumn: 4,
    })
  })

  it('shows the checked side, captured pieces, and coordinate replay', async () => {
    const current = snapshot('p2')
    current.game = {
      ...(current.game as Record<string, unknown>),
      checkedColor: 'black',
      capturedPieces: [{ piece: 'bP', capturedBy: 'red', moveNumber: 1 }],
      moveHistory: [{
        number: 1,
        fromRow: 6,
        fromColumn: 0,
        toRow: 5,
        toColumn: 0,
        piece: 'rP',
        captured: 'bP',
        color: 'red',
        gaveCheck: false,
      }],
    }
    const wrapper = mount(XiangqiBoard, {
      props: { snapshot: current },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('黑方被将军')
    expect(wrapper.text()).toContain('黑方被吃卒')
    await wrapper.findAll('.xiangqi-actions button')[0]?.trigger('click')
    expect(wrapper.text()).toContain('走棋记录')
    expect(wrapper.text()).toContain('兵 (7,1) → (6,1)')
    expect(wrapper.text()).not.toContain('中文棋谱')
  })
})
