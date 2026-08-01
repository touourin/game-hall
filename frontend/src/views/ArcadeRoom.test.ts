import { createPinia } from 'pinia'
import { flushPromises, shallowMount } from '@vue/test-utils'
import type { ArcadeGameKey, ArcadeSnapshot } from '../types/arcade'
import * as clipboard from '../clipboard'
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

  it('copies the shared invitation link and confirms success', async () => {
    const copyText = vi.spyOn(clipboard, 'copyText').mockResolvedValue(true)
    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: snapshot('xiangqi') },
      global: { plugins: [createPinia()] },
    })

    await wrapper.get('.room-code-share button').trigger('click')
    await flushPromises()

    const invitation = new URL(String(copyText.mock.calls[0]?.[0]))
    expect(invitation.searchParams.get('game')).toBe('xiangqi')
    expect(invitation.searchParams.get('room')).toBe('TEST')
    expect(wrapper.get('.room-code-share button').text()).toContain('已复制')
    copyText.mockRestore()
  })

  it('shows the invitation URL when automatic copying is blocked', async () => {
    const copyText = vi.spyOn(clipboard, 'copyText').mockResolvedValue(false)
    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: snapshot('gomoku') },
      global: { plugins: [createPinia()] },
    })

    await wrapper.get('.room-code-share button').trigger('click')
    await flushPromises()

    expect(wrapper.get('.room-code-share button').text()).toContain('复制失败')
    expect(wrapper.get('.invite-copy-fallback input').attributes('value')).toContain(
      'game=gomoku',
    )
    copyText.mockRestore()
  })
})
