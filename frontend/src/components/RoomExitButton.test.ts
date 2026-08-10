import { mount } from '@vue/test-utils'
import RoomExitButton from './RoomExitButton.vue'

describe('RoomExitButton', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('supports a game-specific multiplayer elimination label', async () => {
    const wrapper = mount(RoomExitButton, {
      props: {
        mode: 'multiplayer-active',
        abandonLabel: '退出并淘汰',
      },
    })

    await wrapper.get('.exit-room-trigger').trigger('click')
    const dangerButton = document.body.querySelector<HTMLButtonElement>('.danger-button')!
    expect(dangerButton.textContent).toContain('退出并淘汰')
    dangerButton.click()
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('abandon')).toHaveLength(1)
    wrapper.unmount()
  })
})
