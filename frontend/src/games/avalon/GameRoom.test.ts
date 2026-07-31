import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { vi } from 'vitest'
import { useRoomStore } from './store'
import type { RoomSnapshot } from './types'
import GameRoom from './GameRoom.vue'

function roleRevealSnapshot(revision: number): RoomSnapshot {
  return {
    roomCode: 'TEST',
    revision,
    phase: 'role_reveal',
    self: {
      id: 'p1',
      name: '测试玩家',
      isHost: true,
      role: {
        code: 'merlin',
        label: '梅林',
        alignment: 'good',
        description: '隐藏自己的身份。',
        knowledge: [],
      },
    },
    players: [
      {
        id: 'p1',
        name: '测试玩家',
        seat: 0,
        connected: true,
        isBot: false,
        isHost: true,
        isLeader: true,
        isSelected: false,
      },
    ],
    settings: {
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
      leaderId: 'p1',
      proposalAttempt: 1,
      selectedTeamIds: [],
      teamVotesSubmitted: 0,
      myTeamVoteSubmitted: false,
      lastTeamVotes: [],
      missionVotesSubmitted: 0,
      myMissionVoteSubmitted: false,
      roleConfirmedCount: revision,
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
      assassinTargetId: null,
      assassinationWasEarly: false,
    },
    chat: {
      maxLength: 300,
      messages: [],
    },
    actions: {
      canStart: false,
      canUpdateSettings: false,
      canLeave: false,
      canConfirmRole: true,
      canProposeTeam: false,
      canVoteTeam: false,
      canVoteMission: false,
      canMissionFail: false,
      canContinueRound: false,
      canUseLady: false,
      canAcknowledgeLady: false,
      canAssassinate: false,
      canEarlyAssassinate: false,
      canAddAiPlayer: false,
      canRestart: false,
    },
  }
}

