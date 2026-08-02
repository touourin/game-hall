import { mount } from '@vue/test-utils'
import AccessGate from './AccessGate.vue'

describe('AccessGate', () => {
  it('shows the fixed password and submits it without surrounding whitespace', async () => {
    const wrapper = mount(AccessGate, {
      props: { checking: false, busy: false, error: null },
    })
    const input = wrapper.get('input')

    expect(input.attributes('type')).toBe('password')
    expect(wrapper.text()).toContain('访问密码固定为 avalon')
    expect(wrapper.text()).not.toContain('游戏')
    expect(wrapper.text()).not.toContain('圆桌')
    expect(wrapper.text()).not.toContain('阿瓦隆')

    await input.setValue('  avalon  ')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('unlock')).toEqual([['avalon']])
  })

  it('renders the server error and blocks duplicate submissions', async () => {
    const wrapper = mount(AccessGate, {
      props: { checking: false, busy: true, error: '密码不正确，请重新输入' },
    })

    expect(wrapper.get('[role="alert"]').text()).toContain('密码不正确')
    expect(wrapper.get('button').attributes('disabled')).toBeDefined()
  })
})
