import { mount } from '@vue/test-utils'
import RoomExitButton from './RoomExitButton.vue'

describe('RoomExitButton', () => {
  it('supports a game-specific multiplayer elimination label', async () => {
    const wrapper = mount(RoomExitButton, {
      props: {
        mode: 'multiplayer-active',
        abandonLabel: '退出并淘汰',
      },
    })

    await wrapper.get('.exit-room-trigger').trigger('click')
    expect(wrapper.get('.danger-button').text()).toContain('退出并淘汰')
    await wrapper.get('.danger-button').trigger('click')
    expect(wrapper.emitted('abandon')).toHaveLength(1)
  })
})
