import { mount } from '@vue/test-utils'
import ArtworkSkinPicker from './ArtworkSkinPicker.vue'
import type { ArtworkSkinOption } from './uiTypes'

const options: ArtworkSkinOption[] = [
  { id: 'classic', name: '经典', description: '清晰直观', tier: '基础', preview: '/classic.webp', items: [{ id: 'one', name: '角色一', group: '阵营一', artwork: '/one.webp', framing: { scale: 1, originXPercent: 50, originYPercent: 50 } }] },
  { id: 'deluxe', name: '典藏', description: '精致画风', tier: '高级', preview: '/deluxe.webp', items: [{ id: 'two', name: '角色二', group: '阵营二', artwork: '/two.webp', framing: { scale: 1.1, originXPercent: 50, originYPercent: 29, preserveFrame: true } }] },
]

describe('ArtworkSkinPicker', () => {
  it('previews caller-provided artwork before selecting it', async () => {
    const wrapper = mount(ArtworkSkinPicker, { props: { modelValue: 'classic', options, title: '身份画风', itemName: '身份' }, global: { stubs: { Teleport: true } } })

    expect(wrapper.findAll('.artwork-skin-options button')).toHaveLength(2)
    await wrapper.get('button[data-artwork-skin="deluxe"]').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
    expect(wrapper.get('.artwork-skin-modal').text()).toContain('典藏')
    expect(wrapper.get('.artwork-skin-gallery').text()).toContain('角色二')
    expect(wrapper.find('.artwork-skin-inner-art').exists()).toBe(true)
    await wrapper.get('.artwork-skin-modal footer button').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([['deluxe']])
  })
})
