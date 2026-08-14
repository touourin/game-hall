import { createPinia } from 'pinia'
import { flushPromises, mount, shallowMount } from '@vue/test-utils'
import type {
  ArcadeGameKey,
  ArcadeSnapshot,
} from '../types/arcade'
import * as clipboard from '../clipboard'
import RoomPageHeader from '../components/RoomPageHeader.vue'
import RoomPlayerRoster from '../components/RoomPlayerRoster.vue'
import { useArcadeStore } from '../stores/arcade'
import type {
  AvalonArcadeSnapshot,
  RoomSnapshot as AvalonRoomSnapshot,
} from '../games/avalon/types'
import ArcadeRoom from './ArcadeRoom.vue'
import AvalonTable from '../games/avalon/AvalonTable.vue'
import ChessBoard from '../games/chess/ChessBoard.vue'
import { rememberAccessToken } from '../access'
import { rememberAccountToken } from '../account'
import {
  defaultRoleSkinLoadout,
  rememberRoleSkinLoadout,
  storedRoleSkinLoadout,
} from '../games/avalon/roleSkins'

function roleSkinProgressResponse(legacyAllUnlocked = true): Response {
  const roleProgress = {
    wins: legacyAllUnlocked ? 0 : 2,
    upgradeUnlocked: true,
    ultimateUnlocked: legacyAllUnlocked,
  }
  return new Response(JSON.stringify({
    ok: true,
    progress: {
      legacyAllUnlocked,
      eventAllUnlocked: false,
      eventEndsAt: null,
      rankedOnly: true,
      upgradeWinsRequired: 2,
      ultimateWinsRequired: 5,
      roles: Object.fromEntries(
        [
          'merlin',
          'percival',
          'loyal_servant',
          'assassin',
          'morgana',
          'mordred',
          'oberon',
          'minion',
        ].map((role) => [role, roleProgress]),
      ),
    },
  }), { status: 200, headers: { 'Content-Type': 'application/json' } })
}

async function settleLazyComponents(): Promise<void> {
  await vi.dynamicImportSettled()
  await flushPromises()
}

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
      canAddAiPlayer: gameKey === 'avalon',
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
      shadowMerlinEnabled: false,
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
    shadowMerlin: {
      enabled: false,
      transformed: false,
      councilTriggered: false,
      councilOpened: null,
      ballotsSubmitted: 0,
      myBallotSubmitted: false,
      eligibleExileTargetIds: [],
      assassinationDecisionsSubmitted: 0,
      myAssassinationDecisionSubmitted: false,
      assassinationChosen: null,
      assassinationTargetsSubmitted: 0,
      myAssassinationTargetSubmitted: false,
      eligibleAssassinationTargetIds: [],
      assassinationTargetId: null,
      exileTargetId: null,
      exileSuccess: null,
      openVotes: [],
      targetVotes: [],
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
      canSubmitExileCouncilBallot: false,
      canSubmitExileCouncilAssassinationDecision: false,
      canSubmitExileCouncilAssassinationTarget: false,
      canUseLady: false,
      canAcknowledgeLady: false,
      canAssassinate: false,
      canGrantDagger: false,
      canDissentingAssassinate: false,
      canEarlyAssassinate: false,
      canRestart: false,
    },
  }
  outer.gameName = '阿瓦隆'
  outer.options = {
    mode: inner.settings.mode,
    shadowMerlinEnabled: false,
    ladyEnabled: true,
    listed: true,
    earlyAssassinationEnabled: false,
  }
  outer.phase = phase === 'game_over' ? 'finished' : phase
  outer.minimumPlayers = 5
  outer.requiredPlayers = 10
  outer.actions.canStart = false
  outer.actions.canAddAiPlayer = phase === 'lobby'
  outer.actions.canDissolve = phase === 'lobby'
  outer.actions.canEditRules = phase === 'lobby'
  return { ...outer, gameKey: 'avalon', game: inner }
}

