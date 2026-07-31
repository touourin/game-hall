import { mount } from '@vue/test-utils'
import AccountGate from './AccountGate.vue'

describe('AccountGate', () => {
  it('submits account credentials for login', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    const inputs = wrapper.findAll('input')

    await inputs[0]!.setValue('round_player')
    await inputs[1]!.setValue('secret123')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('login')).toEqual([
      [{ username: 'round_player', password: 'secret123' }],
    ])
  })

  it('registers a stable account with a separate display name', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    await wrapper.findAll('.account-mode button')[1]!.trigger('click')
    const inputs = wrapper.findAll('input')

    await inputs[0]!.setValue('round_player')
    await inputs[1]!.setValue('桌上名字')
    await inputs[2]!.setValue('secret123')
    await inputs[3]!.setValue('secret123')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('register')).toEqual([
      [
        {
          username: 'round_player',
          password: 'secret123',
          displayName: '桌上名字',
        },
      ],
    ])
  })

  it('shows server errors and blocks submission while busy', () => {
    const wrapper = mount(AccountGate, {
      props: { busy: true, error: '账号或密码不正确' },
    })

    expect(wrapper.get('[role="alert"]').text()).toContain('账号或密码不正确')
    expect(wrapper.get('.primary-button').attributes('disabled')).toBeDefined()
  })
})
