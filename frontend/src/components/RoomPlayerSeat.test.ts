import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import RoomPlayerSeat from './RoomPlayerSeat.vue'

describe('RoomPlayerSeat', () => {
  it('renders the shared host and self states', () => {
    const wrapper = mount(RoomPlayerSeat, {
      props: {
        name: '玩家一',
        seat: 0,
        host: true,
        self: true,
      },
    })

    expect(wrapper.text()).toContain('玩家一')
    expect(wrapper.text()).toContain('房主')
    expect(wrapper.text()).toContain('在线')
    expect(wrapper.classes()).toContain('room-player-seat--self')
  })

  it('reacts when a connected player enters disconnect protection', async () => {
    const wrapper = mount(RoomPlayerSeat, {
      props: {
        name: '玩家二',
        seat: 1,
        connected: true,
      },
    })

    await wrapper.setProps({
      connected: false,
      disconnectForfeitAt: '2026-08-01T00:10:00+00:00',
    })

    expect(wrapper.text()).toContain('离线，10 分钟后弃权')
    expect(wrapper.classes()).toContain('room-player-seat--offline')
  })
})
