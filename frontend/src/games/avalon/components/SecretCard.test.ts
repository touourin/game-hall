import { mount } from '@vue/test-utils'
import SecretCard from './SecretCard.vue'

describe('SecretCard', () => {
  it('reveals private content only while pressed', async () => {
    const wrapper = mount(SecretCard, {
      props: { title: '梅林', subtitle: '亚瑟阵营' },
    })

    const card = wrapper.get('.secret-card')
    expect(wrapper.text()).not.toContain('梅林')
    await card.trigger('pointerdown')
    expect(wrapper.text()).toContain('梅林')
    expect(wrapper.emitted('seen')).toHaveLength(1)
    await card.trigger('pointerup')
    expect(wrapper.text()).not.toContain('梅林')
  })

  it('uses the locked skin without offering an in-game picker', async () => {
    const wrapper = mount(SecretCard, {
      props: {
        title: '梅林',
        subtitle: '亚瑟阵营',
        roleCode: 'merlin',
        roleSkin: 'royal-codex',
      },
    })

    expect(wrapper.find('.secret-card__art').exists()).toBe(false)
    expect(wrapper.find('.role-skin-options').exists()).toBe(false)
    expect(wrapper.get('.role-skin-lock').text()).toContain('王庭秘卷')
    expect(wrapper.get('.secret-card-shell').classes()).toContain(
      'has-role-art',
    )
    const card = wrapper.get('.secret-card')
    expect(card.attributes('data-skin')).toBe('royal-codex')

    await card.trigger('pointerdown')
    expect(wrapper.get('.secret-card__art').attributes('src')).toContain(
      'royal-codex',
    )
    await card.trigger('pointerup')
    expect(wrapper.find('.secret-card__art').exists()).toBe(false)
  })
})
