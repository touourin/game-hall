import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseModal from './BaseModal.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('BaseModal', () => {
  it('renders an accessible dialog in the document body', () => {
    const wrapper = mount(BaseModal, {
      props: { title: '规则设置', description: '修改下一局规则' },
      slots: { default: '<button type="button">保存</button>' },
    })

    const dialog = document.body.querySelector('[role="dialog"]')
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    expect(dialog?.textContent).toContain('规则设置')
    expect(dialog?.textContent).toContain('修改下一局规则')
    wrapper.unmount()
  })

  it('emits close from the close button and Escape key', async () => {
    const wrapper = mount(BaseModal, { props: { title: '测试弹窗' } })
    const closeButton = document.body.querySelector<HTMLButtonElement>('[aria-label="关闭弹窗"]')!

    closeButton.click()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('close')).toHaveLength(2)
    wrapper.unmount()
  })

  it('can disable every dismiss action for a blocking flow', async () => {
    const wrapper = mount(BaseModal, {
      props: { title: '必须完成', closable: false },
    })

    expect(document.body.querySelector('[aria-label="关闭弹窗"]')).toBeNull()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    document.body.querySelector<HTMLElement>('.base-modal-backdrop')?.click()
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('close')).toBeUndefined()
    wrapper.unmount()
  })

  it('supports an inline mobile sheet while keeping the shared shell', () => {
    const wrapper = mount(BaseModal, {
      props: {
        ariaLabel: '手机设置',
        panelClass: 'settings-modal',
        mobileSheet: true,
        inline: true,
      },
    })

    expect(wrapper.get('[role="dialog"]').attributes('aria-label')).toBe('手机设置')
    expect(wrapper.get('.base-modal-backdrop').classes()).toContain(
      'base-modal-backdrop--mobile-sheet',
    )
    expect(wrapper.get('.base-modal-card').classes()).toEqual(
      expect.arrayContaining([
        'settings-modal',
        'base-modal-card--mobile-sheet',
      ]),
    )
  })
})
