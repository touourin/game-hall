export const BOARD_WIDTH = 10
export const BOARD_HEIGHT = 20

export type PieceType = 'I' | 'J' | 'L' | 'O' | 'S' | 'T' | 'Z'
export type BoardCell = PieceType | null
export type Board = BoardCell[][]
export type Point = readonly [number, number]

export interface ActivePiece {
  type: PieceType
  rotation: number
  x: number
  y: number
}

const TYPES: readonly PieceType[] = ['I', 'J', 'L', 'O', 'S', 'T', 'Z']

export const PIECE_CELLS: Record<PieceType, readonly (readonly Point[])[]> = {
  I: [
    [[0, 1], [1, 1], [2, 1], [3, 1]],
    [[2, 0], [2, 1], [2, 2], [2, 3]],
    [[0, 2], [1, 2], [2, 2], [3, 2]],
    [[1, 0], [1, 1], [1, 2], [1, 3]],
  ],
  J: [
    [[0, 0], [0, 1], [1, 1], [2, 1]],
    [[1, 0], [2, 0], [1, 1], [1, 2]],
    [[0, 1], [1, 1], [2, 1], [2, 2]],
    [[1, 0], [1, 1], [0, 2], [1, 2]],
  ],
  L: [
    [[2, 0], [0, 1], [1, 1], [2, 1]],
    [[1, 0], [1, 1], [1, 2], [2, 2]],
    [[0, 1], [1, 1], [2, 1], [0, 2]],
    [[0, 0], [1, 0], [1, 1], [1, 2]],
  ],
  O: [
    [[1, 0], [2, 0], [1, 1], [2, 1]],
    [[1, 0], [2, 0], [1, 1], [2, 1]],
    [[1, 0], [2, 0], [1, 1], [2, 1]],
    [[1, 0], [2, 0], [1, 1], [2, 1]],
  ],
  S: [
    [[1, 0], [2, 0], [0, 1], [1, 1]],
    [[1, 0], [1, 1], [2, 1], [2, 2]],
    [[1, 1], [2, 1], [0, 2], [1, 2]],
    [[0, 0], [0, 1], [1, 1], [1, 2]],
  ],
  T: [
    [[1, 0], [0, 1], [1, 1], [2, 1]],
    [[1, 0], [1, 1], [2, 1], [1, 2]],
    [[0, 1], [1, 1], [2, 1], [1, 2]],
    [[1, 0], [0, 1], [1, 1], [1, 2]],
  ],
  Z: [
    [[0, 0], [1, 0], [1, 1], [2, 1]],
    [[2, 0], [1, 1], [2, 1], [1, 2]],
    [[0, 1], [1, 1], [1, 2], [2, 2]],
    [[1, 0], [0, 1], [1, 1], [0, 2]],
  ],
}

export function createBoard(): Board {
  return Array.from({ length: BOARD_HEIGHT }, () => Array<BoardCell>(BOARD_WIDTH).fill(null))
}

export function spawnPiece(type: PieceType): ActivePiece {
  return { type, rotation: 0, x: 3, y: -1 }
}

export function absoluteCells(piece: ActivePiece): Point[] {
  return PIECE_CELLS[piece.type][piece.rotation % 4]!.map(
    ([x, y]) => [piece.x + x, piece.y + y] as const,
  )
}

export function isValidPosition(board: Board, piece: ActivePiece): boolean {
  return absoluteCells(piece).every(([x, y]) => (
    x >= 0
    && x < BOARD_WIDTH
    && y < BOARD_HEIGHT
    && (y < 0 || board[y]?.[x] === null)
  ))
}

export function moved(piece: ActivePiece, dx: number, dy: number): ActivePiece {
  return { ...piece, x: piece.x + dx, y: piece.y + dy }
}

export function tryRotate(
  board: Board,
  piece: ActivePiece,
  direction: 1 | -1,
): ActivePiece | null {
  if (piece.type === 'O') return piece
  const rotation = (piece.rotation + direction + 4) % 4
  for (const [dx, dy] of [[0, 0], [-1, 0], [1, 0], [-2, 0], [2, 0], [0, -1]] as const) {
    const candidate = { ...piece, rotation, x: piece.x + dx, y: piece.y + dy }
    if (isValidPosition(board, candidate)) return candidate
  }
  return null
}

export function ghostPiece(board: Board, piece: ActivePiece): ActivePiece {
  let ghost = piece
  while (isValidPosition(board, moved(ghost, 0, 1))) ghost = moved(ghost, 0, 1)
  return ghost
}

export function lockPiece(board: Board, piece: ActivePiece): { board: Board; toppedOut: boolean } {
  const next = board.map((row) => [...row])
  let toppedOut = false
  for (const [x, y] of absoluteCells(piece)) {
    if (y < 0) toppedOut = true
    else if (next[y]) next[y]![x] = piece.type
  }
  return { board: next, toppedOut }
}

export function clearCompletedLines(board: Board): { board: Board; cleared: number } {
  const remaining = board.filter((row) => row.some((cell) => cell === null))
  const cleared = BOARD_HEIGHT - remaining.length
  return {
    board: [
      ...Array.from({ length: cleared }, () => Array<BoardCell>(BOARD_WIDTH).fill(null)),
      ...remaining.map((row) => [...row]),
    ],
    cleared,
  }
}

export function lineClearScore(cleared: number, level: number): number {
  return ([0, 100, 300, 500, 800][cleared] ?? 0) * level
}

export function shuffledBag(random: () => number = Math.random): PieceType[] {
  const bag = [...TYPES]
  for (let index = bag.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(random() * (index + 1))
    ;[bag[index], bag[swapIndex]] = [bag[swapIndex]!, bag[index]!]
  }
  return bag
}

export function previewCells(type: PieceType): Set<string> {
  return new Set(PIECE_CELLS[type][0]!.map(([x, y]) => `${x}:${y}`))
}
