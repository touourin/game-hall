import { mount } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'
import type { AccountProfile } from '../account'
import SettingsModal from './SettingsModal.vue'

const AvatarCropStub = defineComponent({
  name: 'AvatarCropModal',
  props: ['file'],
  emits: ['close', 'confirm'],
  template: '<div class="avatar-crop-stub" />',
})

const defaultAccount: AccountProfile = {
  id: 'account-1',
  username: 'login_account',
  playerName: '当前昵称',
  avatarType: 'preset',
  avatarPreset: 'moon-fox',
  avatarUrl: '/avatars/moon-fox.webp',
  createdAt: '2026-08-01T00:00:00Z',
  isGuest: false,
}

function mountSettings(
  account: Partial<AccountProfile> = {},
  stubAvatarCrop = false,
) {
  return mount(SettingsModal, {
    props: {
      account: { ...defaultAccount, ...account },
      busy: false,
      error: null,
    },
    global: stubAvatarCrop
      ? { stubs: { AvatarCropModal: AvatarCropStub } }
      : undefined,
  })
}

describe('SettingsModal', () => {
  it('allows renaming to a one-character game nickname', async () => {
    const wrapper = mountSettings({ playerName: '旧昵称' })
    const nameInput = wrapper.get(
      '.settings-section form input:not([disabled])',
    )

    expect(nameInput.attributes('minlength')).toBe('1')
    await nameInput.setValue('王')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('rename')).toEqual([['王']])
  })

  it('keeps the account name fixed and submits a new game nickname', async () => {
    const wrapper = mountSettings({ playerName: '旧昵称' })
    const inputs = wrapper.findAll<HTMLInputElement>(
      '.settings-section form input',
    )

    expect(wrapper.get('h2').text()).toBe('设置')
    expect(inputs[0]!.element.value).toBe('login_account')
    expect(inputs[0]!.attributes('disabled')).toBeDefined()
    await inputs[1]!.setValue('新昵称')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('rename')).toEqual([['新昵称']])
  })

  it('requests and verifies a binding email without losing the target address', async () => {
    const wrapper = mountSettings()
    const emailSection = wrapper.get('.email-settings-section')
    await emailSection.get('input[type="email"]').setValue(' player@example.com ')
    const sendButton = emailSection
      .findAll('button')
      .find((button) => button.text().includes('发送验证码'))

    await sendButton?.trigger('click')
    expect(wrapper.emitted('requestEmailCode')).toEqual([
      ['player@example.com'],
    ])

    await wrapper.setProps({
      emailCodeSent: true,
      emailRequestedFor: 'player@example.com',
    })
    const refreshedSection = wrapper.get('.email-settings-section')
    const bindingCodeInput = refreshedSection.get(
      'input[autocomplete="one-time-code"]',
    )
    expect(bindingCodeInput.attributes('placeholder')).toBe(
      '输入邮件中的 6 位验证码',
    )
    await bindingCodeInput.setValue('123456')
    await refreshedSection.get('form').trigger('submit')

    expect(wrapper.emitted('verifyEmail')).toEqual([
      [{ email: 'player@example.com', code: '123456' }],
    ])
  })

  it('requires a code sent to the current email before unbinding', async () => {
    const wrapper = mountSettings({
      email: 'player@example.com',
      emailVerified: true,
    })

    await wrapper.get('.email-unbind-trigger').trigger('click')
    expect(wrapper.text()).toContain('解绑后将无法通过邮箱找回密码')
    await wrapper
      .get('.email-unbind-panel button.ui-button')
      .trigger('click')
    expect(wrapper.emitted('requestEmailUnbindCode')).toEqual([[]])

    await wrapper.setProps({
      emailUnbindCodeSent: true,
      emailMessage: '解绑验证码已经发送',
    })
    const unbindingCodeInput = wrapper.get(
      '.email-unbind-panel input[autocomplete="one-time-code"]',
    )
    expect(unbindingCodeInput.attributes('placeholder')).toBe(
      '输入邮件中的 6 位验证码',
    )
    await unbindingCodeInput.setValue('654321')
    const confirmButton = wrapper
      .findAll('.email-unbind-panel button')
      .find((button) => button.text().includes('验证并解绑'))
    await confirmButton?.trigger('click')

    expect(wrapper.emitted('unbindEmail')).toEqual([['654321']])
  })

  it('previews a built-in avatar and only saves it after confirmation', async () => {
    const wrapper = mountSettings()
    const presets = wrapper.findAll('.avatar-preset-grid button')

    expect(presets).toHaveLength(8)
    await presets[1]!.trigger('click')

    expect(wrapper.emitted('avatarPreset')).toBeUndefined()
    expect(presets[1]!.classes()).toContain('selected')
    expect(wrapper.get('.current-avatar img').attributes('src')).toBe(
      '/avatars/jade-owl.webp',
    )
    expect(wrapper.text()).toContain('头像更换尚未保存')

    await wrapper.get('.avatar-confirm-button').trigger('click')
    expect(wrapper.emitted('avatarPreset')).toEqual([['jade-owl']])
  })

  it('can discard a staged avatar without changing the account', async () => {
    const wrapper = mountSettings()

    await wrapper.findAll('.avatar-preset-grid button')[2]!.trigger('click')
    await wrapper.get('.avatar-discard-button').trigger('click')

    expect(wrapper.emitted('avatarPreset')).toBeUndefined()
    expect(wrapper.get('.current-avatar img').attributes('src')).toBe(
      '/avatars/moon-fox.webp',
    )
    expect(wrapper.get('.avatar-confirm-button').attributes('disabled')).toBeDefined()
  })

  it('validates custom avatar type before opening the crop step', async () => {
    const wrapper = mountSettings()
    const input = wrapper.get<HTMLInputElement>('.avatar-file-input')
    Object.defineProperty(input.element, 'files', {
      configurable: true,
      value: [new File(['text'], 'avatar.txt', { type: 'text/plain' })],
    })

    await input.trigger('change')

    expect(wrapper.text()).toContain('仅支持 JPEG、PNG、WebP 或 GIF')
    expect(wrapper.emitted('avatarUpload')).toBeUndefined()
  })

  it('stages the cropped upload and only saves it after confirmation', async () => {
    const wrapper = mountSettings({}, true)
    const source = new File(['image'], 'portrait.png', { type: 'image/png' })
    const input = wrapper.get<HTMLInputElement>('.avatar-file-input')
    Object.defineProperty(input.element, 'files', {
      configurable: true,
      value: [source],
    })

    await input.trigger('change')

    expect(wrapper.find('.avatar-crop-stub').exists()).toBe(true)
    expect(wrapper.emitted('avatarUpload')).toBeUndefined()

    const cropped = new File(['cropped'], 'portrait-avatar.webp', {
      type: 'image/webp',
    })
    wrapper.getComponent(AvatarCropStub).vm.$emit('confirm', cropped)
    await nextTick()

    expect(wrapper.find('.avatar-crop-stub').exists()).toBe(false)
    expect(wrapper.emitted('avatarUpload')).toBeUndefined()
    expect(wrapper.text()).toContain('已完成裁剪：portrait-avatar.webp')

    await wrapper.get('.avatar-confirm-button').trigger('click')
    expect(wrapper.emitted('avatarUpload')).toEqual([[cropped]])
  })

  it('offers all four material UI skins and applies the selected one', async () => {
    const wrapper = mountSettings()

    expect(
      wrapper.findAll('.theme-copy strong').map((name) => name.text()),
    ).toEqual(['橘光晴釉', '幽蓝冷钢', '月白云瓷', '曜石黑钛'])
    expect(
      wrapper.findAll('.theme-copy small').map((description) => description.text()),
    ).toEqual([
      '奶油暖杏、柔白陶面与鲜润橘釉',
      '近黑军蓝、深蓝钢面与冰蓝辉光',
      '月白冷灰、柔白云瓷与灰绿釉面',
      '曜石黑陶、石墨烟面与冷银钛光',
    ])
    expect(wrapper.text()).toContain('幽蓝冷钢')
    expect(wrapper.text()).toContain('曜石黑钛')
    expect(wrapper.text()).toContain('月白云瓷')
    expect(wrapper.text()).toContain('橘光晴釉')
    expect(wrapper.text()).not.toContain('暖钛陶瓷')

    const tangerineGlaze = wrapper
      .findAll('.settings-theme-list button')
      .find((button) => button.text().includes('橘光晴釉'))
    await tangerineGlaze?.trigger('click')

    expect(document.documentElement.dataset.theme).toBe('amber')
    expect(document.documentElement.dataset.colorScheme).toBe('light')
    expect(localStorage.getItem('game-hall:theme')).toBe('amber')
  })
})
