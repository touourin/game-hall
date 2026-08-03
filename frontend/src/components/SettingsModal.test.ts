import { mount } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'
import SettingsModal from './SettingsModal.vue'

const AvatarCropStub = defineComponent({
  name: 'AvatarCropModal',
  props: ['file'],
  emits: ['close', 'confirm'],
  template: '<div class="avatar-crop-stub" />',
})

describe('SettingsModal', () => {
  it('allows renaming to a one-character game nickname', async () => {
    const wrapper = mount(SettingsModal, {
      props: {
        account: {
          id: 'account-1',
          username: 'login_account',
          playerName: '旧昵称',
          nextRenameAt: null,
          avatarType: 'preset',
          avatarPreset: 'moon-fox',
          avatarUrl: '/avatars/moon-fox.webp',
          createdAt: '2026-08-01T00:00:00Z',
          isGuest: false,
        },
        busy: false,
        error: null,
      },
    })
    const nameInput = wrapper.get(
      '.settings-section form input:not([disabled])',
    )

    expect(nameInput.attributes('minlength')).toBe('1')
    await nameInput.setValue('王')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('rename')).toEqual([['王']])
  })

  it('keeps the account name fixed and submits a new game nickname', async () => {
    const wrapper = mount(SettingsModal, {
      props: {
        account: {
          id: 'account-1',
          username: 'login_account',
          playerName: '旧昵称',
          nextRenameAt: null,
          avatarType: 'preset',
          avatarPreset: 'moon-fox',
          avatarUrl: '/avatars/moon-fox.webp',
          createdAt: '2026-08-01T00:00:00Z',
        },
        busy: false,
        error: null,
      },
    })
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

  it('disables nickname changes until the cooldown expires', () => {
    const wrapper = mount(SettingsModal, {
      props: {
        account: {
          id: 'account-1',
          username: 'login_account',
          playerName: '当前昵称',
          nextRenameAt: '2099-01-01T00:00:00Z',
          avatarType: 'preset',
          avatarPreset: 'moon-fox',
          avatarUrl: '/avatars/moon-fox.webp',
          createdAt: '2026-08-01T00:00:00Z',
        },
        busy: false,
        error: null,
      },
    })

    expect(wrapper.text()).toContain('每 30 天只能改名一次')
    expect(
      wrapper.findAll('.settings-section form input')[1]!.attributes('disabled'),
    ).toBeDefined()
  })

  it('offers built-in avatars and emits the selected preset', async () => {
    const wrapper = mount(SettingsModal, {
      props: {
        account: {
          id: 'account-1',
          username: 'login_account',
          playerName: '当前昵称',
          nextRenameAt: null,
          avatarType: 'preset',
          avatarPreset: 'moon-fox',
          avatarUrl: '/avatars/moon-fox.webp',
          createdAt: '2026-08-01T00:00:00Z',
        },
        busy: false,
        error: null,
      },
    })

    const presets = wrapper.findAll('.avatar-preset-grid button')
    expect(presets).toHaveLength(8)
    await presets[1]!.trigger('click')
    expect(wrapper.emitted('avatarPreset')).toEqual([['jade-owl']])
  })

  it('validates custom avatar type before emitting an upload', async () => {
    const wrapper = mount(SettingsModal, {
      props: {
        account: {
          id: 'account-1',
          username: 'login_account',
          playerName: '当前昵称',
          nextRenameAt: null,
          avatarType: 'preset',
          avatarPreset: 'moon-fox',
          avatarUrl: '/avatars/moon-fox.webp',
          createdAt: '2026-08-01T00:00:00Z',
        },
        busy: false,
        error: null,
      },
    })
    const input = wrapper.get<HTMLInputElement>('.avatar-file-input')
    Object.defineProperty(input.element, 'files', {
      configurable: true,
      value: [new File(['text'], 'avatar.txt', { type: 'text/plain' })],
    })

    await input.trigger('change')

    expect(wrapper.text()).toContain('仅支持 JPEG、PNG、WebP 或 GIF')
    expect(wrapper.emitted('avatarUpload')).toBeUndefined()
  })

  it('opens the crop step and only uploads the confirmed result', async () => {
    const wrapper = mount(SettingsModal, {
      props: {
        account: {
          id: 'account-1',
          username: 'login_account',
          playerName: '当前昵称',
          nextRenameAt: null,
          avatarType: 'preset',
          avatarPreset: 'moon-fox',
          avatarUrl: '/avatars/moon-fox.webp',
          createdAt: '2026-08-01T00:00:00Z',
        },
        busy: false,
        error: null,
      },
      global: {
        stubs: { AvatarCropModal: AvatarCropStub },
      },
    })
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
    expect(wrapper.emitted('avatarUpload')).toEqual([[cropped]])
  })

  it('offers the three material UI skins and applies the selected one', async () => {
    const wrapper = mount(SettingsModal, {
      props: {
        account: {
          id: 'account-1',
          username: 'login_account',
          playerName: '当前昵称',
          nextRenameAt: null,
          avatarType: 'preset',
          avatarPreset: 'moon-fox',
          avatarUrl: '/avatars/moon-fox.webp',
          createdAt: '2026-08-01T00:00:00Z',
        },
        busy: false,
        error: null,
      },
    })

    expect(wrapper.text()).toContain('墨玉会所')
    expect(wrapper.text()).toContain('午夜铬光')
    expect(wrapper.text()).toContain('象牙棋院')

    const ivory = wrapper
      .findAll('.settings-theme-list button')
      .find((button) => button.text().includes('象牙棋院'))
    await ivory?.trigger('click')

    expect(document.documentElement.dataset.theme).toBe('royal')
    expect(localStorage.getItem('game-hall:theme')).toBe('royal')
  })
})
