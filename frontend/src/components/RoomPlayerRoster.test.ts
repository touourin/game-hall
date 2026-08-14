import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import RoomPlayerRoster from './RoomPlayerRoster.vue'
import RoomPlayerSeat from './RoomPlayerSeat.vue'

function players(count: number) {
  return Array.from({ length: count }, (_, index) => ({
    id: `p${index + 1}`,
    name: `玩家 ${index + 1}`,
    seat: index,
    connected: index !== 1,
    disconnectForfeitAt: index === 1
      ? '2026-08-01T00:10:00+00:00'
      : null,
    disconnectForfeited: false,
    isHost: index === 0,
  }))
}

describe('RoomPlayerRoster', () => {
  it('balances seven players and an AI control across four columns', () => {
    const wrapper = mount(RoomPlayerRoster, {
      props: {
        players: players(7),
        selfId: 'p1',
        canAddAiPlayer: true,
        availableSeats: 3,
      },
    })

    expect(wrapper.attributes('data-player-columns')).toBe('4')
    expect(wrapper.attributes('style')).toContain(
      '--player-card-width: calc(25% - 7.5px)',
    )
    expect(wrapper.findAllComponents(RoomPlayerSeat)).toHaveLength(7)
  })

  it('keeps the shared disconnect state visible', () => {
    const wrapper = mount(RoomPlayerRoster, {
      props: {
        players: players(2),
        selfId: 'p1',
      },
    })

    expect(wrapper.text()).toContain('离线，10 分钟后弃权')
  })
})
