import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ConfirmModal from './ConfirmModal.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('ConfirmModal', () => {
  it('renders shared confirmation actions and emits both outcomes', async () => {
    const wrapper = mount(ConfirmModal, {
      props: {
        title: '解散这个房间？',
        description: '所有玩家都会返回大厅。',
        confirmLabel: '确认解散',
        tone: 'danger',
      },
    })

    const dialog = document.body.querySelector<HTMLElement>('[role="dialog"]')!
    expect(dialog.textContent).toContain('解散这个房间？')
    dialog.querySelector<HTMLButtonElement>('.confirm')!.click()
    dialog.querySelector<HTMLButtonElement>('.cancel')!.click()
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('confirm')).toHaveLength(1)
    expect(wrapper.emitted('close')).toHaveLength(1)
    wrapper.unmount()
  })
})
