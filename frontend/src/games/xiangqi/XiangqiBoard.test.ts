import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import XiangqiBoard from './XiangqiBoard.vue'

interface TestXiangqiGame {
  board: Array<Array<string | null>>
  legalMoves: Array<{
    fromRow: number
    fromColumn: number
    toRow: number
    toColumn: number
  }>
}

function snapshot(
  turnPlayerId: string,
  captureHintsEnabled = true,
): ArcadeSnapshot {
  const board = Array.from({ length: 10 }, () =>
    Array<string | null>(9).fill(null),
  )
  board[9][4] = 'rK'
  return {
    revision: 1,
    roomCode: 'TEST',
    gameKey: 'xiangqi',
    gameName: '中国象棋',
    options: { captureHintsEnabled },
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

    expect(wrapper.find('.xiangqi-lines').exists()).toBe(true)
    expect(wrapper.find('.palace-lines').exists()).toBe(true)
    expect(wrapper.find('.xiangqi-grid').exists()).toBe(true)
    expect(wrapper.findAll('.xiangqi-position-mark')).toHaveLength(24)
    expect(wrapper.findAll('[data-position="3-0"]')).toHaveLength(1)
    expect(wrapper.findAll('[data-position="3-4"]')).toHaveLength(2)
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

  it('shows every current capture target only when the room reminder is enabled', async () => {
    const enabled = snapshot('p1')
    const enabledGame = enabled.game as unknown as TestXiangqiGame
    enabledGame.board[8][4] = 'bP'
    const enabledWrapper = mount(XiangqiBoard, {
      props: { snapshot: enabled },
      global: { plugins: [createPinia()] },
    })

    const target = enabledWrapper.findAll('.xiangqi-cell')[8 * 9 + 4]
    expect(target?.classes()).toContain('capture-reminder')
    expect(target?.attributes('aria-label')).toContain('可吃卒')
    expect(enabledWrapper.text()).toContain('吃子提醒：有 1 个敌子可吃（卒）')

    const disabled = snapshot('p1', false)
    const disabledGame = disabled.game as unknown as TestXiangqiGame
    disabledGame.board[8][4] = 'bP'
    const disabledWrapper = mount(XiangqiBoard, {
      props: { snapshot: disabled },
      global: { plugins: [createPinia()] },
    })
    const disabledTarget = disabledWrapper.findAll('.xiangqi-cell')[8 * 9 + 4]

    expect(disabledTarget?.classes()).not.toContain('capture-reminder')
    expect(disabledWrapper.text()).not.toContain('吃子提醒：')

    await disabledWrapper.findAll('.xiangqi-cell')[9 * 9 + 4]?.trigger('click')
    expect(disabledTarget?.classes()).toContain('legal')
    expect(disabledTarget?.classes()).not.toContain('capture')
  })

  it('previews a touch destination before submitting it on the second tap', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(XiangqiBoard, {
      props: { snapshot: snapshot('p1') },
      global: { plugins: [pinia] },
    })
    const cells = wrapper.findAll('.xiangqi-cell')
    const source = cells[9 * 9 + 4]
    const target = cells[8 * 9 + 4]
    const touchTarget = () => {
      const event = new MouseEvent('click', { bubbles: true, cancelable: true })
      Object.defineProperty(event, 'pointerType', { value: 'touch' })
      target?.element.dispatchEvent(event)
    }

    await source?.trigger('click')
    touchTarget()
    await nextTick()

    expect(action).not.toHaveBeenCalled()
    expect(target?.classes()).toContain('confirming')
    expect(wrapper.text()).toContain('再点一次确认')

    touchTarget()
    await nextTick()

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
