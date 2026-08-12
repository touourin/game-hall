import { computed, onBeforeUnmount, onMounted, ref, watch, type Ref } from 'vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import {
  BOARD_HEIGHT,
  BOARD_WIDTH,
  absoluteCells,
  clearCompletedLines,
  createBoard,
  ghostPiece,
  isValidPosition,
  lineClearScore,
  lockPiece,
  moved,
  shuffledBag,
  spawnPiece,
  tryRotate,
  type ActivePiece,
  type Board,
  type PieceType,
} from './tetrisEngine'

interface TetrisView {
  challengeMode: 'endless' | 'timed'
  durationSeconds: number
  score: number
  lines: number
  level: number
  pieces: number
  elapsedMs: number
}

interface DisplayCell {
  type: PieceType | null
  active: boolean
  ghost: boolean
}

interface SavedRun {
  board: Board
  active: ActivePiece
  queue: PieceType[]
  held: PieceType | null
  holdUsed: boolean
  score: number
  lines: number
  pieces: number
  elapsedMs: number
  ended?: boolean
  endReason?: 'topped_out' | 'timeout'
}

export function useTetrisGame(snapshot: Ref<ArcadeSnapshot>) {
  const arcade = useArcadeStore()
  const board = ref<Board>(createBoard())
  const queue = ref<PieceType[]>([])
  const active = ref<ActivePiece>(spawnPiece('T'))
  const held = ref<PieceType | null>(null)
  const holdUsed = ref(false)
  const score = ref(0)
  const lines = ref(0)
  const pieces = ref(0)
  const elapsedMs = ref(0)
  const paused = ref(false)
  const autoPaused = ref(false)
  const submitting = ref(false)
  const submitted = ref(false)
  const runEnded = ref(false)
  const endReason = ref<'topped_out' | 'timeout'>('topped_out')
  const submissionError = ref<string | null>(null)
  const lastClear = ref(0)
  let frame: number | null = null
  let lastFrameAt = performance.now()
  let dropAccumulator = 0
  let elapsedAccumulator = 0
  let saveAccumulator = 0

  const storageKey = computed(() => `game-hall:tetris:${snapshot.value.roomCode}`)
  const serverGame = computed(() => snapshot.value.game as unknown as TetrisView)
  const isTimed = computed(() => snapshot.value.options.challengeMode !== 'endless')
  const durationMs = computed(() => {
    const seconds = Number(snapshot.value.options.durationSeconds ?? 180)
    return [60, 180, 300].includes(seconds) ? seconds * 1_000 : 180_000
  })
  const level = computed(() => Math.floor(lines.value / 10) + 1)
  const gravityMs = computed(() => Math.max(90, 850 * 0.84 ** (level.value - 1)))
  const nextPieces = computed(() => queue.value.slice(0, 3))
  const isPlaying = computed(() => (
    snapshot.value.phase === 'playing' && !submitting.value && !runEnded.value
  ))
  const canControl = computed(() => isPlaying.value && !paused.value)
  const formattedTime = computed(() => {
    const milliseconds = isTimed.value
      ? Math.max(0, durationMs.value - elapsedMs.value)
      : elapsedMs.value
    const totalSeconds = isTimed.value
      ? Math.ceil(milliseconds / 1_000)
      : Math.floor(milliseconds / 1_000)
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return minutes ? `${minutes}:${String(seconds).padStart(2, '0')}` : `${seconds} 秒`
  })

  const displayCells = computed<DisplayCell[]>(() => {
    const cells = board.value.flat().map((type) => ({ type, active: false, ghost: false }))
    if (!isPlaying.value) return cells
    for (const [x, y] of absoluteCells(ghostPiece(board.value, active.value))) {
      if (y >= 0 && y < BOARD_HEIGHT && !cells[y * BOARD_WIDTH + x]?.type) {
        cells[y * BOARD_WIDTH + x] = { type: active.value.type, active: false, ghost: true }
      }
    }
    for (const [x, y] of absoluteCells(active.value)) {
      if (y >= 0 && y < BOARD_HEIGHT) {
        cells[y * BOARD_WIDTH + x] = { type: active.value.type, active: true, ghost: false }
      }
    }
    return cells
  })

  function ensureQueue() {
    while (queue.value.length < 7) queue.value.push(...shuffledBag())
  }

  function takePiece(): PieceType {
    ensureQueue()
    return queue.value.shift()!
  }

  function freshRun() {
    board.value = createBoard()
    queue.value = []
    held.value = null
    holdUsed.value = false
    score.value = 0
    lines.value = 0
    pieces.value = 0
    elapsedMs.value = 0
    lastClear.value = 0
    submitting.value = false
    submitted.value = false
    runEnded.value = false
    endReason.value = 'topped_out'
    submissionError.value = null
    paused.value = false
    autoPaused.value = false
    ensureQueue()
    active.value = spawnPiece(takePiece())
    dropAccumulator = 0
    elapsedAccumulator = 0
    saveAccumulator = 0
    lastFrameAt = performance.now()
    saveRun()
  }

  function moveHorizontal(direction: -1 | 1) {
    if (!canControl.value) return
    const candidate = moved(active.value, direction, 0)
    if (isValidPosition(board.value, candidate)) active.value = candidate
  }

  function rotate(direction: -1 | 1 = 1) {
    if (!canControl.value) return
    const rotated = tryRotate(board.value, active.value, direction)
    if (rotated) active.value = rotated
  }

  function softDrop() {
    if (!canControl.value) return
    const candidate = moved(active.value, 0, 1)
    if (isValidPosition(board.value, candidate)) {
      active.value = candidate
      score.value += 1
    } else {
      settlePiece()
    }
    dropAccumulator = 0
  }

  function hardDrop() {
    if (!canControl.value) return
    const ghost = ghostPiece(board.value, active.value)
    const distance = ghost.y - active.value.y
    active.value = ghost
    score.value += Math.max(0, distance * 2)
    settlePiece()
    dropAccumulator = 0
  }

  function holdPiece() {
    if (!canControl.value || holdUsed.value) return
    const outgoing = active.value.type
    active.value = spawnPiece(held.value ?? takePiece())
    held.value = outgoing
    holdUsed.value = true
    if (!isValidPosition(board.value, active.value)) {
      void endRun('topped_out')
      return
    }
    saveRun()
  }

  function settlePiece() {
    const locked = lockPiece(board.value, active.value)
    const cleared = clearCompletedLines(locked.board)
    board.value = cleared.board
    pieces.value += 1
    lastClear.value = cleared.cleared
    if (cleared.cleared > 0) {
      score.value += lineClearScore(cleared.cleared, level.value)
      lines.value += cleared.cleared
    }
    holdUsed.value = false
    active.value = spawnPiece(takePiece())
    if (locked.toppedOut || !isValidPosition(board.value, active.value)) {
      void endRun('topped_out')
      return
    }
    saveRun()
  }

  async function endRun(reason: 'topped_out' | 'timeout') {
    if (runEnded.value || snapshot.value.phase !== 'playing') return
    runEnded.value = true
    endReason.value = reason
    paused.value = false
    elapsedMs.value = reason === 'timeout'
      ? durationMs.value
      : Math.max(1_000, Math.round(elapsedMs.value))
    saveRun()
    await submitFinalScore()
  }

  async function submitFinalScore() {
    if (submitting.value || !runEnded.value || snapshot.value.phase !== 'playing') return
    submitting.value = true
    submissionError.value = null
    const succeeded = await arcade.actionWithResult('finish', {
      score: score.value,
      lines: lines.value,
      level: level.value,
      pieces: Math.max(1, pieces.value),
      elapsedMs: elapsedMs.value,
      endReason: endReason.value,
    })
    if (succeeded) {
      submitted.value = true
      sessionStorage.removeItem(storageKey.value)
      return
    }
    submitting.value = false
    submissionError.value = arcade.error || '成绩保存失败，请检查网络后重试'
    saveRun()
  }

  function togglePause() {
    if (!isPlaying.value) return
    paused.value = !paused.value
    autoPaused.value = false
    dropAccumulator = 0
    lastFrameAt = performance.now()
    saveRun()
  }

  function tick(timestamp: number) {
    const elapsedDelta = Math.max(0, timestamp - lastFrameAt)
    const gravityDelta = Math.min(50, elapsedDelta)
    lastFrameAt = timestamp
    if (canControl.value) {
      dropAccumulator += gravityDelta
      elapsedAccumulator += elapsedDelta
      saveAccumulator += elapsedDelta
      if (elapsedAccumulator >= 100) {
        elapsedMs.value += elapsedAccumulator
        elapsedAccumulator = 0
        if (isTimed.value && elapsedMs.value >= durationMs.value) {
          elapsedMs.value = durationMs.value
          void endRun('timeout')
        }
      }
      if (saveAccumulator >= 1_000) {
        saveAccumulator = 0
        saveRun()
      }
      if (!canControl.value) {
        frame = window.requestAnimationFrame(tick)
        return
      }
      if (dropAccumulator >= gravityMs.value) {
        const candidate = moved(active.value, 0, 1)
        if (isValidPosition(board.value, candidate)) active.value = candidate
        else settlePiece()
        dropAccumulator = 0
      }
    }
    frame = window.requestAnimationFrame(tick)
  }

  function onKeydown(event: KeyboardEvent) {
    const target = event.target
    if (
      target instanceof Element
      && target.closest('button, input, textarea, select, [contenteditable="true"], .modal-backdrop')
    ) return
    const handled = ['ArrowLeft', 'ArrowRight', 'ArrowDown', 'ArrowUp', 'Space', 'KeyZ', 'KeyX', 'KeyC', 'KeyP', 'Escape']
      .includes(event.code)
    if (!handled) return
    if (event.code === 'KeyP' || event.code === 'Escape') {
      if (!isPlaying.value) return
      event.preventDefault()
      if (!event.repeat) togglePause()
      return
    }
    if (!canControl.value) return
    event.preventDefault()
    if (event.code === 'ArrowLeft') moveHorizontal(-1)
    else if (event.code === 'ArrowRight') moveHorizontal(1)
    else if (event.code === 'ArrowDown') softDrop()
    else if (event.code === 'ArrowUp' || event.code === 'KeyX') {
      if (!event.repeat) rotate(1)
    } else if (event.code === 'KeyZ') {
      if (!event.repeat) rotate(-1)
    } else if (event.code === 'Space') {
      if (!event.repeat) hardDrop()
    } else if (event.code === 'KeyC' && !event.repeat) holdPiece()
  }

  function saveRun() {
    if (snapshot.value.phase !== 'playing' || submitted.value) return
    const saved: SavedRun = {
      board: board.value,
      active: active.value,
      queue: queue.value,
      held: held.value,
      holdUsed: holdUsed.value,
      score: score.value,
      lines: lines.value,
      pieces: pieces.value,
      elapsedMs: Math.round(elapsedMs.value),
      ended: runEnded.value,
      endReason: endReason.value,
    }
    sessionStorage.setItem(storageKey.value, JSON.stringify(saved))
  }

  function restoreRun(): boolean {
    try {
      const raw = sessionStorage.getItem(storageKey.value)
      if (!raw) return false
      const saved = JSON.parse(raw) as SavedRun
      if (!Array.isArray(saved.board) || saved.board.length !== BOARD_HEIGHT) return false
      board.value = saved.board
      active.value = saved.active
      queue.value = saved.queue
      held.value = saved.held
      holdUsed.value = Boolean(saved.holdUsed)
      score.value = Number(saved.score) || 0
      lines.value = Number(saved.lines) || 0
      pieces.value = Number(saved.pieces) || 0
      elapsedMs.value = Number(saved.elapsedMs) || 0
      runEnded.value = Boolean(saved.ended)
      endReason.value = saved.endReason === 'timeout' ? 'timeout' : 'topped_out'
      ensureQueue()
      return runEnded.value || isValidPosition(board.value, active.value)
    } catch {
      return false
    }
  }

  async function restartChallenge() {
    if (await arcade.restartGame()) freshRun()
  }

  function onVisibilityChange() {
    if (document.hidden && isPlaying.value && !paused.value) {
      paused.value = true
      autoPaused.value = true
      saveRun()
    }
    lastFrameAt = performance.now()
  }

  watch(
    () => snapshot.value.phase,
    (phase, previous) => {
      if (phase === 'finished') {
        submitting.value = false
        submitted.value = true
        runEnded.value = true
        submissionError.value = null
        sessionStorage.removeItem(storageKey.value)
      } else if (phase === 'playing' && previous === 'finished') {
        freshRun()
      }
    },
  )

  onMounted(() => {
    if (snapshot.value.phase === 'playing') {
      if (!restoreRun()) freshRun()
      else if (isTimed.value && !runEnded.value && elapsedMs.value >= durationMs.value) {
        void endRun('timeout')
      }
    }
    window.addEventListener('keydown', onKeydown, { passive: false })
    document.addEventListener('visibilitychange', onVisibilityChange)
    frame = window.requestAnimationFrame(tick)
  })

  onBeforeUnmount(() => {
    saveRun()
    if (frame !== null) window.cancelAnimationFrame(frame)
    window.removeEventListener('keydown', onKeydown)
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return {
    arcade,
    autoPaused,
    canControl,
    displayCells,
    endReason,
    elapsedMs,
    formattedTime,
    hardDrop,
    held,
    holdPiece,
    holdUsed,
    isPlaying,
    isTimed,
    lastClear,
    level,
    lines,
    moveHorizontal,
    nextPieces,
    paused,
    restartChallenge,
    rotate,
    runEnded,
    score,
    serverGame,
    softDrop,
    submissionError,
    submitFinalScore,
    submitting,
    togglePause,
  }
}
