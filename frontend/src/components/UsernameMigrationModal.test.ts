import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import UsernameMigrationModal from './UsernameMigrationModal.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('UsernameMigrationModal', () => {
  it('blocks invalid account names and accepts a valid replacement', async () => {
    const wrapper = mount(UsernameMigrationModal, {
      props: {
        currentUsername: '旧账号',
        busy: false,
        error: null,
      },
      global: { stubs: { teleport: true } },
    })
    const input = wrapper.get('input[autocomplete="username"]')

    await input.setValue('仍是中文')
    expect(
      wrapper.get('input[autocomplete="username"]').attributes('aria-invalid'),
    ).toBe('true')
    expect(
      wrapper.get<HTMLButtonElement>('button[type="submit"]').element.disabled,
    ).toBe(true)

    await wrapper.get('input[autocomplete="username"]').setValue('new.player_01')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('migrate')).toEqual([['new.player_01']])
    wrapper.unmount()
  })

  it('cannot be dismissed but still allows logging out', async () => {
    const wrapper = mount(UsernameMigrationModal, {
      props: {
        currentUsername: '旧账号',
        busy: false,
        error: null,
      },
      global: { stubs: { teleport: true } },
    })

    expect(wrapper.find('[aria-label="关闭弹窗"]').exists()).toBe(false)
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.get('button[type="button"]').trigger('click')

    expect(wrapper.emitted('logout')).toEqual([[]])
    wrapper.unmount()
  })
})
