import { mount } from '@vue/test-utils'
import RoleSkinPicker from './RoleSkinPicker.vue'

describe('RoleSkinPicker', () => {
  it('opens a labeled eight-role preview before selecting a skin', async () => {
    const wrapper = mount(RoleSkinPicker, {
      props: { modelValue: 'classic-tabletop' },
      global: { stubs: { Teleport: true } },
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

    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
    const modal = wrapper.get('.role-skin-modal')
    expect(modal.attributes('data-tier')).toBe('终极')
    expect(modal.text()).toContain('圣杯神话')
    expect(modal.findAll('.role-skin-portrait')).toHaveLength(8)
    expect(modal.findAll('.role-skin-portrait img')).toHaveLength(8)
    expect(modal.text()).toContain('梅林')
    expect(modal.text()).toContain('派西维尔')
    expect(modal.text()).toContain('亚瑟的忠臣')
    expect(modal.text()).toContain('刺客')
    expect(modal.text()).toContain('莫甘娜')
    expect(modal.text()).toContain('莫德雷德')
    expect(modal.text()).toContain('奥伯伦')
    expect(modal.text()).toContain('莫德雷德的爪牙')
    expect(
      modal.get('[data-role="merlin"] img').attributes('style'),
    ).toContain('--role-art-scale: 1')
    expect(
      modal.get('[data-role="morgana"] img').attributes('style'),
    ).toContain('--role-art-scale: 1.1')
    expect(
      modal.get('[data-role="assassin"] img').attributes('style'),
    ).toContain('--role-art-scale: 1.18')

    await modal.get('.role-skin-use-button').trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([['grail-myth']])
    expect(wrapper.find('.role-skin-modal').exists()).toBe(false)
  })

  it('keeps the royal-codex frame intact while scaling Merlin inside it', async () => {
    const wrapper = mount(RoleSkinPicker, {
      props: { modelValue: 'classic-tabletop' },
      global: { stubs: { Teleport: true } },
    })

    await wrapper
      .get('button[data-role-skin="royal-codex"]')
      .trigger('click')

    const merlin = wrapper.get('[data-role="merlin"]')
    expect(merlin.find('.role-skin-artwork.preserves-frame').exists()).toBe(true)
    expect(merlin.find('.role-skin-inner-artwork').exists()).toBe(true)
    expect(
      merlin.get('.role-skin-inner-artwork').attributes('style'),
    ).toContain('--role-art-scale: 1.16')
  })
})
