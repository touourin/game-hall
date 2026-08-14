import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiIconButton from './UiIconButton.vue'

describe('UiIconButton', () => {
  it('keeps a safe native type and accessible attributes', () => {
    const wrapper = mount(UiIconButton, {
      props: { compact: true },
      attrs: { 'aria-label': '关闭弹窗', disabled: true },
      slots: { default: '×' },
    })

    expect(wrapper.attributes()).toMatchObject({
      type: 'button',
      'aria-label': '关闭弹窗',
      disabled: '',
    })
    expect(wrapper.classes()).toContain('ui-icon-button--compact')
  })
})
