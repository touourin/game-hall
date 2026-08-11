import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import DepartedSuspicionTable from './DepartedSuspicionTable.vue'
import type { SuspicionGameView } from './types'

const catalogCard = {
  id: 'k9_unit',
  number: 6,
  name: '警犬队',
  englishName: 'K-9 Unit',
  expansion: 'base',
  timing: 'anytime',
  description: '令一名持枪玩家立即丢枪。',
  persistent: false,
  requiresCover: false,
  available: true,
}

function cards(own: boolean, revealed = false) {
  return ['honest', 'crooked', 'agent'].map((kind, index) => ({
    index,
    knowledgeKey: null,
    kind: own ? kind : null,
    label: own ? ['正直', '腐败', '探员'][index] : '未知',
    revealed: own && revealed,
    knowledge: own ? 'own' : 'hidden',
    wounded: false,
  }))
}

function snapshot(response = false, allOwnRevealed = false, restrictedToEquip = false): ArcadeSnapshot {
  const players = Array.from({ length: 4 }, (_, seat) => ({
    id: `p${seat + 1}`,
    name: `玩家${seat + 1}`,
    seat,
    connected: true,
    isHost: seat === 0,
  }))
  return {
    revision: 1,
    roomCode: 'COPS',
    gameKey: 'departed_suspicion',
    gameName: '无间疑云',
    options: { equipmentSet: 'bombers' },
    phase: 'playing',
    hostId: 'p1',
    self: { id: response ? 'p2' : 'p1', name: response ? '玩家2' : '玩家1', seat: response ? 1 : 0 },
    players,
    requiredPlayers: 8,
    minimumPlayers: 4,
    roundNumber: 1,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: {
      canStart: false,
      canRestart: false,
      canAct: true,
      canKickPlayers: false,
      canDissolve: false,
      canEditRules: false,
      canRequestUndo: false,
      canRequestDraw: false,
      canResolveRequest: false,
    },
    rematchReadyPlayerIds: [],
    request: null,
    chat: { maxLength: 300, messages: [] },
    game: {
      turnPlayerId: 'p1',
      turnNumber: 1,
      direction: 'clockwise',
      centralGuns: 2,
      actionDone: false,
      extraInvestigationDone: false,
      players: players.map(player => ({
        playerId: player.id,
        seat: player.seat,
        alive: true,
        gun: player.id === 'p1' && response,
        aimPlayerId: player.id === 'p1' && response ? 'p2' : null,
        equipmentCount: player.id === 'p2' && response ? 1 : 0,
        effects: [],
        restrictedToEquip: player.id === (response ? 'p2' : 'p1') && restrictedToEquip,
        cards: cards(player.id === (response ? 'p2' : 'p1'), allOwnRevealed),
        team: player.id === (response ? 'p2' : 'p1') ? 'honest' : null,
      })),
      selfTeam: 'honest',
      equipmentHand: response ? [catalogCard] : [],
      equipmentCatalog: [catalogCard],
      pendingAction: response ? {
        actorPlayerId: 'p1',
        action: 'shoot',
        actionLabel: '射击',
        targetPlayerId: 'p2',
        targetCardIndex: null,
        responsePlayerId: 'p2',
        isMyResponse: true,
      } : null,
      pendingShot: null,
      choice: null,
      postShot: null,
      waiting: response ? { kind: 'equipment_response', playerId: 'p2' } : null,
      currentPrompt: response ? {
        kind: 'equipment_response',
        title: '玩家1宣布射击玩家2',
        detail: '等待玩家2决定是否使用装备。',
        decisionPlayerId: 'p2',
        isMyDecision: true,
        actorPlayerId: 'p1',
        targetPlayerId: 'p2',
        targetCardIndex: null,
        sourceCardId: null,
      } : null,
      legal: {
        canTakeNormalAction: !response,
        normalActionIds: response || allOwnRevealed ? [] : restrictedToEquip ? ['equip'] : ['investigate', 'equip', 'arm'],
        canPassNormalAction: !response && allOwnRevealed,
        investigationTargetPlayerIds: response ? [] : ['p2', 'p3', 'p4'],
        canTakeExtraInvestigation: false,
        canEndTurn: false,
        canRespond: response,
        responseEquipmentIds: response ? ['k9_unit'] : [],
        playableEquipmentIds: response ? ['k9_unit'] : [],
        equipmentOptions: response ? [{
          cardId: 'k9_unit',
          fields: [{
            key: 'targetSeat',
            label: '持枪玩家',
            kind: 'player',
            required: true,
            options: [{ value: 0, label: '玩家1' }],
          }],
        }] : [],
      },
      history: [],
      rulesNotice: '卧底牌能力尚未启用。',
    },
  }
}

