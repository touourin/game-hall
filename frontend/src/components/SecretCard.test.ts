import { mount } from '@vue/test-utils'
import SecretCard from './SecretCard.vue'

describe('SecretCard', () => {
  it('reveals private content only while pressed', async () => {
    const wrapper = mount(SecretCard, {
      props: { title: '梅林', subtitle: '亚瑟阵营' },
    })

    expect(wrapper.classes()).toEqual(['secret-card'])
    expect(wrapper.text()).not.toContain('梅林')
    await wrapper.trigger('pointerdown')
    expect(wrapper.text()).toContain('梅林')
    expect(wrapper.emitted('seen')).toHaveLength(1)
    await wrapper.trigger('pointerup')
    expect(wrapper.text()).not.toContain('梅林')
  })
})
