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
    await wrapper.get('input[autocomplete="username"]').setValue('round_player')
    await wrapper.get('input[autocomplete="nickname"]').setValue('游戏昵称')
    const passwords = wrapper.findAll('input[autocomplete="new-password"]')
    await passwords[0]!.setValue('secret123')
    await passwords[1]!.setValue('secret123')
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

  it('verifies an optional email in place before registration', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    await wrapper.findAll('.account-mode button')[1]!.trigger('click')
    await wrapper.get('input[autocomplete="username"]').setValue('mail_player')
    await wrapper.get('input[autocomplete="nickname"]').setValue('邮箱玩家')
    await wrapper.get('input[autocomplete="email"]').setValue(' player@example.com ')
    const sendButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('发送验证码'))
    await sendButton?.trigger('click')
    expect(wrapper.emitted('registrationEmailCode')).toEqual([
      ['player@example.com'],
    ])
    await wrapper.setProps({
      registrationEmailRequestedFor: 'player@example.com',
      registrationEmailMessage: '验证码已经发送',
    })
    const emailCodeInput = wrapper.get(
      'input[autocomplete="one-time-code"]',
    )
    expect(emailCodeInput.attributes('placeholder')).toBe(
      '输入邮件中的 6 位验证码',
    )
    await emailCodeInput.setValue('123456')
    const passwords = wrapper.findAll('input[autocomplete="new-password"]')
    await passwords[0]!.setValue('secret123')
    await passwords[1]!.setValue('secret123')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('register')).toEqual([
      [
        {
          username: 'mail_player',
          playerName: '邮箱玩家',
          password: 'secret123',
          email: 'player@example.com',
          emailCode: '123456',
        },
      ],
    ])
    expect(wrapper.text()).toContain('请先在这里完成验证')
  })

  it('allows an email-style login name up to 50 characters', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    const usernameInput = wrapper.get('input[autocomplete="username"]')

    expect(usernameInput.attributes('maxlength')).toBe('50')
    expect(usernameInput.attributes('placeholder')).toBe(
      '2–50 个字符，仅用于登录',
    )
    await usernameInput.setValue('gantianyu+game.account@sinodata.example')

    expect((usernameInput.element as HTMLInputElement).value).toBe(
      'gantianyu+game.account@sinodata.example',
    )
  })

  it('rejects Chinese and unsupported symbols in new account names', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    await wrapper.findAll('.account-mode button')[1]!.trigger('click')
    const usernameInput = wrapper.get('input[autocomplete="username"]')
    await usernameInput.setValue('中文账号')
    await wrapper.get('input[autocomplete="nickname"]').setValue('中文昵称')
    const passwords = wrapper.findAll('input[autocomplete="new-password"]')
    await passwords[0]!.setValue('secret123')
    await passwords[1]!.setValue('secret123')

    expect(usernameInput.attributes('pattern')).toBe('[A-Za-z0-9._@+\\-]+')
    expect(usernameInput.attributes('aria-invalid')).toBe('true')
    expect(wrapper.get('.field-hint').text()).toContain('不支持中文')
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()

    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('register')).toBeUndefined()
    expect(wrapper.get('[role="alert"]').text()).toContain(
      '账号名只能使用英文字母、数字及 . _ @ + -',
    )
  })

  it('accepts documented symbols in new account names', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    await wrapper.findAll('.account-mode button')[1]!.trigger('click')
    await wrapper.get('input[autocomplete="username"]').setValue(
      'player.name_01+test@example-game',
    )
    await wrapper.get('input[autocomplete="nickname"]').setValue('玩家昵称')
    const passwords = wrapper.findAll('input[autocomplete="new-password"]')
    await passwords[0]!.setValue('secret123')
    await passwords[1]!.setValue('secret123')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('register')?.[0]?.[0]).toMatchObject({
      username: 'player.name_01+test@example-game',
    })
  })

  it('keeps existing Unicode account names available for login', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    const inputs = wrapper.findAll('input')
    await inputs[0]!.setValue('旧账号')
    await inputs[1]!.setValue('secret123')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('login')).toEqual([
      [{ username: '旧账号', password: 'secret123' }],
    ])
  })

  it('allows a one-character game nickname for registration and guests', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null },
    })
    await wrapper.findAll('.account-mode button')[1]!.trigger('click')
    await wrapper.get('input[autocomplete="username"]').setValue('single_name')
    await wrapper.get('input[autocomplete="nickname"]').setValue('王')
    const registerPasswords = wrapper.findAll(
      'input[autocomplete="new-password"]',
    )
    await registerPasswords[0]!.setValue('secret123')
    await registerPasswords[1]!.setValue('secret123')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('register')?.[0]?.[0]).toMatchObject({
      playerName: '王',
    })

    await wrapper.findAll('.account-mode button')[2]!.trigger('click')
    await wrapper.get('input').setValue('李')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('guest')?.[0]?.[0]).toEqual({ playerName: '李' })
  })

  it('supports requesting a code and confirming a password reset', async () => {
    const wrapper = mount(AccountGate, {
      props: { busy: false, error: null, passwordResetState: 'idle' },
    })

    await wrapper.get('.forgot-password-button').trigger('click')
    await wrapper.get('input[autocomplete="username"]').setValue('player@example.com')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('passwordResetCode')).toEqual([
      ['player@example.com'],
    ])

    await wrapper.setProps({ passwordResetState: 'code-sent' })
    const resetCodeInput = wrapper.get(
      'input[autocomplete="one-time-code"]',
    )
    expect(resetCodeInput.attributes('placeholder')).toBe(
      '输入邮件中的 6 位验证码',
    )
    await resetCodeInput.setValue('123456')
    const passwordInputs = wrapper.findAll('input[autocomplete="new-password"]')
    await passwordInputs[0]!.setValue('new-secret')
    await passwordInputs[1]!.setValue('new-secret')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('passwordResetConfirm')).toEqual([
      [
        {
          identifier: 'player@example.com',
          code: '123456',
          password: 'new-secret',
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
    expect(wrapper.get('.ui-button--primary').attributes('disabled')).toBeDefined()
  })
})
