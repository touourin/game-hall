import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import CleanupRoomButton from '../components/CleanupRoomButton.vue'
import { useRoomStore } from '../games/avalon/store'
import AvalonHomeView from './AvalonHomeView.vue'

describe('Avalon home view', () => {
  it('shows cleanup-ready rooms and lets any logged-in user clean them', async () => {
    const pinia = createPinia()
    const room = useRoomStore(pinia)
    room.availableRooms = [
      {
        roomCode: 'OLD1',
        hostName: '旧房主',
        playerCount: 5,
        maxPlayers: 10,
        ladyEnabled: true,
        phase: 'team_building',
        cleanupAvailable: true,
        allHumansOffline: true,
      },
    ]
    const cleanupRoom = vi.spyOn(room, 'cleanupRoom').mockResolvedValue(true)
    const wrapper = mount(AvalonHomeView, {
      props: {
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          nextRenameAt: null,
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.game-home-header').text()).toContain('阿瓦隆')
    expect(wrapper.find('.account-bar').exists()).toBe(false)
    expect(wrapper.text()).toContain('待清理的圆桌')
    expect(wrapper.text()).toContain('未完成对局')
    wrapper.findComponent(CleanupRoomButton).vm.$emit('confirm')
    await wrapper.vm.$nextTick()

    expect(cleanupRoom).toHaveBeenCalledWith('OLD1')
  })
})
