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
        normalActionIds: response ? [] : restrictedToEquip ? ['equip'] : ['investigate', 'equip', 'arm'],
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

function scannerSnapshot(activated: boolean): ArcadeSnapshot {
  const current = snapshot()
  const game = current.game as unknown as SuspicionGameView
  const target = game.players[1]
  if (!target) throw new Error('fixture is missing the scanner target')
  if (activated) {
    const kinds = ['honest', 'crooked', 'kingpin'] as const
    const labels = ['正直', '腐败', '头目']
    target.cards.forEach((card, index) => {
      card.kind = kinds[index] ?? 'honest'
      card.label = labels[index] ?? '正直'
      card.knowledge = 'known'
      card.knowledgeKey = `target-${index}`
    })
  }
  game.pendingShot = {
    targetPlayerId: 'p2',
    source: 'gun',
    scannerPlayerId: 'p1',
    isMyDecision: true,
    scannerActivated: activated,
  }
  game.waiting = { kind: 'thumbprint_scanner', playerId: 'p1' }
  game.currentPrompt = {
    kind: 'thumbprint_scanner',
    title: '玩家2中枪，底细与伤害尚未结算',
    detail: activated ? '玩家1已使用指纹扫描器。' : '等待玩家1决定是否使用指纹扫描器。',
    decisionPlayerId: 'p1',
    isMyDecision: true,
    actorPlayerId: null,
    targetPlayerId: 'p2',
    targetCardIndex: null,
    sourceCardId: 'thumbprint_scanner',
  }
  game.legal.canTakeNormalAction = false
  game.legal.normalActionIds = []
  game.legal.investigationTargetPlayerIds = []
  return current
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

  it('submits the fingerprint kit self-target and return-to-hand choice', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const actionWithResult = vi.spyOn(arcade, 'actionWithResult').mockResolvedValue(true)
    const current = snapshot()
    const game = current.game as unknown as SuspicionGameView
    const fingerprintKit = {
      ...catalogCard,
      id: 'fingerprint_kit',
      number: 19,
      name: '指纹工具',
      englishName: 'Fingerprint Kit',
      description: '调查任意玩家一张暗置底细；公开自己一张暗牌可收回本牌。',
    }
    game.equipmentHand = [fingerprintKit]
    game.equipmentCatalog = [fingerprintKit]
    game.legal.playableEquipmentIds = ['fingerprint_kit']
    game.legal.equipmentOptions = [{
      cardId: 'fingerprint_kit',
      fields: [
        {
          key: 'targetSeat',
          label: '调查目标',
          kind: 'player',
          required: true,
          options: [{ value: 0, label: '玩家1' }, { value: 1, label: '玩家2' }],
        },
        {
          key: 'cardIndex',
          label: '目标暗置底细',
          kind: 'card',
          required: true,
          dependsOn: 'targetSeat',
          optionsByValue: {
            '0': [{ value: 0, label: '第1张' }],
            '1': [{ value: 1, label: '第2张' }],
          },
        },
        {
          key: 'returnToHand',
          label: '公开自己一张暗牌，让指纹工具回到手中',
          kind: 'boolean',
          required: false,
          default: false,
        },
        {
          key: 'ownCardIndex',
          label: '公开自己的底细',
          kind: 'card',
          required: true,
          options: [{ value: 1, label: '第2张 · 腐败' }],
          visibleWhen: { field: 'returnToHand', equals: true },
        },
      ],
    }]

    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: current },
      global: { plugins: [pinia] },
    })
    await wrapper.get('.equipment-hand article button').trigger('click')
    let selects = wrapper.findAll('.equipment-fields select')
    expect(selects).toHaveLength(2)
    await selects[0]?.setValue('0')
    await selects[1]?.setValue('0')
    await wrapper.get('.equipment-fields input[type="checkbox"]').setValue(true)
    selects = wrapper.findAll('.equipment-fields select')
    expect(selects).toHaveLength(3)
    await selects[2]?.setValue('1')
    await wrapper.get('.suspicion-modal .primary-button').trigger('click')

    expect(actionWithResult).toHaveBeenCalledWith('play_equipment', {
      cardId: 'fingerprint_kit',
      targetSeat: 0,
      cardIndex: 0,
      returnToHand: true,
      ownCardIndex: 1,
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

  it('lets the flashbang target privately choose all three new positions', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const current = snapshot()
    const game = current.game as unknown as SuspicionGameView
    game.choice = {
      kind: 'flashbang',
      isMyDecision: true,
      integrityCards: [
        { index: 0, kind: 'honest', label: '正直', revealed: false },
        { index: 1, kind: 'crooked', label: '腐败', revealed: true },
        { index: 2, kind: 'agent', label: '探员', revealed: false },
      ],
    }
    game.waiting = { kind: 'flashbang', playerId: 'p1' }
    game.currentPrompt = {
      kind: 'flashbang',
      title: '玩家2对玩家1使用了闪光弹',
      detail: '由玩家1决定自己三张底细的新顺序。',
      decisionPlayerId: 'p1',
      isMyDecision: true,
      actorPlayerId: 'p2',
      targetPlayerId: null,
      targetCardIndex: null,
      sourceCardId: 'flashbang',
    }

    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: current },
      global: { plugins: [pinia] },
    })
    const selects = wrapper.findAll('.decision-panel select')
    expect(selects).toHaveLength(3)
    expect(wrapper.get('.decision-panel .primary-button').attributes('disabled')).toBeDefined()
    await selects[0]?.setValue('2')
    await selects[1]?.setValue('0')
    await selects[2]?.setValue('1')
    await wrapper.get('.decision-panel .primary-button').trigger('click')

    expect(action).toHaveBeenCalledWith('reorder_integrity', {
      cardOrder: [2, 0, 1],
    })
  })

  it('lets the truth serum target choose one of their own hidden cards', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const current = snapshot()
    const game = current.game as unknown as SuspicionGameView
    const firstCard = game.players[0]?.cards[0]
    if (!firstCard) throw new Error('fixture is missing the target card')
    firstCard.revealed = true
    game.choice = {
      kind: 'truth_serum',
      isMyDecision: true,
    }
    game.waiting = { kind: 'truth_serum', playerId: 'p1' }
    game.currentPrompt = {
      kind: 'truth_serum',
      title: '玩家2对玩家1使用了吐真剂',
      detail: '玩家1必须选择自己的一张暗置底细永久公开。',
      decisionPlayerId: 'p1',
      isMyDecision: true,
      actorPlayerId: 'p2',
      targetPlayerId: null,
      targetCardIndex: null,
      sourceCardId: 'truth_serum',
    }

    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: current },
      global: { plugins: [pinia] },
    })
    const choices = wrapper.findAll('.card-choice-list button')
    expect(choices.map(button => button.text())).toEqual([
      '公开第2张',
      '公开第3张',
    ])
    await choices[0]?.trigger('click')

    expect(action).toHaveBeenCalledWith('choose_reveal', { cardIndex: 1 })
  })

  it('does not expose the shot target before the scanner is activated', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: scannerSnapshot(false) },
      global: { plugins: [pinia] },
    })

    const panel = wrapper.get('.urgent-panel')
    expect(panel.text()).toContain('底细尚未公开')
    expect(panel.find('select').exists()).toBe(false)
    const buttons = panel.findAll('button')
    expect(buttons.map(button => button.text())).toEqual(['使用并私看', '不使用'])
    await buttons[0]?.trigger('click')
    await buttons[1]?.trigger('click')

    expect(action).toHaveBeenNthCalledWith(1, 'use_scanner')
    expect(action).toHaveBeenNthCalledWith(2, 'pass_scanner')
  })

  it('lets an activated scanner exchange or continue without exchanging', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: scannerSnapshot(true) },
      global: { plugins: [pinia] },
    })

    const panel = wrapper.get('.urgent-panel')
    const selects = panel.findAll('select')
    expect(selects).toHaveLength(2)
    expect(selects[1]?.text()).toContain('正直')
    expect(selects[1]?.text()).toContain('腐败')
    expect(selects[1]?.text()).not.toContain('头目')
    const buttons = panel.findAll('button')
    expect(buttons.map(button => button.text())).toEqual([
      '交换并继续结算',
      '不交换，继续结算',
    ])
    expect(buttons[0]?.attributes('disabled')).toBeDefined()
    await selects[0]?.setValue('0')
    await selects[1]?.setValue('1')
    await buttons[0]?.trigger('click')
    await buttons[1]?.trigger('click')

    expect(action).toHaveBeenNthCalledWith(1, 'resolve_scanner', {
      ownCardIndex: 0,
      targetCardIndex: 1,
    })
    expect(action).toHaveBeenNthCalledWith(2, 'resolve_scanner')
  })

  it('lets an all-revealed player equip without choosing an integrity card', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot(false, true) },
      global: { plugins: [pinia] },
    })

    const equip = wrapper.findAll('.action-grid button').find(button => button.text().includes('获取装备'))
    expect(equip).toBeDefined()
    await equip?.trigger('click')
    expect(wrapper.find('.action-form select').exists()).toBe(false)
    await wrapper.get('.action-form .primary-button').trigger('click')

    expect(action).toHaveBeenCalledWith('equip', {})
  })

  it('lets an all-revealed player arm by choosing only a target', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot(false, true) },
      global: { plugins: [pinia] },
    })

    const arm = wrapper.findAll('.action-grid button').find(button => button.text().includes('武装'))
    expect(arm).toBeDefined()
    await arm?.trigger('click')
    const selects = wrapper.findAll('.action-form select')
    expect(selects).toHaveLength(1)
    await selects[0]?.setValue('1')
    await wrapper.get('.action-form .primary-button').trigger('click')

    expect(action).toHaveBeenCalledWith('arm', { targetSeat: 1 })
  })

  it('lets a fully revealed Crutches-revived player perform its required equip action', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot(false, true, true) },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.turn-console').text()).toContain('拐杖复活限制：此后只能获取装备')
    const actionButtons = wrapper.findAll('.action-grid button')
    expect(actionButtons).toHaveLength(1)
    expect(actionButtons[0]?.text()).toContain('获取装备')

    await actionButtons[0]?.trigger('click')
    expect(wrapper.find('.action-form select').exists()).toBe(false)
    await wrapper.get('.action-form .primary-button').trigger('click')

    expect(action).toHaveBeenCalledWith('equip', {})
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
