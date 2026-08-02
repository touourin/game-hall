import { createPinia } from 'pinia'
import { flushPromises, mount, shallowMount } from '@vue/test-utils'
import type { ArcadeGameKey, ArcadeSnapshot } from '../types/arcade'
import * as clipboard from '../clipboard'
import RoomPageHeader from '../components/RoomPageHeader.vue'
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
  beforeEach(() => localStorage.clear())

  it('offers five local skins for supported multiplayer games', async () => {
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: snapshot('gomoku') },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.game-skin-card').text()).toContain('我的棋盘画风')
    expect(wrapper.findAll('[data-game-skin-option]')).toHaveLength(5)
    expect(wrapper.get('.arcade-room').attributes('data-game-skin')).toBe('classic-wood')

    await wrapper.get('[data-game-skin-option="celestial-gold"]').trigger('click')

    expect(wrapper.get('.arcade-room').attributes('data-game-skin')).toBe('celestial-gold')
    expect(localStorage.getItem('game-hall:game-skin')).toBe('celestial-gold')

    await wrapper.setProps({ snapshot: snapshot('poker') })
    expect(wrapper.get('.game-skin-card').text()).toContain('我的扑克画风')

    await wrapper.setProps({ snapshot: snapshot('hanoi') })
    expect(wrapper.find('.game-skin-card').exists()).toBe(false)
    expect(wrapper.get('.arcade-room').attributes('data-game-skin')).toBeUndefined()
  })

  it('uses the wide desktop layout only for wide table games', async () => {
    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: snapshot('doudizhu') },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.getComponent(RoomPageHeader).props('title')).toBe('房间 TEST')
    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--wide')
    await wrapper.setProps({ snapshot: snapshot('gomoku') })
    expect(wrapper.get('.arcade-room').classes()).not.toContain('arcade-room--wide')
    await wrapper.setProps({ snapshot: snapshot('minesweeper') })
    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--wide')
  })

  it('shows the shared ten-minute disconnect rule and pending forfeit', () => {
    const playingRoom = snapshot('gomoku')
    playingRoom.phase = 'playing'
    playingRoom.players.push({
      id: 'p2',
      name: '玩家二',
      seat: 1,
      connected: false,
      disconnectForfeitAt: '2026-08-01T00:10:00+00:00',
      disconnectForfeited: false,
      isHost: false,
    })
    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: playingRoom },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('掉线保护 10 分钟')
    expect(wrapper.text()).toContain('离线，10 分钟后弃权')
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

  it('shows the shared QR invitation in multiplayer lobbies only', async () => {
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: snapshot('gomoku') },
      global: { plugins: [createPinia()] },
    })

    const qrButtons = wrapper.findAll('[aria-label="显示加入二维码"]')
    expect(qrButtons).toHaveLength(2)
    await qrButtons[0]?.trigger('click')

    expect(wrapper.get('.qr-modal').text()).toContain('扫描加入测试游戏房间')
    expect(wrapper.get('.qr-modal').text()).toContain('TEST')

    await wrapper.setProps({ snapshot: snapshot('hanoi') })
    expect(wrapper.find('[aria-label="显示加入二维码"]').exists()).toBe(false)
    expect(wrapper.find('.qr-modal').exists()).toBe(false)
  })

  it('uses the shared confirmation before dissolving a multiplayer room', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const dissolveRoom = vi.spyOn(arcade, 'dissolveRoom').mockResolvedValue(true)
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: snapshot('gomoku') },
      global: { plugins: [pinia] },
    })

    await wrapper.get('.dissolve-room-trigger').trigger('click')
    expect(wrapper.get('.dissolve-room-modal').text()).toContain(
      '所有等待中的玩家都会返回大厅',
    )
    expect(dissolveRoom).not.toHaveBeenCalled()

    await wrapper.get('.dissolve-room-actions .danger').trigger('click')
    await flushPromises()

    expect(dissolveRoom).toHaveBeenCalledOnce()
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
    await wrapper.get('.kick-player-actions .danger').trigger('click')
    await flushPromises()

    expect(kickPlayer).toHaveBeenCalledWith('p2')
    expect(wrapper.find('.kick-player-modal').exists()).toBe(false)
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
