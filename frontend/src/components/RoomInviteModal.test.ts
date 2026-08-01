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

    expect(wrapper.text()).toContain('扫描加入五子棋房间')
    expect(wrapper.text()).toContain('ABCD')
    expect(wrapper.text()).toContain('game=gomoku')

    await wrapper.get('[aria-label="关闭二维码"]').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })
})
