import { createPinia } from 'pinia'
import { flushPromises, mount, shallowMount } from '@vue/test-utils'
import type { ArcadeGameKey, ArcadeSnapshot } from '../types/arcade'
import * as clipboard from '../clipboard'
import { useArcadeStore } from '../stores/arcade'
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
    roundNumber: 0,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: {
      canStart: false,
      canRestart: false,
      canAct: false,
      canKickPlayers: true,
      canDissolve: true,
      canEditRules: true,
      canRequestUndo: false,
      canRequestDraw: false,
      canResolveRequest: false,
    },
    rematchReadyPlayerIds: [],
    request: null,
    chat: { maxLength: 300, messages: [] },
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
    await wrapper.setProps({ snapshot: snapshot('minesweeper') })
    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--wide')
  })

  it('copies the shared invitation link and confirms success', async () => {
    const copyText = vi.spyOn(clipboard, 'copyText').mockResolvedValue(true)
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: snapshot('xiangqi') },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.invite-link-field input').attributes('value')).toContain(
      'game=xiangqi',
    )
    await wrapper.get('.invite-link-actions button').trigger('click')
    await flushPromises()

    const invitation = new URL(String(copyText.mock.calls[0]?.[0]))
    expect(invitation.searchParams.get('game')).toBe('xiangqi')
    expect(invitation.searchParams.get('room')).toBe('TEST')
    expect(wrapper.get('.invite-link-actions button').text()).toContain('已复制')
    copyText.mockRestore()
  })

  it('shows the invitation URL when automatic copying is blocked', async () => {
    const copyText = vi.spyOn(clipboard, 'copyText').mockResolvedValue(false)
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: snapshot('gomoku') },
      global: { plugins: [createPinia()] },
    })

    await wrapper.get('.invite-link-actions button').trigger('click')
    await flushPromises()

    expect(wrapper.get('.invite-link-actions button').text()).toContain('复制失败')
    expect(wrapper.get('.invite-link-field input').attributes('value')).toContain(
      'game=gomoku',
    )
    expect(wrapper.text()).toContain('自动复制失败')
    copyText.mockRestore()
  })

  it('lets the host confirm removing a waiting player', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const kickPlayer = vi.spyOn(arcade, 'kickPlayer').mockResolvedValue(true)
    const waitingRoom = snapshot('gomoku')
    waitingRoom.players.push({
      id: 'p2',
      name: '玩家二',
      seat: 1,
      connected: true,
      isHost: false,
    })
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: waitingRoom },
      global: { plugins: [pinia] },
    })

    await wrapper.get('[aria-label="移除玩家二"]').trigger('click')
    expect(wrapper.text()).toContain('移除玩家二？')
    await wrapper.get('.arcade-confirm-actions .danger').trigger('click')
    await flushPromises()

    expect(kickPlayer).toHaveBeenCalledWith('p2')
    expect(wrapper.find('.arcade-confirm-card').exists()).toBe(false)
  })

  it('asks for confirmation before leaving the room', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const leaveRoom = vi.spyOn(arcade, 'leaveRoom').mockResolvedValue()
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: snapshot('gomoku') },
      global: { plugins: [pinia] },
    })

    await wrapper.get('.exit-room-trigger').trigger('click')
    expect(wrapper.get('.exit-room-modal').text()).toContain(
      '离开房间并让出座位',
    )
    expect(leaveRoom).not.toHaveBeenCalled()

    await wrapper.get('.exit-room-modal .danger-button').trigger('click')

    expect(leaveRoom).toHaveBeenCalledOnce()
  })

  it('shows the opponent response controls for a draw request', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const resolve = vi
      .spyOn(arcade, 'resolveGameRequest')
      .mockResolvedValue(true)
    const playingRoom = snapshot('gomoku')
    playingRoom.phase = 'playing'
    playingRoom.actions.canKickPlayers = false
    playingRoom.actions.canDissolve = false
    playingRoom.actions.canEditRules = false
    playingRoom.actions.canAct = true
    playingRoom.request = {
      kind: 'draw',
      requesterId: 'p2',
      requesterName: '玩家二',
      isMine: false,
    }
    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: playingRoom },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('玩家二申请和棋')
    const buttons = wrapper.findAll('.request-response-actions button')
    await buttons[1]?.trigger('click')
    expect(resolve).toHaveBeenCalledWith(true)
  })

  it('lets the host edit and save rules before the game', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const updateRules = vi.spyOn(arcade, 'updateRules').mockResolvedValue(true)
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: snapshot('gomoku') },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.room-rule-bar').text()).toContain('15 路棋盘')
    await wrapper.get('.room-rule-bar > button').trigger('click')
    const exactFive = wrapper
      .findAll('.rule-editor-modal .game-rule-settings button')
      .find((button) => button.text().includes('正好五子'))
    await exactFive?.trigger('click')
    await wrapper.get('.rule-editor-modal > .primary-button').trigger('click')
    await flushPromises()

    expect(updateRules).toHaveBeenCalledWith(
      expect.objectContaining({ winRule: 'exact_five' }),
    )
    expect(wrapper.find('.rule-editor-modal').exists()).toBe(false)
  })
})
