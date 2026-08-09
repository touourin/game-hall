import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import XiangqiBoard from './XiangqiBoard.vue'

interface TestXiangqiGame {
  board: Array<Array<string | null>>
  hangingPieces: Array<{ row: number; column: number }>
  legalMoves: Array<{
    fromRow: number
    fromColumn: number
    toRow: number
    toColumn: number
    destinationAttacked?: boolean
    destinationProtected?: boolean
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
      hangingPieces: [],
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

    const boardArt = wrapper.get('.xiangqi-board-art')
    const boundary = wrapper.get('.xiangqi-board-boundary')

    expect(boardArt.attributes('viewBox')).toBe('0 0 9 10')
    expect(wrapper.find('.xiangqi-board-stage').exists()).toBe(true)
    expect(wrapper.findAll('.xiangqi-lattice-lines')).toHaveLength(2)
    expect(wrapper.find('.xiangqi-palace-lines').exists()).toBe(true)
    expect(boundary.attributes()).toMatchObject({
      x: '0.5',
      y: '0.5',
      width: '8',
      height: '9',
    })
    expect(wrapper.findAll('.xiangqi-river-label text').map((node) => node.text())).toEqual([
      '楚 河',
      '汉 界',
    ])
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
    expect(cells[8 * 9 + 4]?.get('.xiangqi-hint-dot').classes()).toContain('is-green')
    await cells[8 * 9 + 4]?.trigger('click')
    expect(action).toHaveBeenCalledWith('move', {
      fromRow: 9,
      fromColumn: 4,
      toRow: 8,
      toColumn: 4,
    })
  })

  it('keeps an unrooted enemy capture marked before and after selection', async () => {
    const enabled = snapshot('p1')
    const enabledGame = enabled.game as unknown as TestXiangqiGame
    enabledGame.board[8][4] = 'bP'
    enabledGame.hangingPieces.push({ row: 8, column: 4 })
    const enabledWrapper = mount(XiangqiBoard, {
      props: { snapshot: enabled },
      global: { plugins: [createPinia()] },
    })

    const target = enabledWrapper.findAll('.xiangqi-cell')[8 * 9 + 4]
    expect(target?.get('.xiangqi-hint-dot').classes()).toContain('is-red')
    expect(target?.attributes('aria-label')).toContain('可吃无根卒')
    expect(enabledWrapper.text()).not.toContain('吃子提醒')

    await enabledWrapper.findAll('.xiangqi-cell')[9 * 9 + 4]?.trigger('click')
    expect(target?.get('.xiangqi-hint-dot').classes()).toContain('is-red')
  })

  it('keeps an unrooted friendly piece marked at all times', async () => {
    const current = snapshot('p1')
    const currentGame = current.game as unknown as TestXiangqiGame
    currentGame.board[8][3] = 'rP'
    currentGame.hangingPieces.push({ row: 8, column: 3 })
    const wrapper = mount(XiangqiBoard, {
      props: { snapshot: current },
      global: { plugins: [createPinia()] },
    })
    const friendlyTarget = () => wrapper.findAll('.xiangqi-cell')[8 * 9 + 3]

    expect(friendlyTarget()?.get('.xiangqi-hint-dot').classes()).toContain('is-red')
    expect(friendlyTarget()?.attributes('aria-label')).toContain('我方兵无根')

    await wrapper.findAll('.xiangqi-cell')[9 * 9 + 4]?.trigger('click')
    expect(friendlyTarget()?.get('.xiangqi-hint-dot').classes()).toContain('is-red')

    const waiting = snapshot('p2')
    const waitingGame = waiting.game as unknown as TestXiangqiGame
    waitingGame.board[8][3] = 'rP'
    waitingGame.hangingPieces.push({ row: 8, column: 3 })
    await wrapper.setProps({ snapshot: waiting })
    expect(friendlyTarget()?.get('.xiangqi-hint-dot').classes()).toContain('is-red')
  })

  it('hides rooted captures before selection and warns about an unrooted landing', async () => {
    const protectedCapture = snapshot('p1')
    const protectedGame = protectedCapture.game as unknown as TestXiangqiGame
    protectedGame.board[8][4] = 'bP'
    protectedGame.legalMoves[0].destinationAttacked = true
    const protectedWrapper = mount(XiangqiBoard, {
      props: { snapshot: protectedCapture },
      global: { plugins: [createPinia()] },
    })
    const protectedTarget = protectedWrapper.findAll('.xiangqi-cell')[8 * 9 + 4]

    expect(protectedTarget?.find('.xiangqi-hint-dot').exists()).toBe(false)
    await protectedWrapper.findAll('.xiangqi-cell')[9 * 9 + 4]?.trigger('click')
    expect(protectedTarget?.get('.xiangqi-hint-dot').classes()).toContain('is-red')
  })

  it('uses red only for an attacked unrooted move', async () => {
    const unsafeMove = snapshot('p1')
    const unsafeGame = unsafeMove.game as unknown as TestXiangqiGame
    unsafeGame.legalMoves[0].destinationAttacked = true
    unsafeGame.legalMoves[0].destinationProtected = false
    const unsafeWrapper = mount(XiangqiBoard, {
      props: { snapshot: unsafeMove },
      global: { plugins: [createPinia()] },
    })

    await unsafeWrapper.findAll('.xiangqi-cell')[9 * 9 + 4]?.trigger('click')
    expect(
      unsafeWrapper.findAll('.xiangqi-cell')[8 * 9 + 4]
        ?.get('.xiangqi-hint-dot').classes(),
    ).toContain('is-red')

    const rootedMove = snapshot('p1')
    const rootedGame = rootedMove.game as unknown as TestXiangqiGame
    rootedGame.legalMoves[0].destinationAttacked = true
    rootedGame.legalMoves[0].destinationProtected = true
    const rootedWrapper = mount(XiangqiBoard, {
      props: { snapshot: rootedMove },
      global: { plugins: [createPinia()] },
    })

    await rootedWrapper.findAll('.xiangqi-cell')[9 * 9 + 4]?.trigger('click')
    expect(
      rootedWrapper.findAll('.xiangqi-cell')[8 * 9 + 4]
        ?.get('.xiangqi-hint-dot').classes(),
    ).toContain('is-green')
  })

  it('hides unselected capture dots when the room reminder is disabled', async () => {

    const disabled = snapshot('p1', false)
    const disabledGame = disabled.game as unknown as TestXiangqiGame
    disabledGame.board[8][4] = 'bP'
    const disabledWrapper = mount(XiangqiBoard, {
      props: { snapshot: disabled },
      global: { plugins: [createPinia()] },
    })
    const disabledTarget = disabledWrapper.findAll('.xiangqi-cell')[8 * 9 + 4]

    expect(disabledTarget?.find('.xiangqi-hint-dot').exists()).toBe(false)

    await disabledWrapper.findAll('.xiangqi-cell')[9 * 9 + 4]?.trigger('click')
    expect(disabledTarget?.classes()).toContain('legal')
    expect(disabledTarget?.get('.xiangqi-hint-dot').classes()).toContain('is-green')
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