describe('DepartedSuspicionTable', () => {
  it('reveals private identity in place only while held and submits an investigation', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    expect(wrapper.findAll('.integrity-card')).toHaveLength(12)
    expect(wrapper.findAll('.suspect-board')[0]?.text()).not.toContain('探员')
    expect(wrapper.findAll('.suspect-board')[1]?.text()).not.toContain('探员')
    expect(wrapper.text()).not.toContain('正直阵营')

    const teamButton = wrapper.get('.private-team-trigger')
    await teamButton.trigger('pointerdown')
    expect(teamButton.text()).toContain('正直阵营')
    await teamButton.trigger('pointerup')
    expect(teamButton.text()).not.toContain('正直阵营')

    const ownAgentCard = wrapper.findAll('.suspect-board')[0]?.findAll('.integrity-card')[2]
    expect(ownAgentCard?.text()).not.toContain('探员')
    await ownAgentCard?.trigger('pointerdown')
    expect(ownAgentCard?.text()).toContain('探员')
    await ownAgentCard?.trigger('pointerup')
    expect(ownAgentCard?.text()).not.toContain('探员')
    expect(wrapper.find('.private-info-modal').exists()).toBe(false)

    await wrapper.findAll('.action-grid button')[0]?.trigger('click')
    const selects = wrapper.findAll('.action-form select')
    await selects[0]?.setValue('1')
    await selects[1]?.setValue('0')
    await wrapper.get('.action-form .primary-button').trigger('click')

    expect(action).toHaveBeenCalledWith('investigate', {
      targetSeat: 1,
      cardIndex: 0,
    })
  })

  it('marks newly investigated cards on the board and reveals them only while held', async () => {
    const pinia = createPinia()
    const initial = snapshot()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: initial },
      global: { plugins: [pinia] },
    })

    const investigated = snapshot()
    const investigatedGame = investigated.game as unknown as SuspicionGameView
    const investigatedCard = investigatedGame.players[1]?.cards[0]
    if (!investigatedCard) throw new Error('fixture is missing the investigated card')
    Object.assign(investigatedCard, {
      knowledgeKey: 'crooked-investigated',
      kind: 'crooked',
      label: '腐败',
      knowledge: 'known',
    })
    await wrapper.setProps({ snapshot: investigated })

    expect(wrapper.get('.private-result-notice').text()).toContain('获得 1 条新底细')
    expect(wrapper.get('.private-result-notice').text()).toContain('玩家2 · 第1张')
    const card = wrapper.findAll('.suspect-board')[1]?.findAll('.integrity-card')[0]
    expect(card?.text()).toContain('已掌握')
    expect(card?.text()).not.toContain('腐败')
    await card?.trigger('pointerdown')
    expect(card?.text()).toContain('腐败')
    await card?.trigger('pointerup')
    expect(card?.text()).not.toContain('腐败')
  })

  it('collects one metal detector choice for every eligible armed player', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const actionWithResult = vi.spyOn(arcade, 'actionWithResult').mockResolvedValue(true)
    const current = snapshot()
    const game = current.game as unknown as SuspicionGameView
    const metalDetector = {
      ...catalogCard,
      id: 'metal_detector',
      number: 7,
      name: '金属探测器',
      englishName: 'Metal Detector',
      timing: 'anytime',
      description: '依次调查每名持枪玩家的一张暗置底细。',
    }
    game.players[1].gun = true
    game.players[2].gun = true
    game.equipmentHand = [metalDetector]
    game.equipmentCatalog = [metalDetector]
    game.legal.playableEquipmentIds = ['metal_detector']
    game.legal.equipmentOptions = [{
      cardId: 'metal_detector',
      fields: [
        { key: 'choices.1', label: '玩家2的暗置底细', kind: 'card', required: true, options: [{ value: 1, label: '第2张' }] },
        { key: 'choices.2', label: '玩家3的暗置底细', kind: 'card', required: true, options: [{ value: 2, label: '第3张' }] },
      ],
    }]

    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: current },
      global: { plugins: [pinia] },
    })

    await wrapper.get('.equipment-hand article button').trigger('click')
    const selects = wrapper.findAll('.equipment-fields select')
    expect(selects).toHaveLength(2)
    expect(wrapper.get('.suspicion-modal .primary-button').attributes('disabled')).toBeDefined()
    await selects[0]?.setValue('1')
    await selects[1]?.setValue('2')
    await wrapper.get('.suspicion-modal .primary-button').trigger('click')

    expect(actionWithResult).toHaveBeenCalledWith('play_equipment', {
      cardId: 'metal_detector',
      choices: { '1': 1, '2': 2 },
    })
  })

  it('renders dependent equipment fields from the server contract', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const actionWithResult = vi.spyOn(arcade, 'actionWithResult').mockResolvedValue(true)
    const current = snapshot()
    const game = current.game as unknown as SuspicionGameView
    const blackmail = {
      ...catalogCard,
      id: 'blackmail',
      number: 1,
      name: '勒索信',
      englishName: 'Blackmail',
      description: '交换两名其他存活玩家各一张底细。',
    }
    const players = [
      { value: 1, label: '玩家2' },
      { value: 2, label: '玩家3' },
      { value: 3, label: '玩家4' },
    ]
    const cardsByPlayer = {
      '1': [{ value: 0, label: '第1张' }],
      '2': [{ value: 1, label: '第2张' }],
      '3': [{ value: 2, label: '第3张' }],
    }
    game.equipmentHand = [blackmail]
    game.equipmentCatalog = [blackmail]
    game.legal.playableEquipmentIds = ['blackmail']
    game.legal.equipmentOptions = [{
      cardId: 'blackmail',
      fields: [
        { key: 'firstSeat', label: '第一名玩家', kind: 'player', required: true, options: players },
        { key: 'firstCardIndex', label: '第一张底细', kind: 'card', required: true, dependsOn: 'firstSeat', optionsByValue: cardsByPlayer },
        { key: 'secondSeat', label: '第二名玩家', kind: 'player', required: true, options: players, distinctFrom: 'firstSeat' },
        { key: 'secondCardIndex', label: '第二张底细', kind: 'card', required: true, dependsOn: 'secondSeat', optionsByValue: cardsByPlayer },
      ],
    }]

    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: current },
      global: { plugins: [pinia] },
    })
    await wrapper.get('.equipment-hand article button').trigger('click')
    const selects = wrapper.findAll('.equipment-fields select')
    await selects[0]?.setValue('1')
    await selects[1]?.setValue('0')
    expect(selects[2]?.findAll('option').map(option => option.text())).not.toContain('玩家2')
    await selects[2]?.setValue('2')
    await selects[3]?.setValue('1')
    await wrapper.get('.suspicion-modal .primary-button').trigger('click')

    expect(actionWithResult).toHaveBeenCalledWith('play_equipment', {
      cardId: 'blackmail',
      firstSeat: 1,
      firstCardIndex: 0,
      secondSeat: 2,
      secondCardIndex: 1,
    })
  })

  it('shows the ordered response window and plays a legal response card', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const actionWithResult = vi.spyOn(arcade, 'actionWithResult').mockResolvedValue(true)
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot(true) },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.current-prompt').text()).toContain('玩家1宣布射击玩家2')
    expect(wrapper.get('.urgent-panel').text()).toContain('装备响应')
    await wrapper.findAll('.equipment-actions button')[0]?.trigger('click')
    await wrapper.get('.suspicion-modal select').setValue('0')
    await wrapper.get('.suspicion-modal .primary-button').trigger('click')

    expect(actionWithResult).toHaveBeenCalledWith('play_equipment', {
      cardId: 'k9_unit',
      targetSeat: 0,
    })
  })

  it('offers a skip when an all-revealed player has no legal normal action', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot(false, true) },
      global: { plugins: [pinia] },
    })

    expect(wrapper.findAll('.action-grid button')).toHaveLength(0)
    const skip = wrapper.get('.extra-action')
    expect(skip.text()).toContain('没有合法行动')
    await skip.trigger('click')

    expect(action).toHaveBeenCalledWith('pass_turn')
  })

  it('lets a fully revealed Crutches-revived player skip instead of equipping for free', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot(false, true, true) },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.turn-console').text()).toContain('拐杖复活限制：此后只能获取装备')
    const actionButtons = wrapper.findAll('.action-grid button')
    expect(actionButtons).toHaveLength(0)

    await wrapper.get('.extra-action').trigger('click')

    expect(action).toHaveBeenCalledWith('pass_turn')
  })

  it('places actionable controls before the player board', () => {
    const pinia = createPinia()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    const children = Array.from(wrapper.element.children)
    expect(children.indexOf(wrapper.get('.turn-console').element)).toBeLessThan(
      children.indexOf(wrapper.get('.investigation-board').element),
    )
  })
})
