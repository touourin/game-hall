import { mount } from '@vue/test-utils'
import CleanupRoomButton from './CleanupRoomButton.vue'

describe('CleanupRoomButton', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('requires confirmation before permanently cleaning a room', async () => {
    const wrapper = mount(CleanupRoomButton, {
      props: { roomCode: 'OLD1' },
      attachTo: document.body,
    })

    await wrapper.get('.cleanup-room-button').trigger('click')
    expect(document.body.textContent).toContain('房间 OLD1')
    expect(document.body.textContent).toContain('彻底清理这个房间')
    const confirm = Array.from(document.body.querySelectorAll('button')).find(
      (button) => button.textContent?.includes('确认清理'),
    ) as HTMLButtonElement
    confirm.click()
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('confirm')).toHaveLength(1)
    wrapper.unmount()
  })
})
