import { mount } from '@vue/test-utils'
import RoomDissolveButton from './RoomDissolveButton.vue'

describe('RoomDissolveButton', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('requires confirmation before dissolving the room', async () => {
    const wrapper = mount(RoomDissolveButton)

    await wrapper.get('.dissolve-room-trigger').trigger('click')
    expect(document.body.querySelector('.dissolve-room-modal')?.textContent).toContain(
      '所有等待中的玩家都会返回大厅',
    )
    expect(wrapper.emitted('confirm')).toBeUndefined()

    document.body.querySelector<HTMLButtonElement>('.confirm-modal-actions .ui-button--danger')!.click()
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('confirm')).toHaveLength(1)
    expect(document.body.querySelector('.dissolve-room-modal')).toBeNull()
    wrapper.unmount()
  })
})
