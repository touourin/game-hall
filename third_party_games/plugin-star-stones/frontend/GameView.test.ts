import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import GameView from './GameView.vue'
import type { ArcadeSnapshot } from '@game-hall/plugin-sdk'

const snapshot = {
  phase: 'playing',
  self: { id: 'p1' },
  players: [
    { id: 'p1', name: '玩家一' },
    { id: 'p2', name: '玩家二' },
  ],
  game: {
    startingStones: 15,
    maxTake: 3,
    remaining: 15,
    currentPlayerId: 'p1',
    moves: [],
    winnerPlayerId: null,
    isMyTurn: true,
  },
} as unknown as ArcadeSnapshot

describe('star stones plugin view', () => {
  it('renders the shared state and all legal take actions', () => {
    const wrapper = mount(GameView, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.stone-field i')).toHaveLength(15)
    expect(wrapper.findAll('.take-actions button')).toHaveLength(3)
    expect(wrapper.text()).toContain('轮到你取石')
  })
})
