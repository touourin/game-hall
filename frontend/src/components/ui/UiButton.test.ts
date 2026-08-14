import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiButton from './UiButton.vue'

describe('UiButton', () => {
  it('uses a safe native button type by default', () => {
    const wrapper = mount(UiButton, { slots: { default: '继续' } })

    expect(wrapper.element.tagName).toBe('BUTTON')
    expect(wrapper.attributes('type')).toBe('button')
    expect(wrapper.classes()).toContain('ui-button--secondary')
  })

  it('applies variants and layout without hiding native attributes', () => {
    const wrapper = mount(UiButton, {
      props: { variant: 'primary', block: true, compact: true, type: 'submit' },
      attrs: { disabled: true, 'aria-label': '保存规则' },
    })

    expect(wrapper.classes()).toEqual(expect.arrayContaining([
      'ui-button--primary',
      'ui-button--block',
      'ui-button--compact',
    ]))
    expect(wrapper.attributes()).toMatchObject({
      type: 'submit',
      disabled: '',
      'aria-label': '保存规则',
    })
  })
})
