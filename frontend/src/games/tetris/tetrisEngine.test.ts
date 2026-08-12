import { describe, expect, it } from 'vitest'
import {
  BOARD_HEIGHT,
  absoluteCells,
  clearCompletedLines,
  createBoard,
  ghostPiece,
  isValidPosition,
  lineClearScore,
  lockPiece,
  shuffledBag,
  spawnPiece,
  tryRotate,
} from './tetrisEngine'

describe('落块挑战规则', () => {
  it('每个随机袋恰好包含七种方块', () => {
    const bag = shuffledBag(() => 0.42)
    expect(bag).toHaveLength(7)
    expect(new Set(bag)).toEqual(new Set(['I', 'J', 'L', 'O', 'S', 'T', 'Z']))
  })

  it('幽灵方块会落到空棋盘底部并能锁定', () => {
    const board = createBoard()
    const ghost = ghostPiece(board, spawnPiece('O'))
    expect(Math.max(...absoluteCells(ghost).map(([, y]) => y))).toBe(BOARD_HEIGHT - 1)
    const locked = lockPiece(board, ghost)
    expect(locked.toppedOut).toBe(false)
    expect(locked.board.flat().filter(Boolean)).toHaveLength(4)
  })

  it('消除填满的行并在顶部补空行', () => {
    const board = createBoard()
    board[18] = Array(10).fill('T')
    board[19] = Array(10).fill('I')
    const result = clearCompletedLines(board)
    expect(result.cleared).toBe(2)
    expect(result.board).toHaveLength(20)
    expect(result.board[0]?.every((cell) => cell === null)).toBe(true)
  })

  it('靠墙旋转时会尝试横向修正', () => {
    const board = createBoard()
    const piece = { ...spawnPiece('I'), rotation: 1, x: -2, y: 3 }
    expect(isValidPosition(board, piece)).toBe(true)
    const rotated = tryRotate(board, piece, 1)
    expect(rotated).not.toBeNull()
    expect(rotated && isValidPosition(board, rotated)).toBe(true)
  })

  it('按当前等级计算经典消行基础分', () => {
    expect(lineClearScore(1, 3)).toBe(300)
    expect(lineClearScore(4, 3)).toBe(2_400)
  })
})
