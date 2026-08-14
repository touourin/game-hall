import { mount } from '@vue/test-utils'
import RoomKickButton from './RoomKickButton.vue'

describe('RoomKickButton', () => {
  it('requires confirmation before removing a player', async () => {
    const wrapper = mount(RoomKickButton, {
      props: { playerName: 'AI玩家 6' },
    })

    await wrapper.get('[aria-label="移除AI玩家 6"]').trigger('click')
    const modal = document.body.querySelector('.kick-player-modal')
    expect(modal?.textContent).toContain('移除AI玩家 6？')
    expect(modal?.parentElement?.parentElement).toBe(document.body)
    expect(wrapper.emitted('confirm')).toBeUndefined()

    document.body.querySelector<HTMLButtonElement>('.confirm-modal-actions .ui-button--danger')?.click()
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('confirm')).toHaveLength(1)
    expect(document.body.querySelector('.kick-player-modal')).toBeNull()

    wrapper.unmount()
  })
})