describe('GameRoom role reveal', () => {
  it('keeps the player own number visible and opens the full number list', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.players.push({
      id: 'p2',
      name: '第二位玩家',
      seat: 1,
      connected: true,
      isBot: false,
      isHost: false,
      isLeader: false,
      isSelected: false,
    })
    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.self-number-trigger').text()).toContain('我的号码')
    expect(wrapper.get('.self-number-trigger').text()).toContain('1号')
    expect(wrapper.get('.self-number-trigger').text()).toContain('查看号码表')
    await wrapper.get('.self-number-trigger').trigger('click')

    const numberList = wrapper.get('.player-number-list').text()
    expect(numberList).toContain('测试玩家')
    expect(numberList).toContain('第二位玩家')
    expect(numberList).toContain('你')
  })

  it('shows every player number and name on the identity confirmation page', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.players.push({
      id: 'p2',
      name: '第二位玩家',
      seat: 1,
      connected: true,
      isBot: false,
      isHost: false,
      isLeader: false,
      isSelected: false,
    })

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    const roster = wrapper.get('.player-number-roster').text()
    expect(roster).toContain('1号')
    expect(roster).toContain('测试玩家')
    expect(roster).toContain('2号')
    expect(roster).toContain('第二位玩家')
  })

  it('announces the first leader before team building starts', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.players.push({
      id: 'p2',
      name: '首任队长',
      seat: 1,
      connected: true,
      isBot: false,
      isHost: false,
      isLeader: true,
      isSelected: false,
    })
    snapshot.players[0]!.isLeader = false
    snapshot.game.leaderId = 'p2'

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    const leaderCard = wrapper.get('.first-leader-card')
    expect(leaderCard.text()).toContain('本局首任队长')
    expect(leaderCard.text()).toContain('2号 首任队长')
    expect(leaderCard.text()).toContain('首先组建任务队伍')

    const leaderRosterItem = wrapper.get('.player-number-roster .leader')
    expect(leaderRosterItem.text()).toContain('2号')
    expect(leaderRosterItem.text()).toContain('队长')
  })

  it('announces the initial Lady holder before the first mission', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.players.push({
      id: 'p2',
      name: '仙女持有者',
      seat: 1,
      connected: true,
      isBot: false,
      isHost: false,
      isLeader: false,
      isSelected: false,
    })
    snapshot.lady.holderId = 'p2'

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.initial-lady-card').text()).toContain(
      '2号 仙女持有者',
    )
    expect(wrapper.get('.player-number-roster').text()).toContain('仙女')
  })

  it('shows numbered AI players and lets the host add another one', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'lobby'
    snapshot.self.role = null
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canAddAiPlayer = true
    snapshot.players.push({
      id: 'bot-1',
      name: 'AI玩家 1',
      seat: 1,
      connected: true,
      isBot: true,
      isHost: false,
      isLeader: false,
      isSelected: false,
    })
    const pinia = createPinia()
    const room = useRoomStore(pinia)
    const perform = vi.spyOn(room, 'perform').mockResolvedValue({ ok: true })
    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.player-list').text()).toContain('2 号玩家')
    expect(wrapper.get('.ai-player-badge').text()).toBe('AI')
    await wrapper.get('.add-ai-button').trigger('click')

    expect(perform).toHaveBeenCalledWith('room:add-ai-player')
  })

  it('keeps confirmation enabled when another player updates the room', async () => {
    const wrapper = mount(GameRoom, {
      props: { snapshot: roleRevealSnapshot(1) },
      global: { plugins: [createPinia()] },
    })

    const confirmButton = wrapper.get('.primary-button')
    expect(confirmButton.attributes('disabled')).toBeDefined()

    await wrapper.get('.secret-card').trigger('pointerdown')
    expect(confirmButton.attributes('disabled')).toBeUndefined()

    await wrapper.setProps({ snapshot: roleRevealSnapshot(2) })
    expect(confirmButton.attributes('disabled')).toBeUndefined()
  })

  it('opens a replay with the recorded public team votes', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'team_building'
    snapshot.actions.canConfirmRole = false
    snapshot.game.proposalHistory = [
      {
        missionNumber: 1,
        attempt: 1,
        leaderId: 'p1',
        teamIds: ['p1'],
        votes: [{ playerId: 'p1', approve: true }],
        accepted: true,
      },
    ]

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    await wrapper.findAll('.mission-node')[0].trigger('click')

    expect(wrapper.get('.replay-modal').text()).toContain('第 1 轮复盘')
    expect(wrapper.get('.replay-modal').text()).toContain(
      '1号 测试玩家 赞成',
    )
    expect(wrapper.get('.replay-leader').text()).toContain(
      '队长 1号 测试玩家',
    )
    expect(wrapper.get('.replay-team .leader').text()).toContain('队长')
    expect(wrapper.get('.replay-modal').text()).toContain('通过')
    expect(wrapper.find('.game-toolbar').exists()).toBe(false)
  })

  it('opens a mission-specific replay from the mission track', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'team_building'
    snapshot.actions.canConfirmRole = false
    snapshot.game.missionNumber = 2
    snapshot.game.proposalHistory = [
      {
        missionNumber: 1,
        attempt: 1,
        leaderId: 'p1',
        teamIds: ['p1'],
        votes: [{ playerId: 'p1', approve: false }],
        accepted: false,
      },
      {
        missionNumber: 2,
        attempt: 1,
        leaderId: 'p1',
        teamIds: ['p1'],
        votes: [{ playerId: 'p1', approve: true }],
        accepted: true,
      },
    ]

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    await wrapper.findAll('.mission-node')[0].trigger('click')

    const replay = wrapper.get('.replay-modal')
    expect(replay.get('h2').text()).toContain('第 1 轮复盘')
    expect(replay.text()).toContain('反对')
    expect(replay.text()).not.toContain('赞成')
  })

  it('shows the lady history and only reveals the viewer own result', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'team_building'
    snapshot.actions.canConfirmRole = false
    snapshot.players.push({
      id: 'p2',
      name: '被查验者',
      seat: 1,
      connected: true,
      isBot: false,
      isHost: false,
      isLeader: false,
      isSelected: false,
    })
    snapshot.lady.holderId = 'p2'
    snapshot.lady.history = [
      {
        inspectorId: 'p1',
        inspectorName: '测试玩家',
        targetId: 'p2',
        targetName: '被查验者',
        missionNumber: 2,
      },
    ]
    snapshot.lady.myChecks = [
      {
        targetId: 'p2',
        targetName: '被查验者',
        alignment: 'good',
        missionNumber: 2,
      },
    ]

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    const historyButton = wrapper
      .findAll('.game-toolbar button')
      .find((button) => button.text().includes('仙女记录'))
    expect(historyButton).toBeDefined()
    await historyButton!.trigger('click')

    const history = wrapper.get('.lady-history-modal').text()
    expect(history).toContain('第 2 次任务后')
    expect(history).toContain('1号 测试玩家')
    expect(history).toContain('2号 被查验者')
    expect(history).toContain('你看到： 好人阵营')
  })

  it('keeps voting controls available while the bottom chat is open', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'team_voting'
    snapshot.game.selectedTeamIds = ['p1']
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canVoteTeam = true

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    await wrapper.get('.chat-dock').trigger('click')

    expect(wrapper.get('.chat-sheet').attributes('role')).toBe('region')
    expect(wrapper.find('.chat-backdrop').exists()).toBe(false)
    expect(wrapper.get('.decision-button.approve').attributes('disabled')).toBeUndefined()
    expect(wrapper.classes()).toContain('chat-open')

    const initialStyle = wrapper.get('main').attributes('style') ?? ''
    const initialHeightMatch = initialStyle.match(
      /--chat-sheet-height:\s*([\d.]+)px/,
    )
    expect(initialHeightMatch).not.toBeNull()
    const initialHeight = Number.parseFloat(initialHeightMatch![1]!)
    const resizeHandle = wrapper.get('.chat-resize-handle')
    const pointerDown = new MouseEvent('pointerdown', {
      bubbles: true,
      clientY: 500,
    })
    Object.defineProperty(pointerDown, 'pointerId', { value: 1 })
    resizeHandle.element.dispatchEvent(pointerDown)
    const pointerMove = new MouseEvent('pointermove', {
      bubbles: true,
      clientY: 350,
    })
    Object.defineProperty(pointerMove, 'pointerId', { value: 1 })
    resizeHandle.element.dispatchEvent(pointerMove)
    await nextTick()
    const resizedStyle = wrapper.get('main').attributes('style') ?? ''
    const resizedHeightMatch = resizedStyle.match(
      /--chat-sheet-height:\s*([\d.]+)px/,
    )
    expect(resizedHeightMatch).not.toBeNull()
    const resizedHeight = Number.parseFloat(resizedHeightMatch![1]!)
    expect(resizedHeight).toBeGreaterThan(initialHeight)

    await wrapper.get('.chat-size-button').trigger('click')
    expect(wrapper.get('.chat-size-button').attributes('aria-label')).toBe(
      '还原聊天框',
    )
  })

  it('lets desktop users drag the chat window into unused space', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'team_voting'
    snapshot.actions.canConfirmRole = false
    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    await wrapper.get('.chat-dock').trigger('click')
    const sheet = wrapper.get('.chat-sheet')
    Object.defineProperty(sheet.element, 'getBoundingClientRect', {
      value: () => ({
        left: 400,
        top: 160,
        right: 900,
        bottom: 660,
        width: 500,
        height: 500,
        x: 400,
        y: 160,
        toJSON: () => ({}),
      }),
    })
    const moveHandle = wrapper.get('.chat-move-handle')
    const pointerDown = new MouseEvent('pointerdown', {
      bubbles: true,
      clientX: 500,
      clientY: 220,
    })
    Object.defineProperty(pointerDown, 'pointerId', { value: 2 })
    moveHandle.element.dispatchEvent(pointerDown)
    const pointerMove = new MouseEvent('pointermove', {
      bubbles: true,
      clientX: 560,
      clientY: 270,
    })
    Object.defineProperty(pointerMove, 'pointerId', { value: 2 })
    moveHandle.element.dispatchEvent(pointerMove)
    await nextTick()

    const style = wrapper.get('main').attributes('style') ?? ''
    expect(style).toContain('--chat-sheet-offset-x: 60px')
    expect(style).toContain('--chat-sheet-offset-y: 50px')
  })

  it('shows the irreversible early assassination confirmation to the assassin', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'team_building'
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canEarlyAssassinate = true
    snapshot.settings.earlyAssassinationEnabled = true
    snapshot.self.role = {
      code: 'assassin',
      label: '刺客',
      alignment: 'evil',
      description: '可以提前刺杀梅林。',
      knowledge: [],
    }
    snapshot.players.push({
      id: 'p2',
      name: '梅林候选人',
      seat: 1,
      connected: true,
      isBot: false,
      isHost: false,
      isLeader: false,
      isSelected: false,
    })

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    await wrapper.get('.game-toolbar .danger-tool').trigger('click')

    const modal = wrapper.get('.early-assassination-modal')
    expect(modal.text()).toContain('刺中梅林，坏人立即获胜')
    expect(modal.text()).toContain('刺错，好人立即获胜')
    expect(modal.text()).toContain('梅林候选人')
    expect(modal.get('.danger-button').attributes('disabled')).toBeDefined()

    await modal.get('.player-tile').trigger('click')
    expect(modal.get('.danger-button').attributes('disabled')).toBeUndefined()
    expect(modal.get('.danger-button').text()).toContain('2号 梅林候选人')
  })

  it('reveals every alignment and only offers good targets in final assassination', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'assassination'
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canAssassinate = true
    snapshot.self.role = {
      code: 'assassin',
      label: '刺客',
      alignment: 'evil',
      description: '找出梅林。',
      knowledge: [],
    }
    snapshot.players[0]!.alignment = 'evil'
    snapshot.players.push(
      {
        id: 'p2',
        name: '奥伯伦',
        seat: 1,
        connected: true,
        isBot: false,
        isHost: false,
        isLeader: false,
        isSelected: false,
        alignment: 'evil',
      },
      {
        id: 'p3',
        name: '梅林候选',
        seat: 2,
        connected: true,
        isBot: false,
        isHost: false,
        isLeader: false,
        isSelected: false,
        alignment: 'good',
      },
    )

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    const alignments = wrapper.get('.assassination-alignments').text()
    expect(alignments).toContain('奥伯伦')
    expect(alignments).toContain('坏人')
    expect(alignments).toContain('梅林候选')
    expect(alignments).toContain('好人')
    expect(wrapper.get('.player-grid').text()).toContain('梅林候选')
    expect(wrapper.get('.player-grid').text()).not.toContain('奥伯伦')
  })

  it('asks for confirmation before exiting an active game', async () => {
    const snapshot = roleRevealSnapshot(1)
    const pinia = createPinia()
    const room = useRoomStore(pinia)
    const leaveRoom = vi.spyOn(room, 'leaveRoom').mockResolvedValue()
    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [pinia] },
    })

    await wrapper.get('.exit-room-trigger').trigger('click')
    expect(wrapper.get('.exit-room-modal').text()).toContain(
      '座位、号码和身份都会保留',
    )
    await wrapper.get('.exit-room-modal .danger-button').trigger('click')

    expect(leaveRoom).toHaveBeenCalledOnce()
  })

  it('renders the early assassination target in the final record', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'game_over'
    snapshot.actions.canConfirmRole = false
    snapshot.result = {
      winner: 'evil',
      reason: '刺客提前刺杀并成功找出了梅林',
      assassinTargetId: 'p2',
      assassinationWasEarly: true,
    }
    snapshot.players[0] = {
      ...snapshot.players[0],
      role: 'assassin',
      roleLabel: '刺客',
      alignment: 'evil',
    }
    snapshot.players.push({
      id: 'p2',
      name: '真正的梅林',
      seat: 1,
      connected: true,
      isBot: false,
      isHost: false,
      isLeader: false,
      isSelected: false,
      role: 'merlin',
      roleLabel: '梅林',
      alignment: 'good',
    })

    const wrapper = mount(GameRoom, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    const record = wrapper.get('.assassination-record').text()
    expect(record).toContain('提前刺杀')
    expect(record).toContain('命中梅林')
    expect(record).toContain('1号 测试玩家')
    expect(record).toContain('2号 真正的梅林')
    expect(record).toContain('真实身份为 梅林')
  })

})
