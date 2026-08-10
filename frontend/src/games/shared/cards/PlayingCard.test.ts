import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PlayingCard from './PlayingCard.vue'

describe('PlayingCard', () => {
  it('renders a face card and its visual variants', () => {
    const wrapper = mount(PlayingCard, {
      props: { rank: 'A', suit: '♥', red: true, wild: true, size: 'hand' },
    })

    expect(wrapper.text()).toContain('A')
    expect(wrapper.text()).toContain('♥')
    expect(wrapper.classes()).toContain('red')
    expect(wrapper.classes()).toContain('wild')
  })

  it('renders a hidden card without exposing its rank', () => {
    const wrapper = mount(PlayingCard, {
      props: { rank: 'A', suit: '♠', faceDown: true, size: 'mini' },
    })

    expect(wrapper.classes()).toContain('card-back')
    expect(wrapper.text()).not.toContain('A')
  })

  it('emits selection from an interactive card', async () => {
    const wrapper = mount(PlayingCard, {
      props: { rank: 'K', interactive: true, ariaLabel: '黑桃 K' },
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })
})
