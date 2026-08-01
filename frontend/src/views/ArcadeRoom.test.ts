import { createPinia } from 'pinia'
import { shallowMount } from '@vue/test-utils'
import type { ArcadeGameKey, ArcadeSnapshot } from '../types/arcade'
import ArcadeRoom from './ArcadeRoom.vue'

function snapshot(gameKey: ArcadeGameKey): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'TEST',
    gameKey,
    gameName: '测试游戏',
    options: {},
    phase: 'lobby',
    hostId: 'p1',
    self: { id: 'p1', name: '玩家一', seat: 0 },
    players: [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
    ],
    requiredPlayers: gameKey === 'doudizhu' ? 3 : 2,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: { canStart: false, canRestart: false, canAct: false },
    game: {},
  }
}

describe('ArcadeRoom', () => {
  it('uses the wide desktop layout only for wide table games', async () => {
    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: snapshot('doudizhu') },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--wide')
    await wrapper.setProps({ snapshot: snapshot('gomoku') })
    expect(wrapper.get('.arcade-room').classes()).not.toContain('arcade-room--wide')
  })
})
