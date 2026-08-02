import { createPinia } from 'pinia'
import { flushPromises, mount, shallowMount } from '@vue/test-utils'
import type {
  ArcadeGameKey,
  ArcadeSnapshot,
  AvalonArcadeSnapshot,
} from '../types/arcade'
import * as clipboard from '../clipboard'
import RoomPageHeader from '../components/RoomPageHeader.vue'
import { useArcadeStore } from '../stores/arcade'
import type { RoomSnapshot as AvalonRoomSnapshot } from '../types/avalon'
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
    self: { id: 'p1', accountId: 'account-1', name: '玩家一', seat: 0 },
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

function avalonSnapshot(
  phase: AvalonRoomSnapshot['phase'] = 'lobby',
): AvalonArcadeSnapshot {
  const outer = snapshot('avalon')
  const started = phase !== 'lobby'
  const inner: AvalonRoomSnapshot = {
    roomCode: 'TEST',
    revision: 1,
    phase,
    self: {
      id: 'p1',
      name: '玩家一',
      isHost: true,
      role: started
        ? {
            code: 'merlin',
            label: '梅林',
            alignment: 'good',
            description: '隐藏自己的身份。',
            knowledge: [],
          }
        : null,
    },
    players: [
      {
        id: 'p1',
        name: '玩家一',
        seat: 0,
        connected: true,
        isBot: false,
        isHost: true,
        isLeader: started,
        isSelected: false,
      },
    ],
    settings: {
      mode: 'standard',
      ladyEnabled: true,
      ladyRecommended: false,
      listed: true,
      earlyAssassinationEnabled: false,
      rolePreset: [],
    },
    game: {
      missionNumber: 1,
      requiredTeamSize: 2,
      failThreshold: 1,
      leaderId: started ? 'p1' : null,
      proposalAttempt: 1,
      selectedTeamIds: [],
      teamVotesSubmitted: 0,
      myTeamVoteSubmitted: false,
      lastTeamVotes: [],
      missionVotesSubmitted: 0,
      myMissionVoteSubmitted: false,
      roleConfirmedCount: 0,
      missionHistory: [],
      proposalHistory: [],
      successCount: 0,
      failCount: 0,
    },
    lady: {
      enabled: true,
      holderId: null,
      usedByIds: [],
      eligibleTargetIds: [],
      pendingInspectorId: null,
      pendingTargetId: null,
      history: [],
      myChecks: [],
      currentResult: null,
    },
    result: {
      winner: null,
      reason: null,
      endingRoute: null,
      assassinTargetId: null,
      assassinationWasEarly: false,
      eligibleTargetIds: [],
    },
    courtUndercurrent: {
      enabled: false,
      daggerCandidateIds: [],
      daggerTargetId: null,
      daggerHit: null,
      transformedPlayerId: null,
      eligibleTargetIds: [],
      assassinationTargetId: null,
    },
    chat: { maxLength: 300, messages: [] },
    actions: {
      canStart: false,
      canUpdateSettings: phase === 'lobby',
      canDissolve: phase === 'lobby',
      canLeave: true,
      canConfirmRole: phase === 'role_reveal',
      canProposeTeam: false,
      canVoteTeam: false,
      canVoteMission: false,
      canMissionFail: false,
      canContinueRound: false,
      canUseLady: false,
      canAcknowledgeLady: false,
      canAssassinate: false,
      canGrantDagger: false,
      canDissentingAssassinate: false,
      canEarlyAssassinate: false,
      canAddAiPlayer: phase === 'lobby',
      canRestart: false,
    },
  }
  outer.gameName = '阿瓦隆'
  outer.options = {
    mode: inner.settings.mode,
    ladyEnabled: true,
    listed: true,
    earlyAssassinationEnabled: false,
  }
  outer.phase = phase === 'game_over' ? 'finished' : phase
  outer.minimumPlayers = 5
  outer.requiredPlayers = 10
  outer.actions.canStart = false
  outer.actions.canDissolve = phase === 'lobby'
  outer.actions.canEditRules = phase === 'lobby'
  return { ...outer, gameKey: 'avalon', game: inner }
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
    await wrapper.setProps({ snapshot: avalonSnapshot() })
    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--wide')
    await wrapper.setProps({ snapshot: snapshot('gomoku') })
    expect(wrapper.get('.arcade-room').classes()).not.toContain('arcade-room--wide')
    await wrapper.setProps({ snapshot: snapshot('minesweeper') })
    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--wide')
  })

  it('runs the Avalon lobby inside the same shared room shell', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const room = avalonSnapshot()
    room.players.push({
      id: 'bot-1',
      name: 'AI玩家 1',
      seat: 1,
      connected: true,
      isBot: true,
      isHost: false,
    })
    const avalon = room.game
    avalon.players.push({
      id: 'bot-1',
      name: 'AI玩家 1',
      seat: 1,
      connected: true,
      isBot: true,
      isHost: false,
      isLeader: false,
      isSelected: false,
    })
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: room },
      global: { plugins: [pinia] },
    })

    expect(wrapper.findAll('main.arcade-room')).toHaveLength(1)
    expect(wrapper.find('.game-page').exists()).toBe(false)
    expect(wrapper.get('.arcade-player-strip').text()).toContain('AI玩家 1')
    expect(wrapper.get('.artwork-skin-card').text()).toContain('开局后锁定')
    expect(wrapper.findAll('.exit-room-trigger')).toHaveLength(1)

    await wrapper.get('.self-number-trigger').trigger('click')
    expect(wrapper.get('.player-number-list').text()).toContain('AI玩家 1')
    await wrapper.get('.room-rule-actions button').trigger('click')
    expect(action).toHaveBeenCalledWith('add_ai')
  })

  it('balances a seven-player Avalon lobby instead of leaving one orphan card', () => {
    const room = avalonSnapshot()
    room.players = Array.from({ length: 7 }, (_, index) => ({
      id: `p${index + 1}`,
      name: index === 0 ? '玩家一' : `AI玩家 ${index}`,
      seat: index,
      connected: true,
      isBot: index > 0,
      isHost: index === 0,
    }))
    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: room },
      global: { plugins: [createPinia()] },
    })

    const playerStrip = wrapper.get('.arcade-player-strip')
    const playerCards = playerStrip.findAll('article')
    expect(playerStrip.attributes('data-player-columns')).toBe('4')
    expect(playerStrip.attributes('style')).toContain(
      '--player-card-width: calc(25% - 7.5px)',
    )
    expect(playerCards).toHaveLength(7)
  })

  it('keeps Avalon rules, identity, table and chat in the shared room page', async () => {
    const lobby = avalonSnapshot()
    const lobbyGame = lobby.game
    lobbyGame.settings.mode = 'court_undercurrent'
    lobbyGame.settings.ladyEnabled = false
    lobby.options.mode = 'court_undercurrent'
    lobby.options.ladyEnabled = false
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: lobby },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('[aria-label="查看我的战绩"]').text()).toContain('我的战绩')
    expect(wrapper.get('[aria-label="查看排行榜"]').text()).toContain('排行榜')
    await wrapper.get('[aria-label="打开设置"]').trigger('click')
    expect(wrapper.emitted('settings')).toHaveLength(1)

    await wrapper.get('[aria-label="查看玩法说明"]').trigger('click')
    expect(wrapper.get('.rules-modal').text()).toContain('胜势已成，暗流未息')
    expect(wrapper.get('.rules-modal').text()).toContain('心怀异念之臣')

    await wrapper.setProps({ snapshot: avalonSnapshot('role_reveal') })
    expect(wrapper.find('[aria-label="查看我的战绩"]').exists()).toBe(true)
    expect(wrapper.find('[aria-label="查看排行榜"]').exists()).toBe(true)
    expect(wrapper.find('[aria-label="打开设置"]').exists()).toBe(true)
    expect(wrapper.get('.avalon-table').text()).toContain('只让自己看到')
    expect(wrapper.get('.arcade-player-strip').text()).toContain('玩家一')
    await wrapper.get('[aria-label="查看我的身份"]').trigger('click')
    await wrapper.get('.identity-modal .press-reveal-card').trigger('pointerdown')
    expect(wrapper.get('.identity-modal').text()).toContain('梅林')
    await wrapper.get('.arcade-chat-dock').trigger('click')
    expect(wrapper.get('.arcade-chat-panel').attributes('aria-label')).toBe('房间聊天')
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
      '/games/xiangqi/rooms/TEST',
    )
    await wrapper.get('.invite-link-actions button').trigger('click')
    await flushPromises()

    const invitation = new URL(String(copyText.mock.calls[0]?.[0]))
    expect(invitation.pathname).toBe('/games/xiangqi/rooms/TEST')
    expect(invitation.search).toBe('')
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
      '/games/gomoku/rooms/TEST',
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
    expect(document.body.querySelector('.kick-player-modal')?.textContent).toContain('移除玩家二？')
    document.body.querySelector<HTMLButtonElement>('.kick-player-actions .danger')?.click()
    await flushPromises()

    expect(kickPlayer).toHaveBeenCalledWith('p2')
    expect(document.body.querySelector('.kick-player-modal')).toBeNull()
    wrapper.unmount()
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
    await wrapper.get('.room-rule-actions > button').trigger('click')
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
