import { mount } from '@vue/test-utils'
import SettingsModal from './SettingsModal.vue'

describe('SettingsModal', () => {
  it('keeps the account name fixed and submits a new game nickname', async () => {
    const wrapper = mount(SettingsModal, {
      props: {
        account: {
          id: 'account-1',
          username: 'login_account',
          playerName: '旧昵称',
          nextRenameAt: null,
          createdAt: '2026-08-01T00:00:00Z',
        },
        busy: false,
        error: null,
      },
    })
    const inputs = wrapper.findAll('input')

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
          createdAt: '2026-08-01T00:00:00Z',
        },
        busy: false,
        error: null,
      },
    })

    expect(wrapper.text()).toContain('每 30 天只能改名一次')
    expect(wrapper.findAll('input')[1]!.attributes('disabled')).toBeDefined()
  })
})
