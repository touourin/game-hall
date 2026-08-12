import { mount } from '@vue/test-utils'
import LobbyRoomPanel from './LobbyRoomPanel.vue'

describe('LobbyRoomPanel', () => {
  it('renders real room data and emits the selected room', async () => {
    const room = {
      roomCode: 'NX42',
      roomName: '冠军桌',
      gameKey: 'avalon' as const,
      gameName: '阿瓦隆',
      hostName: '测试房主',
      playerCount: 6,
      maxPlayers: 10,
      options: {},
      phase: 'lobby' as const,
    }
    const wrapper = mount(LobbyRoomPanel, {
      props: { rooms: [room], connected: true },
    })

    expect(wrapper.text()).toContain('冠军桌')
    expect(wrapper.text()).toContain('6/10')
    expect(wrapper.text()).toContain('在线')

    await wrapper.get('.lobby-room-row').trigger('click')
    expect(wrapper.emitted('open')?.[0]?.[0]).toEqual(room)
  })

  it('shows an honest empty state while reconnecting', () => {
    const wrapper = mount(LobbyRoomPanel, {
      props: { rooms: [], connected: false },
    })

    expect(wrapper.text()).toContain('当前没有公开房间')
    expect(wrapper.text()).toContain('重连中')
  })
})
