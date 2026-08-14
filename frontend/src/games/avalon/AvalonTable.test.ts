import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { RoomSnapshot } from './types'
import AvalonTable from './AvalonTable.vue'

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
    chat: {
      maxLength: 300,
      messages: [],
    },
    actions: {
      canStart: false,
      canUpdateSettings: false,
      canDissolve: false,
      canLeave: false,
      canConfirmRole: true,
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
}

describe('AvalonTable role reveal', () => {
  beforeEach(() => {
    localStorage.clear()
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

    const wrapper = mount(AvalonTable, {
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

    const wrapper = mount(AvalonTable, {
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

    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.initial-lady-card').text()).toContain(
      '2号 仙女持有者',
    )
    expect(wrapper.get('.player-number-roster').text()).toContain('仙女')
  })

  it('keeps the current Lady holder visible while the first team is built', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'team_building'
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canProposeTeam = true
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

    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    const reminder = wrapper.get('.mission-lady-reminder')
    expect(reminder.text()).toContain('湖中仙女当前持有者')
    expect(reminder.text()).toContain('2号 仙女持有者')
    expect(reminder.text()).toContain('第 2 次任务结束后首次查验')

    const holderTile = wrapper.findAll('.player-tile')[1]!
    expect(holderTile.get('.lady-chip').text()).toContain('仙女')
  })

  it('keeps confirmation enabled when another player updates the room', async () => {
    const wrapper = mount(AvalonTable, {
      props: { snapshot: roleRevealSnapshot(1) },
      global: { plugins: [createPinia()] },
    })

    const confirmButton = wrapper.get('.ui-button--primary')
    expect(confirmButton.attributes('disabled')).toBeDefined()

    await wrapper.get('.press-reveal-card').trigger('pointerdown')
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

    const wrapper = mount(AvalonTable, {
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

    const wrapper = mount(AvalonTable, {
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

    const wrapper = mount(AvalonTable, {
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
    snapshot.result.eligibleTargetIds = ['p2']
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
    snapshot.players.push({
      id: 'p3',
      name: '已知的莫甘娜',
      seat: 2,
      connected: true,
      isBot: false,
      isHost: false,
      isLeader: false,
      isSelected: false,
    })

    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    await wrapper.get('.game-toolbar .danger-tool').trigger('click')

    const modal = wrapper.get('.early-assassination-modal')
    expect(modal.text()).toContain('刺中梅林，坏人立即获胜')
    expect(modal.text()).toContain('刺错，好人立即获胜')
    expect(modal.text()).toContain('梅林候选人')
    expect(modal.text()).not.toContain('已知的莫甘娜')
    expect(modal.get('.ui-button--danger').attributes('disabled')).toBeDefined()

    await modal.get('.player-tile').trigger('click')
    expect(modal.get('.ui-button--danger').attributes('disabled')).toBeUndefined()
    expect(modal.get('.ui-button--danger').text()).toContain('2号 梅林候选人')
  })

  it('reveals known evil while keeping Oberon among assassination candidates', () => {
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
    snapshot.settings.rolePreset = [{ code: 'oberon', label: '奥伯伦' }]
    snapshot.players[0]!.alignment = 'evil'
    snapshot.result.eligibleTargetIds = ['p2', 'p3']
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
      },
      {
        id: 'p4',
        name: '已知的莫甘娜',
        seat: 3,
        connected: true,
        isBot: false,
        isHost: false,
        isLeader: false,
        isSelected: false,
        alignment: 'evil',
      },
    )

    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    const alignments = wrapper.get('.assassination-alignments').text()
    expect(alignments).toContain('奥伯伦不会现身')
    expect(alignments).toContain('坏人')
    const publicAlignmentPlayers = wrapper
      .findAll('.assassination-alignments > div > span')
      .map((player) => player.text())
    expect(
      publicAlignmentPlayers.some((player) => player.includes('奥伯伦')),
    ).toBe(false)
    expect(
      publicAlignmentPlayers.some((player) => player.includes('梅林候选')),
    ).toBe(false)
    const assassinationCandidates = wrapper.get('.player-grid').text()
    expect(assassinationCandidates).toContain('梅林候选')
    expect(assassinationCandidates).toContain('奥伯伦')
    expect(assassinationCandidates).not.toContain('已知的莫甘娜')
  })

  it('shows only the private dagger candidates to the assassin', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'dagger_grant'
    snapshot.settings.mode = 'court_undercurrent'
    snapshot.courtUndercurrent.enabled = true
    snapshot.courtUndercurrent.daggerCandidateIds = ['p2', 'p3']
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canGrantDagger = true
    snapshot.self.role = {
      code: 'assassin',
      label: '刺客',
      alignment: 'evil',
      description: '寻找心怀异念之臣。',
      knowledge: [],
    }
    snapshot.players.push(
      {
        id: 'p2',
        name: '二号候选',
        seat: 1,
        connected: true,
        isBot: false,
        isHost: false,
        isLeader: false,
        isSelected: false,
      },
      {
        id: 'p3',
        name: '三号候选',
        seat: 2,
        connected: true,
        isBot: false,
        isHost: false,
        isLeader: false,
        isSelected: false,
      },
      {
        id: 'p4',
        name: '名单外玩家',
        seat: 3,
        connected: true,
        isBot: false,
        isHost: false,
        isLeader: false,
        isSelected: false,
      },
    )
    const pinia = createPinia()
    const room = useArcadeStore(pinia)
    const action = vi.spyOn(room, 'action').mockResolvedValue()
    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('刺客最后的授刃')
    expect(wrapper.get('.player-grid').text()).toContain('二号候选')
    expect(wrapper.get('.player-grid').text()).toContain('三号候选')
    expect(wrapper.get('.player-grid').text()).not.toContain('名单外玩家')
    await wrapper.findAll('.player-grid .player-tile')[0]!.trigger('click')
    await wrapper.get('.ui-button--danger').trigger('click')

    expect(action).toHaveBeenCalledWith('grant_dagger', {
      target_id: 'p2',
    })
  })

  it('lets only the transformed courtier end the final council', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'final_council'
    snapshot.settings.mode = 'court_undercurrent'
    snapshot.courtUndercurrent.enabled = true
    snapshot.courtUndercurrent.daggerTargetId = 'p1'
    snapshot.courtUndercurrent.daggerHit = true
    snapshot.courtUndercurrent.transformedPlayerId = 'p1'
    snapshot.courtUndercurrent.eligibleTargetIds = ['p2', 'p3']
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canDissentingAssassinate = true
    snapshot.self.role = {
      code: 'dissenting_courtier',
      label: '心怀异念之臣',
      alignment: 'evil',
      description: '你已被强制转化。',
      knowledge: [],
    }
    snapshot.players.push(
      {
        id: 'p2',
        name: '梅林候选甲',
        seat: 1,
        connected: true,
        isBot: false,
        isHost: false,
        isLeader: false,
        isSelected: false,
      },
      {
        id: 'p3',
        name: '梅林候选乙',
        seat: 2,
        connected: true,
        isBot: false,
        isHost: false,
        isLeader: false,
        isSelected: false,
      },
    )
    const pinia = createPinia()
    const room = useArcadeStore(pinia)
    const action = vi.spyOn(room, 'action').mockResolvedValue()
    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('王庭最后议事')
    expect(wrapper.text()).toContain('1号 测试玩家 已接过黑誓之刃')
    expect(wrapper.text()).toContain('你已必定转化为邪恶阵营')
    await wrapper.findAll('.player-grid .player-tile')[1]!.trigger('click')
    await wrapper.get('.ui-button--danger').trigger('click')

    expect(action).toHaveBeenCalledWith('dissenting_assassinate', {
      target_id: 'p3',
    })
  })

  it('submits the forced shadow-council target ballot', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'exile_council_ballot'
    snapshot.settings.mode = 'court_undercurrent'
    snapshot.settings.shadowMerlinEnabled = true
    snapshot.shadowMerlin.enabled = true
    snapshot.shadowMerlin.councilTriggered = true
    snapshot.shadowMerlin.eligibleExileTargetIds = ['p1']
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canSubmitExileCouncilBallot = true
    const pinia = createPinia()
    const room = useArcadeStore(pinia)
    const action = vi.spyOn(room, 'action').mockResolvedValue()
    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('祓影议庭强制开启')
    expect(wrapper.text()).toContain('议庭已经开启')
    expect(wrapper.text()).toContain('提交祓影票')
    expect(wrapper.text()).not.toContain('启庭表决')
    expect(wrapper.text()).not.toContain('裁影')
    expect(wrapper.text()).toContain('系统不会提示你的票是否有效')
    await wrapper.get('.player-grid .player-tile').trigger('click')
    await wrapper.get('.ui-button--primary').trigger('click')

    expect(action).toHaveBeenCalledWith('exile_council_ballot', {
      open_council: true,
      target_id: 'p1',
    })
  })

  it('only lets a non-assassin abandon the council assassination', async () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'exile_council_assassination_decision'
    snapshot.settings.mode = 'court_undercurrent'
    snapshot.settings.shadowMerlinEnabled = true
    snapshot.shadowMerlin.enabled = true
    snapshot.shadowMerlin.councilTriggered = true
    snapshot.shadowMerlin.councilOpened = true
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canSubmitExileCouncilAssassinationDecision = true
    snapshot.self.role = {
      code: 'loyal_servant',
      label: '亚瑟的忠臣',
      alignment: 'good',
      description: '没有额外信息。',
      knowledge: [],
    }
    const pinia = createPinia()
    const room = useArcadeStore(pinia)
    const action = vi.spyOn(room, 'action').mockResolvedValue()
    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('你并非刺客，只需确认放弃刺杀')
    expect(wrapper.find('.decision-button.approve').exists()).toBe(false)
    await wrapper.get('.decision-button.reject').trigger('click')
    await wrapper.get('.ui-button--danger').trigger('click')

    expect(action).toHaveBeenCalledWith(
      'council_assassination_decision',
      { assassinate: false },
    )
  })

  it('lets the assassin choose whether to launch the council assassination', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'exile_council_assassination_decision'
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canSubmitExileCouncilAssassinationDecision = true
    snapshot.self.role = {
      code: 'assassin',
      label: '刺客',
      alignment: 'evil',
      description: '刺杀梅林。',
      knowledge: [],
    }
    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('你是刺客，请决定是否发动刺杀')
    expect(wrapper.text()).toContain('放弃刺杀')
    expect(wrapper.text()).toContain('发动刺杀')
  })

  it('does not ask shadow Merlin to choose the assassination target', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'exile_council_assassination_target'
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canSubmitExileCouncilAssassinationTarget = false
    snapshot.self.role = {
      code: 'shadow_merlin',
      label: '暗影梅林',
      alignment: 'good',
      description: '保护梅林。',
      knowledge: [],
    }
    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('刺客正在选择目标')
    expect(wrapper.text()).toContain('你不需要进行任何操作')
    expect(wrapper.find('.player-grid').exists()).toBe(false)
  })

  it('only shows the council target picker to the assassin', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'exile_council_assassination_target'
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canSubmitExileCouncilAssassinationTarget = true
    snapshot.shadowMerlin.eligibleAssassinationTargetIds = ['p2']
    snapshot.self.role = {
      code: 'assassin',
      label: '刺客',
      alignment: 'evil',
      description: '刺杀梅林。',
      knowledge: [],
    }
    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('你是刺客，请选择刺杀目标')
    expect(wrapper.find('.player-grid').exists()).toBe(true)
  })

  it('renders the early assassination target in the final record', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'game_over'
    snapshot.actions.canConfirmRole = false
    snapshot.result = {
      winner: 'evil',
      reason: '刺客提前刺杀并成功找出了梅林',
      endingRoute: 'standard_assassination',
      assassinTargetId: 'p2',
      assassinationWasEarly: true,
      eligibleTargetIds: [],
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

    const wrapper = mount(AvalonTable, {
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

  it('shows five rejected proposals as one failed mission', () => {
    const snapshot = roleRevealSnapshot(1)
    snapshot.phase = 'round_result'
    snapshot.actions.canConfirmRole = false
    snapshot.actions.canContinueRound = true
    snapshot.game.missionHistory = [
      {
        number: 1,
        teamIds: [],
        success: false,
        failCount: 0,
        failedByRejections: true,
      },
    ]
    snapshot.game.failCount = 1

    const wrapper = mount(AvalonTable, {
      props: { snapshot },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.result-hero').text()).toContain('任务失败')
    expect(wrapper.get('.result-hero').text()).toContain(
      '连续五次组队被否决，本次任务直接失败',
    )
    expect(wrapper.get('.score-summary').text()).toContain('莫德雷德阵营1次失败')
  })

})
