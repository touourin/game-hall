import { mount } from '@vue/test-utils'
import RoomInviteModal from './RoomInviteModal.vue'

describe('RoomInviteModal', () => {
  it('renders the room code and invitation URL and can be closed', async () => {
    const wrapper = mount(RoomInviteModal, {
      props: {
        roomCode: 'ABCD',
        url: 'http://192.168.1.20:10618/?game=gomoku&room=ABCD',
        title: '扫描加入五子棋房间',
      },
    })

    const dialog = document.body.querySelector<HTMLElement>('[role="dialog"]')!
    expect(dialog.textContent).toContain('扫描加入五子棋房间')
    expect(dialog.textContent).toContain('ABCD')
    expect(dialog.textContent).toContain('game=gomoku')

    document.body.querySelector<HTMLButtonElement>('[aria-label="关闭二维码"]')!.click()
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('close')).toHaveLength(1)
    wrapper.unmount()
  })
})