describe('ArcadeRoom', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  afterEach(async () => {
    await vi.dynamicImportSettled()
    vi.unstubAllGlobals()
    document.body.innerHTML = ''
  })

  it('shows the fixed perspective and everyone currently watching', () => {
    const next = snapshot('gomoku')
    next.phase = 'playing'
    next.players = [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '玩家二', seat: 1, connected: true, isHost: false },
    ]
    next.self = { id: 'p2', name: '玩家二', seat: 1 }
    next.viewer = {
      mode: 'spectator',
      id: 's1',
      accountId: 'spectator-account',
      name: '观众甲',
      targetPlayerId: 'p2',
    }
    next.spectators = [
      {
        id: 's1',
        name: '观众甲',
        targetPlayerId: 'p2',
        targetPlayerName: '玩家二',
      },
      {
        id: 's2',
        name: '观众乙',
        targetPlayerId: 'p1',
        targetPlayerName: '玩家一',
      },
    ]

    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: next },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.spectator-mode-banner').text()).toContain('玩家二')
    expect(wrapper.get('.arcade-spectator-strip').text()).toContain('观众甲（你）')
    expect(wrapper.get('.arcade-spectator-strip').text()).toContain('观众乙')
    expect(wrapper.get('.arcade-spectator-strip').text()).toContain('正在观看 玩家一')
    expect(wrapper.findComponent({ name: 'ArcadeChatPanel' }).props('readOnly')).toBe(true)
    expect(wrapper.findComponent({ name: 'RoomRecordActions' }).exists()).toBe(false)
  })

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

  it('renders international chess through the built-in game registry', async () => {
    const room = snapshot('chess')
    room.gameName = '国际象棋'
    room.phase = 'playing'
    room.players = [
      { id: 'p1', name: '白方', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '黑方', seat: 1, connected: true, isHost: false },
    ]
    room.actions.canAct = true
    room.game = {
      board: [
        ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
        Array(8).fill('bP'),
        ...Array.from({ length: 4 }, () => Array(8).fill(null)),
        Array(8).fill('wP'),
        ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR'],
      ],
      turnPlayerId: 'p1',
      colors: { p1: 'white', p2: 'black' },
      viewerColor: 'white',
      lastMove: null,
      moveHistory: [],
      capturedPieces: [],
      legalMoves: [],
      whiteInCheck: false,
      blackInCheck: false,
      checkedColor: null,
      halfmoveClock: 0,
      fullmoveNumber: 1,
    }

    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: room },
      global: { plugins: [createPinia()] },
    })
    await settleLazyComponents()

    expect(wrapper.findComponent(ChessBoard).exists()).toBe(true)
    expect(wrapper.findAll('.chess-cell')).toHaveLength(64)
    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--board-game')
    expect(wrapper.get('.arcade-room').attributes('data-game-skin')).toBe('classic-wood')
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
    await wrapper.setProps({ snapshot: snapshot('plugin-pyramid-solitaire') })
    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--immersive')
    expect(wrapper.get('.arcade-room').classes()).not.toContain('arcade-room--wide')
    await wrapper.setProps({ snapshot: snapshot('plugin-number-vault') })
    expect(wrapper.get('.arcade-room').classes()).not.toContain('arcade-room--immersive')
  })

  it('marks active board rooms for the mobile board-first layout', () => {
    const room = snapshot('xiangqi')
    room.phase = 'playing'
    room.actions.canRequestDraw = true
    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: room },
      global: {
        plugins: [createPinia()],
        stubs: { MatchRequestPanel: false },
      },
    })

    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--active')
    expect(wrapper.get('.arcade-room').classes()).toContain('arcade-room--board-game')
    expect(wrapper.get('.arcade-game-stage').element.lastElementChild?.classList).toContain(
      'match-request-panel',
    )
  })

  it('uses the shared solo room shell for a one-player plugin', () => {
    const room = snapshot('plugin-number-vault')
    room.gameName = '数字密匣'
    room.requiredPlayers = 1
    room.phase = 'playing'
    room.actions.canAct = true
    room.game = {
      minimum: 1,
      maximum: 20,
      maxAttempts: 6,
      remainingAttempts: 6,
      guesses: [],
      hint: 'ready',
      answer: null,
      won: false,
    }
    const wrapper = shallowMount(ArcadeRoom, {
      props: { snapshot: room },
      global: {
        plugins: [createPinia()],
        stubs: { RoomPlayerRoster: false },
      },
    })

    expect(wrapper.getComponent(RoomPageHeader).props('title')).toBe('数字密匣')
    expect(wrapper.find('.arcade-player-strip').exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'ArcadeChatPanel' }).exists()).toBe(false)
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
    await settleLazyComponents()

    expect(wrapper.findAll('main.arcade-room')).toHaveLength(1)
    expect(wrapper.find('.game-page').exists()).toBe(false)
    expect(wrapper.get('.arcade-player-strip').text()).toContain('AI玩家 1')
    expect(wrapper.get('.role-skin-loadout').text()).toContain('开局后锁定')
    expect(wrapper.findAll('[data-role-skin-role]')).toHaveLength(10)
    expect(wrapper.get('[data-role-skin-role="shadow_merlin"]').text()).toContain(
      '暗影梅林',
    )
    expect(wrapper.get('[data-role-skin-role="dissenting_courtier"]').text()).toContain(
      '心怀异念之臣',
    )
    expect(wrapper.findAll('.exit-room-trigger')).toHaveLength(1)
    expect(
      wrapper.find('.room-page-navigation .exit-room-trigger').exists(),
    ).toBe(true)
    expect(wrapper.find('.room-page-actions .exit-room-trigger').exists()).toBe(
      false,
    )

    await wrapper.get('.self-number-trigger').trigger('click')
    expect(wrapper.get('.player-number-list').text()).toContain('AI玩家 1')
    expect(wrapper.get('.room-ai-seat-control').text()).toContain('添加 AI 玩家')
    expect(wrapper.find('.room-rule-actions .room-ai-seat-control').exists()).toBe(false)
    await wrapper.get('.room-ai-add-button').trigger('click')
    expect(action).toHaveBeenCalledWith('add_ai', { difficulty: 'normal' })
  })

  it('adds a board-game AI with the selected difficulty', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const room = snapshot('xiangqi')
    room.actions.canAddAiPlayer = true
    room.ai = {
      defaultDifficulty: 'normal',
      difficulties: [
        { key: 'easy', label: '简单' },
        { key: 'normal', label: '普通' },
        { key: 'hard', label: '困难' },
      ],
    }
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: room },
      global: { plugins: [pinia] },
    })

    await wrapper.get('[aria-label="AI 难度"]').setValue('hard')
    expect(wrapper.get('.arcade-player-strip .room-ai-seat-control').text()).toContain(
      '添加 AI 玩家',
    )
    await wrapper.get('.room-ai-add-button').trigger('click')

    expect(action).toHaveBeenCalledWith('add_ai', { difficulty: 'hard' })
  })

  it('stores a separate selected style for each Avalon role', async () => {
    rememberAccessToken('access-token')
    rememberAccountToken('account-token')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(roleSkinProgressResponse()))
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: avalonSnapshot() },
      global: { plugins: [createPinia()] },
    })
    await settleLazyComponents()

    await wrapper.get('[data-role-skin-role="merlin"]').trigger('click')
    document.body.querySelector<HTMLButtonElement>(
      '[data-role-skin-choice="dark-chronicle"]',
    )?.click()
    await flushPromises()

    const saved = storedRoleSkinLoadout('account-1')
    expect(saved.merlin).toBe('dark-chronicle')
    expect(saved.percival).toBe('classic-tabletop')
    wrapper.unmount()
  })

  it('uses the independent dissenting-courtier selection in play', async () => {
    rememberAccessToken('access-token')
    rememberAccountToken('account-token')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(roleSkinProgressResponse()))
    const loadout = defaultRoleSkinLoadout()
    loadout.loyal_servant = 'classic-tabletop'
    loadout.dissenting_courtier = 'dark-chronicle'
    rememberRoleSkinLoadout('account-1', loadout)
    const room = avalonSnapshot('role_reveal')
    const role = room.game.self.role
    if (role) {
      role.code = 'dissenting_courtier'
      role.label = '心怀异念之臣'
    }
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: room },
      global: { plugins: [createPinia()] },
    })
    await settleLazyComponents()

    expect(wrapper.getComponent(AvalonTable).props('roleSkin')).toBe('dark-chronicle')
  })

  it('uses the independent shadow Merlin selection in play', async () => {
    rememberAccessToken('access-token')
    rememberAccountToken('account-token')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(roleSkinProgressResponse()))
    const loadout = defaultRoleSkinLoadout()
    loadout.merlin = 'classic-tabletop'
    loadout.shadow_merlin = 'grail-myth'
    rememberRoleSkinLoadout('account-1', loadout)
    const room = avalonSnapshot('role_reveal')
    const role = room.game.self.role
    if (role) {
      role.code = 'shadow_merlin'
      role.label = '暗影梅林'
    }
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: room },
      global: { plugins: [createPinia()] },
    })
    await settleLazyComponents()

    expect(wrapper.getComponent(AvalonTable).props('roleSkin')).toBe('grail-myth')
  })

  it('passes every seat in a seven-player Avalon lobby to the shared roster', () => {
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

    const roster = wrapper.getComponent(RoomPlayerRoster)
    expect(roster.props('players')).toHaveLength(7)
    expect(roster.props('canAddAiPlayer')).toBe(true)
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
    expect(wrapper.get('.rules-modal').text()).toContain('光明渐盛，暗流未息')
    expect(wrapper.get('.rules-modal').text()).toContain('心怀异念之臣')

    await wrapper.setProps({ snapshot: avalonSnapshot('role_reveal') })
    await settleLazyComponents()
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
      global: {
        plugins: [createPinia()],
        stubs: {
          RoomPlayerRoster: false,
          RoomPlayerSeat: false,
        },
      },
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

    expect(document.body.querySelector('.qr-modal')?.textContent).toContain('扫描加入测试游戏房间')
    expect(document.body.querySelector('.qr-modal')?.textContent).toContain('TEST')

    await wrapper.setProps({ snapshot: snapshot('hanoi') })
    expect(wrapper.find('[aria-label="显示加入二维码"]').exists()).toBe(false)
    expect(document.body.querySelector('.qr-modal')).toBeNull()
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
    expect(document.body.querySelector('.dissolve-room-modal')?.textContent).toContain(
      '所有等待中的玩家都会返回大厅',
    )
    expect(dissolveRoom).not.toHaveBeenCalled()

    document.body.querySelector<HTMLButtonElement>('.confirm-modal-actions .ui-button--danger')!.click()
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
    document.body.querySelector<HTMLButtonElement>('.confirm-modal-actions .ui-button--danger')?.click()
    await flushPromises()

    expect(kickPlayer).toHaveBeenCalledWith('p2')
    expect(document.body.querySelector('.kick-player-modal')).toBeNull()
    wrapper.unmount()
  })

  it('asks for confirmation before leaving the room', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const leaveRoom = vi.spyOn(arcade, 'leaveRoom').mockResolvedValue(true)
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: snapshot('gomoku') },
      global: { plugins: [pinia] },
    })

    await wrapper.get('.exit-room-trigger').trigger('click')
    expect(document.body.querySelector('.exit-room-modal')?.textContent).toContain(
      '离开房间并让出座位',
    )
    expect(leaveRoom).not.toHaveBeenCalled()

    document.body.querySelector<HTMLButtonElement>('.exit-room-modal .ui-button--danger')!.click()
    await wrapper.vm.$nextTick()

    expect(leaveRoom).toHaveBeenCalledOnce()
  })

  it('separates temporary return from resigning an active multiplayer game', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const detachRoom = vi.spyOn(arcade, 'detachRoom').mockResolvedValue(true)
    const abandonRoom = vi.spyOn(arcade, 'abandonRoom').mockResolvedValue(true)
    const playingRoom = snapshot('gomoku')
    playingRoom.phase = 'playing'
    playingRoom.actions.canAct = true
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: playingRoom },
      global: { plugins: [pinia], stubs: { GomokuBoard: true } },
    })

    await wrapper.get('.exit-room-trigger').trigger('click')
    expect(document.body.querySelector('.exit-room-modal')?.textContent).toContain('暂时返回')
    expect(document.body.querySelector('.exit-room-modal')?.textContent).toContain('认输并退出')
    document.body.querySelector<HTMLButtonElement>('.exit-room-modal .ui-button--secondary')!.click()
    await wrapper.vm.$nextTick()
    expect(detachRoom).toHaveBeenCalledOnce()

    await wrapper.get('.exit-room-trigger').trigger('click')
    document.body.querySelector<HTMLButtonElement>('.exit-room-modal .ui-button--danger')!.click()
    await wrapper.vm.$nextTick()
    expect(abandonRoom).toHaveBeenCalledOnce()
  })

  it('warns that leaving an active solo challenge discards progress', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const abandonRoom = vi.spyOn(arcade, 'abandonRoom').mockResolvedValue(true)
    const playingRoom = snapshot('reaction')
    playingRoom.phase = 'playing'
    playingRoom.actions.canAct = true
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: playingRoom },
      global: { plugins: [pinia], stubs: { ReactionTest: true } },
    })

    await wrapper.get('.exit-room-trigger').trigger('click')
    expect(document.body.querySelector('.exit-room-modal')?.textContent).toContain('放弃当前进度')
    document.body.querySelector<HTMLButtonElement>('.exit-room-modal .ui-button--danger')!.click()
    await wrapper.vm.$nextTick()
    expect(abandonRoom).toHaveBeenCalledOnce()
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
      global: {
        plugins: [pinia],
        stubs: { MatchRequestPanel: false },
      },
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
    await wrapper.get('.rule-editor-modal > .ui-button--primary').trigger('click')
    await flushPromises()

    expect(updateRules).toHaveBeenCalledWith(
      expect.objectContaining({ winRule: 'exact_five' }),
    )
    expect(wrapper.find('.rule-editor-modal').exists()).toBe(false)
  })

  it('opens the one night werewolf flow and role guide from one place', async () => {
    const room = snapshot('one_night_werewolf')
    room.gameName = '一夜狼人'
    room.options = { rolePreset: 'standard', listed: true, allowSpectators: false }
    room.game = {
      roleDeck: [],
      roleGuide: [
        { code: 'werewolf', label: '狼人', alignment: 'werewolf', description: '查看其他狼人。' },
        { code: 'seer', label: '预言家', alignment: 'village', description: '查看玩家牌或中央牌。' },
        { code: 'tanner', label: '皮匠', alignment: 'tanner', description: '希望自己被处决。' },
      ],
      self: { initialRole: null, nightResults: [] },
      night: { isMyTurn: false, prompt: null },
      votesSubmitted: 0,
      hasVoted: false,
      resolution: null,
      legal: {},
    }
    const wrapper = mount(ArcadeRoom, {
      props: { snapshot: room },
      global: { plugins: [createPinia()] },
    })
    await settleLazyComponents()

    const guideButton = wrapper
      .findAll('.room-rule-actions button')
      .find(button => button.text().includes('规则与角色'))
    await guideButton?.trigger('click')

    const guide = wrapper.get('.one-night-rules-modal')
    expect(guide.text()).toContain('玩法流程、角色技能、行动限制与胜负条件')
    expect(guide.text()).toContain('狼人')
    expect(guide.text()).toContain('预言家')
    expect(guide.text()).toContain('皮匠')
  })
})
