import { mount } from '@vue/test-utils'
import RoomDissolveButton from './RoomDissolveButton.vue'

describe('RoomDissolveButton', () => {
  it('requires confirmation before dissolving the room', async () => {
    const wrapper = mount(RoomDissolveButton)

    await wrapper.get('.dissolve-room-trigger').trigger('click')
    expect(wrapper.get('.dissolve-room-modal').text()).toContain(
      '所有等待中的玩家都会返回大厅',
    )
    expect(wrapper.emitted('confirm')).toBeUndefined()

    await wrapper.get('.dissolve-room-actions .danger').trigger('click')
    expect(wrapper.emitted('confirm')).toHaveLength(1)
    expect(wrapper.find('.dissolve-room-modal').exists()).toBe(false)
  })
})
