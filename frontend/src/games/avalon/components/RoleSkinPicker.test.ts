import { mount } from '@vue/test-utils'
import RoleSkinPicker from './RoleSkinPicker.vue'

describe('RoleSkinPicker', () => {
  it('previews all five skins by tier and emits the selected one', async () => {
    const wrapper = mount(RoleSkinPicker, {
      props: { modelValue: 'classic-tabletop' },
    })

    expect(wrapper.text()).toContain('仅影响你看到的身份卡 · 开局后锁定')
    const options = wrapper.findAll('.role-skin-options button')
    expect(options).toHaveLength(5)
    expect(options[0]?.attributes('data-role-skin')).toBe('classic-tabletop')
    expect(options[4]?.attributes('data-role-skin')).toBe('grail-myth')
    expect(wrapper.findAll('.role-skin-preview img')).toHaveLength(5)
    expect(wrapper.text()).toContain('基础')
    expect(wrapper.text()).toContain('终极')

    await wrapper
      .get('button[data-role-skin="grail-myth"]')
      .trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([['grail-myth']])
  })
})
