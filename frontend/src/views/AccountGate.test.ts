import { mount } from '@vue/test-utils'
import AccountGate from './AccountGate.vue'

describe('AccountGate', () => {
  it('keeps all three account entry modes in one segmented control', () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })

    expect(wrapper.get('.account-mode').attributes('aria-label')).toBe(
      '登录、注册或游客入席',
    )
    expect(wrapper.findAll('.account-mode button').map((button) => button.text())).toEqual([
      '登录',
      '注册',
      '游客',
    ])
  })

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

  it('registers an account with a separate game nickname', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    await wrapper.findAll('.account-mode button')[1]!.trigger('click')
    const inputs = wrapper.findAll('input')

    await inputs[0]!.setValue('round_player')
    await inputs[1]!.setValue('游戏昵称')
    await inputs[2]!.setValue('secret123')
    await inputs[3]!.setValue('secret123')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('register')).toEqual([
      [
        {
          username: 'round_player',
          password: 'secret123',
          playerName: '游戏昵称',
        },
      ],
    ])
  })

  it('enters with only a temporary guest nickname', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    await wrapper.findAll('.account-mode button')[2]!.trigger('click')

    await wrapper.get('input').setValue('临时骑士')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('guest')).toEqual([
      [{ playerName: '临时骑士' }],
    ])
    expect(wrapper.text()).toContain('不会计入任何玩家战绩')
  })

  it('shows server errors and blocks submission while busy', () => {
    const wrapper = mount(AccountGate, {
      props: { busy: true, error: '账号或密码不正确' },
    })

    expect(wrapper.get('[role="alert"]').text()).toContain('账号或密码不正确')
    expect(wrapper.get('.primary-button').attributes('disabled')).toBeDefined()
  })
})
