import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import ChessBoard from './ChessBoard.vue'


function initialBoard(): Array<Array<string | null>> {
  const board = Array.from({ length: 8 }, () => Array<string | null>(8).fill(null))
  const backRank = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
  board[0] = backRank.map((piece) => `b${piece}`)
  board[1] = Array(8).fill('bP')
  board[6] = Array(8).fill('wP')
  board[7] = backRank.map((piece) => `w${piece}`)
  return board
}


function snapshot(
  turnPlayerId: string | null = 'p1',
  viewerColor: 'white' | 'black' = 'white',
): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'CHESS',
    gameKey: 'chess',
    gameName: '国际象棋',
    options: { firstPlayer: 'random', allowUndo: true, allowDraw: true },
    phase: 'playing',
    hostId: 'p1',
    self: {
      id: viewerColor === 'white' ? 'p1' : 'p2',
      name: viewerColor === 'white' ? '白方玩家' : '黑方玩家',
      seat: viewerColor === 'white' ? 0 : 1,
    },
    players: [
      { id: 'p1', name: '白方玩家', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '黑方玩家', seat: 1, connected: true, isHost: false },
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
      board: initialBoard(),
      turnPlayerId,
      colors: { p1: 'white', p2: 'black' },
      viewerColor,
      lastMove: null,
      moveHistory: [],
      capturedPieces: [],
      legalMoves: viewerColor === 'white' ? [
        {
          fromRow: 6,
          fromColumn: 4,
          toRow: 4,
          toColumn: 4,
          isCapture: false,
          promotionRequired: false,
          castle: null,
        },
      ] : [],
      whiteInCheck: false,
      blackInCheck: false,
      checkedColor: null,
      halfmoveClock: 0,
      fullmoveNumber: 1,
    },
  }
}


describe('ChessBoard', () => {
  it('renders all squares, selects a piece, and submits a legal move', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(ChessBoard, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    expect(wrapper.findAll('.chess-cell')).toHaveLength(64)
    expect(wrapper.get('[data-square="e1"]').text()).toContain('♔')
    expect(wrapper.get('[data-square="e8"]').text()).toContain('♚')

    await wrapper.get('[data-square="e2"]').trigger('click')
    expect(wrapper.get('[data-square="e2"]').classes()).toContain('selected')
    expect(wrapper.get('[data-square="e4"]').classes()).toContain('legal')
    expect(wrapper.text()).toContain('已选择白兵')

    await wrapper.get('[data-square="e4"]').trigger('click')
    expect(action).toHaveBeenCalledWith('move', {
      fromRow: 6,
      fromColumn: 4,
      toRow: 4,
      toColumn: 4,
    })
  })

  it('rotates the board for black and disables it while waiting', () => {
    const current = snapshot('p1', 'black')
    const wrapper = mount(ChessBoard, {
      props: { snapshot: current },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.chess-cell')[0]?.attributes('data-square')).toBe('h1')
    expect(wrapper.findAll('.chess-cell').every(
      (cell) => cell.attributes('disabled') !== undefined,
    )).toBe(true)
    expect(wrapper.text()).toContain('你执黑')
  })

  it('asks which piece a pawn should promote to before moving', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const current = snapshot()
    const board = Array.from({ length: 8 }, () => Array<string | null>(8).fill(null))
    board[0][7] = 'bK'
    board[1][0] = 'wP'
    board[7][7] = 'wK'
    current.game = {
      ...(current.game as Record<string, unknown>),
      board,
      legalMoves: [{
        fromRow: 1,
        fromColumn: 0,
        toRow: 0,
        toColumn: 0,
        isCapture: false,
        promotionRequired: true,
        castle: null,
      }],
    }
    const wrapper = mount(ChessBoard, {
      props: { snapshot: current },
      global: { plugins: [pinia] },
    })

    await wrapper.get('[data-square="a7"]').trigger('click')
    await wrapper.get('[data-square="a8"]').trigger('click')

    expect(wrapper.get('.promotion-panel').text()).toContain('选择升变棋子')
    expect(action).not.toHaveBeenCalled()
    await wrapper.findAll('.promotion-panel > div button')[0]?.trigger('click')
    expect(action).toHaveBeenCalledWith('move', {
      fromRow: 1,
      fromColumn: 0,
      toRow: 0,
      toColumn: 0,
      promotion: 'Q',
    })
  })

  it('shows check and captured pieces and replays castling correctly', async () => {
    const current = snapshot(null)
    current.phase = 'finished'
    current.actions.canAct = false
    current.game = {
      ...(current.game as Record<string, unknown>),
      board: initialBoard(),
      checkedColor: 'black',
      capturedPieces: [{ piece: 'bP', capturedBy: 'white', moveNumber: 1 }],
      moveHistory: [{
        number: 1,
        fullmoveNumber: 1,
        fromRow: 7,
        fromColumn: 4,
        toRow: 7,
        toColumn: 6,
        piece: 'wK',
        resultPiece: 'wK',
        captured: null,
        color: 'white',
        promotion: null,
        castle: 'kingside',
        enPassant: false,
        gaveCheck: false,
        notation: 'O-O',
      }],
    }
    const wrapper = mount(ChessBoard, {
      props: { snapshot: current },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('黑方被将军')
    expect(wrapper.text()).toContain('♟')
    await wrapper.findAll('.chess-actions button')[0]?.trigger('click')

    expect(wrapper.get('.replay-panel').text()).toContain('O-O')
    expect(wrapper.get('[data-square="g1"] .chess-piece').text()).toBe('♔')
    expect(wrapper.get('[data-square="f1"] .chess-piece').text()).toBe('♖')
    expect(wrapper.find('[data-square="e1"] .chess-piece').exists()).toBe(false)
  })

  it('keeps a spectator board read-only even from the current player perspective', () => {
    const current = snapshot()
    current.viewer = {
      mode: 'spectator',
      id: 'spectator',
      name: '观众',
      targetPlayerId: 'p1',
    }
    current.actions.canAct = false
    const wrapper = mount(ChessBoard, {
      props: { snapshot: current },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('正在观战')
    expect(wrapper.findAll('.chess-cell').every(
      (cell) => cell.attributes('disabled') !== undefined,
    )).toBe(true)
    expect(wrapper.find('.arcade-danger-button').exists()).toBe(false)
  })
})
