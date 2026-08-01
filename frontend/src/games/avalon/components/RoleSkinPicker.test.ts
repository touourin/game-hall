import { mount } from '@vue/test-utils'
import RoleSkinPicker from './RoleSkinPicker.vue'

describe('RoleSkinPicker', () => {
  it('offers all three skins before the game and emits the selected one', async () => {
    const wrapper = mount(RoleSkinPicker, {
      props: { modelValue: 'dark-chronicle' },
    })

    expect(wrapper.text()).toContain('仅影响你看到的身份卡 · 开局后锁定')
    expect(wrapper.findAll('.role-skin-options button')).toHaveLength(3)

    await wrapper
      .get('button[data-role-skin="royal-codex"]')
      .trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([['royal-codex']])
  })
})
