import { mount } from '@vue/test-utils'
import RoomKickButton from './RoomKickButton.vue'

describe('RoomKickButton', () => {
  it('requires confirmation before removing a player', async () => {
    const wrapper = mount(RoomKickButton, {
      props: { playerName: '玩家二' },
    })

    await wrapper.get('[aria-label="移除玩家二"]').trigger('click')
    expect(wrapper.get('.kick-player-modal').text()).toContain('移除玩家二？')
    expect(wrapper.emitted('confirm')).toBeUndefined()

    await wrapper.get('.kick-player-actions .danger').trigger('click')
    expect(wrapper.emitted('confirm')).toHaveLength(1)
    expect(wrapper.find('.kick-player-modal').exists()).toBe(false)
  })
})
