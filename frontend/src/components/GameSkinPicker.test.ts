import { mount } from '@vue/test-utils'
import GameSkinPicker from './GameSkinPicker.vue'

describe('GameSkinPicker', () => {
  it('previews five tiered board and card treatments and emits a selection', async () => {
    const wrapper = mount(GameSkinPicker, {
      props: { modelValue: 'classic-wood', kind: 'board' },
    })

    expect(wrapper.text()).toContain('我的棋盘画风')
    expect(wrapper.text()).toContain('仅影响你看到的棋盘和棋子 · 开局后保持')
    const options = wrapper.findAll('[data-game-skin-option]')
    expect(options).toHaveLength(5)
    expect(options[0]?.attributes('data-game-skin-option')).toBe('classic-wood')
    expect(options[4]?.attributes('data-game-skin-option')).toBe('celestial-gold')
    expect(wrapper.findAll('.preview-board')).toHaveLength(5)
    expect(wrapper.findAll('.preview-table')).toHaveLength(5)
    expect(wrapper.text()).toContain('初级')
    expect(wrapper.text()).toContain('中级')
    expect(wrapper.text()).toContain('高级')

    await wrapper.get('button[data-game-skin-option="celestial-gold"]').trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([['celestial-gold']])
  })

  it('uses poker-specific copy for card games', () => {
    const wrapper = mount(GameSkinPicker, {
      props: { modelValue: 'classic-wood', kind: 'cards' },
    })

    expect(wrapper.text()).toContain('我的扑克画风')
    expect(wrapper.text()).toContain('仅影响你看到的牌桌和扑克 · 开局后保持')
  })

  it('opens the compact mobile picker and closes it after selection', async () => {
    const wrapper = mount(GameSkinPicker, {
      props: { modelValue: 'classic-wood', kind: 'board' },
    })

    expect(wrapper.get('.game-skin-mobile-trigger').text()).toContain('原木经典')
    await wrapper.get('.game-skin-mobile-trigger').trigger('click')
    expect(wrapper.get('.game-skin-options').classes()).toContain('is-mobile-open')

    await wrapper.get('button[data-game-skin-option="midnight-neon"]').trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([['midnight-neon']])
    expect(wrapper.get('.game-skin-options').classes()).not.toContain('is-mobile-open')
  })
})
