import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import GomokuBoard from './GomokuBoard.vue'

function snapshot(): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'TEST',
    gameKey: 'gomoku',
    gameName: '五子棋',
    options: {},
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
      boardSize: 15,
      board: Array.from({ length: 15 }, () => Array<number>(15).fill(0)),
      turnPlayerId: 'p1',
      lastMove: null,
      colors: { p1: 'black', p2: 'white' },
    },
  }
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
    const point = wrapper.findAll('.board-point')[7 * 15 + 7]
    const touchClick = () => {
      const event = new MouseEvent('click', { bubbles: true, cancelable: true })
      Object.defineProperty(event, 'pointerType', { value: 'touch' })
      point?.element.dispatchEvent(event)
    }

    expect(wrapper.findAll('.board-point.star')).toHaveLength(5)
    touchClick()
    await nextTick()
    expect(action).not.toHaveBeenCalled()
    expect(point?.find('.stone-preview').classes()).toContain('active')

    touchClick()
    await nextTick()
    expect(action).toHaveBeenCalledWith('place', { row: 7, column: 7 })
  })
})
