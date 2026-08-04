import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import GameView from './GameView.vue'
import type { ArcadeSnapshot } from '@game-hall/plugin-sdk'

const snapshot = {
  phase: 'playing',
  roundNumber: 1,
  actions: { canAct: true },
  game: {
    minimum: 1,
    maximum: 20,
    maxAttempts: 6,
    remainingAttempts: 5,
    guesses: [10],
    hint: 'higher',
    answer: null,
    won: false,
  },
} as unknown as ArcadeSnapshot

describe('number vault plugin view', () => {
  it('shows server feedback without revealing the answer', () => {
    const wrapper = mount(GameView, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('答案更大一些')
    expect(wrapper.text()).toContain('还剩 5 次机会')
    expect(wrapper.text()).not.toContain('答案：')
    expect(wrapper.get('[aria-label="猜测数字"]').exists()).toBe(true)
  })
})
