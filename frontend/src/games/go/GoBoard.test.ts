import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import GoBoard from './GoBoard.vue'

function snapshot(): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'TEST',
    gameKey: 'go',
    gameName: '围棋',
    options: { boardSize: 9 },
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', name: '玩家一', seat: 0 },
    players: [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '玩家二', seat: 1, connected: true, isHost: false },
    ],
    requiredPlayers: 2,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: { canStart: false, canRestart: false, canAct: true },
    game: {
      boardSize: 9,
      board: Array.from({ length: 9 }, () => Array<number>(9).fill(0)),
      turnPlayerId: 'p1',
      colors: { p1: 'black', p2: 'white' },
      captures: { black: 0, white: 0 },
      komi: 7.5,
      lastMove: null,
      score: null,
    },
  }
}

describe('GoBoard', () => {
  it('shows star points and confirms touch moves on the second tap', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(GoBoard, {
      props: { snapshot: snapshot() },
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

    touchClick()
    await nextTick()
    expect(action).toHaveBeenCalledWith('place', { row: 4, column: 4 })
  })
})
