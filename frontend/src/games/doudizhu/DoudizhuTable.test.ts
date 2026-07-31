import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import DoudizhuTable from './DoudizhuTable.vue'

function playingSnapshot(): ArcadeSnapshot {
  return {
    revision: 3,
    roomCode: 'TEST',
    gameKey: 'doudizhu',
    gameName: '斗地主',
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', name: '玩家一', seat: 0 },
    players: [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '玩家二', seat: 1, connected: true, isHost: false },
      { id: 'p3', name: '玩家三', seat: 2, connected: true, isHost: false },
    ],
    requiredPlayers: 3,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: { canStart: false, canRestart: false, canAct: true },
    game: {
      phase: 'playing',
      currentPlayerId: 'p1',
      bids: [{ seat: 0, score: 3 }],
      highestBid: 3,
      landlordPlayerId: 'p1',
      bottomCards: [],
      hand: [{ id: '3-spade', rank: 3, label: '3', suit: 'spade' }],
      cardCounts: { p1: 1, p2: 17, p3: 17 },
      teams: { p1: 'landlord', p2: 'farmer', p3: 'farmer' },
      lastPlay: null,
      lastPlayPlayerId: null,
    },
  }
}

describe('DoudizhuTable', () => {
  it('selects a card and submits its id', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: playingSnapshot() },
      global: { plugins: [pinia] },
    })

    await wrapper.get('.playing-card').trigger('click')
    expect(wrapper.get('.playing-card').classes()).toContain('selected')
    expect(wrapper.get('.play-actions .primary').attributes('disabled')).toBeUndefined()

    await wrapper.get('.play-actions .primary').trigger('click')
    expect(action).toHaveBeenCalledWith('play', { cardIds: ['3-spade'] })
  })
})
