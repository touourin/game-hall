import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import GoBoard from './GoBoard.vue'

function scoringSnapshot(): ArcadeSnapshot {
  const board = Array.from({ length: 9 }, () => Array<number>(9).fill(0))
  board[0][0] = 1
  board[0][1] = 2
  return {
    revision: 4,
    roomCode: 'TEST',
    gameKey: 'go',
    gameName: '围棋',
    options: { boardSize: 9, komi: 7.5 },
    phase: 'scoring',
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
      canRequestDraw: false,
      canResolveRequest: false,
    },
    rematchReadyPlayerIds: [],
    request: null,
    chat: { maxLength: 300, messages: [] },
    game: {
      boardSize: 9,
      board,
      turnPlayerId: null,
      colors: { p1: 'black', p2: 'white' },
      captures: { black: 0, white: 0 },
      komi: 7.5,
      lastMove: { pass: true },
      score: {
        black: 81,
        white: 7.5,
        blackStones: 1,
        blackTerritory: 80,
        whiteStones: 0,
        whiteTerritory: 0,
        neutralPoints: 0,
        komi: 7.5,
        deadBlack: 0,
        deadWhite: 1,
      },
      scoring: {
        deadStones: [{ row: 0, column: 1 }],
        confirmedPlayerIds: [],
        resumeRequesterId: null,
      },
    },
  }
}

function playingSnapshot(): ArcadeSnapshot {
  const next = scoringSnapshot()
  next.phase = 'playing'
  next.revision = 1
  next.game.turnPlayerId = 'p1'
  next.game.lastMove = null
  next.game.score = null
  next.game.scoring = null
  next.game.board = Array.from({ length: 9 }, () => Array<number>(9).fill(0))
  return next
}

describe('GoBoard', () => {
  it('sizes the shared intersection lattice from the current board', () => {
    const wrapper = mount(GoBoard, {
      props: { snapshot: playingSnapshot() },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.intersection-board__lattice').attributes('viewBox')).toBe(
      '0 0 9 9',
    )
  })

  it('shows star points and confirms touch moves on the second tap', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(GoBoard, {
      props: { snapshot: playingSnapshot() },
      global: { plugins: [pinia] },
    })
    const point = wrapper.findAll('.go-point')[4 * 9 + 4]
    const touchClick = () => {
      const event = new MouseEvent('click', { bubbles: true, cancelable: true })
      Object.defineProperty(event, 'pointerType', { value: 'touch' })
      point?.element.dispatchEvent(event)
    }

    expect(wrapper.findAll('.go-point.star')).toHaveLength(5)
    touchClick()
    await nextTick()

    expect(action).not.toHaveBeenCalled()
    expect(point?.find('.go-preview').classes()).toContain('active')
    expect(wrapper.get('.go-board-hint').text()).toContain('再轻点一次确认')

    touchClick()
    await nextTick()

    expect(action).toHaveBeenCalledWith('place', { row: 4, column: 4 })
  })

  it('marks dead stones and exposes both scoring decisions', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(GoBoard, {
      props: { snapshot: scoringSnapshot() },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('终局数子确认')
    expect(wrapper.text()).toContain('黑方 81')
    expect(wrapper.get('.go-stone.white').classes()).toContain('dead')

    await wrapper.findAll('.go-point')[1]?.trigger('click')
    expect(action).toHaveBeenCalledWith('mark_dead', { row: 0, column: 1 })

    const scoringButtons = wrapper.findAll('.go-scoring-actions button')
    await scoringButtons[0]?.trigger('click')
    expect(action).toHaveBeenCalledWith('confirm_score')
    await scoringButtons[1]?.trigger('click')
    expect(action).toHaveBeenCalledWith('resume_play')
  })

  it('shows that the other player requested continuing the game', () => {
    const next = scoringSnapshot()
    ;(next.game.scoring as { resumeRequesterId: string | null }).resumeRequesterId = 'p2'
    const wrapper = mount(GoBoard, {
      props: { snapshot: next },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('玩家二申请继续对局')
    expect(wrapper.findAll('.go-scoring-actions button')[1]?.text()).toContain(
      '同意继续对局',
    )
  })
})
