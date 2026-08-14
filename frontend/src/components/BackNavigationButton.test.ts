import { mount } from '@vue/test-utils'
import BackNavigationButton from './BackNavigationButton.vue'

describe('BackNavigationButton', () => {
  it('provides the shared top-left navigation control', async () => {
    const wrapper = mount(BackNavigationButton, {
      props: { label: '返回游戏大厅' },
    })

    expect(wrapper.classes()).toContain('ui-icon-button')
    expect(wrapper.classes()).toContain('back-navigation-button')
    expect(wrapper.attributes('aria-label')).toBe('返回游戏大厅')

    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('forwards the disabled state', () => {
    const wrapper = mount(BackNavigationButton, {
      props: { disabled: true },
    })

    expect(wrapper.attributes('disabled')).toBeDefined()
  })
})
