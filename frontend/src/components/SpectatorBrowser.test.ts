import { createPinia, setActivePinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ArcadeLobbyRoom } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import SpectatorBrowser from './SpectatorBrowser.vue'

const room: ArcadeLobbyRoom = {
  roomCode: 'VIEW',
  roomName: '公开牌桌',
  gameKey: 'poker',
  gameName: '德州扑克',
  hostName: '房主',
  playerCount: 2,
  maxPlayers: 8,
  phase: 'playing',
  watchable: true,
  spectatorCount: 1,
  options: { allowSpectators: true },
  players: [
    { id: 'p1', name: '房主', seat: 0, connected: true },
    { id: 'p2', name: '玩家二', seat: 1, connected: true },
  ],
}

describe('SpectatorBrowser', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('lets the viewer choose one player perspective', async () => {
    const arcade = useArcadeStore()
    const watchRoom = vi.spyOn(arcade, 'watchRoom').mockResolvedValue(true)
    const wrapper = mount(SpectatorBrowser, {
      props: {
        gameKey: 'poker',
        gameName: '德州扑克',
        rooms: [room],
      },
    })

    await wrapper.get('.spectator-room-list button').trigger('click')
    const targetButtons = wrapper.findAll('.spectator-targets button')
    expect(targetButtons).toHaveLength(2)
    await targetButtons[1]!.trigger('click')
    await flushPromises()

    expect(watchRoom).toHaveBeenCalledWith('poker', 'VIEW', 'p2')
    expect(wrapper.emitted('watched')).toEqual([[
      { gameKey: 'poker', roomCode: 'VIEW' },
    ]])
  })
})
