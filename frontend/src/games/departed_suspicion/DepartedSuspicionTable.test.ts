import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import DepartedSuspicionTable from './DepartedSuspicionTable.vue'

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
    kind: own ? kind : null,
    label: own ? ['正直', '腐败', '探员'][index] : '未知',
    revealed: own && revealed,
    knowledge: own ? 'own' : 'hidden',
    wounded: false,
  }))
}

function snapshot(response = false, allOwnRevealed = false): ArcadeSnapshot {
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
    options: { equipmentSet: 'expanded' },
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
        restrictedToEquip: false,
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
        responsePlayerId: 'p2',
        isMyResponse: true,
      } : null,
      pendingShot: null,
      choice: null,
      postShot: null,
      waiting: response ? { kind: 'equipment_response', playerId: 'p2' } : null,
      legal: {
        canTakeNormalAction: !response,
        canTakeExtraInvestigation: false,
        canEndTurn: false,
        canRespond: response,
        responseEquipmentIds: response ? ['k9_unit'] : [],
        playableEquipmentIds: response ? ['k9_unit'] : [],
      },
      history: [],
      rulesNotice: '卧底牌能力尚未启用。',
    },
  }
}

describe('DepartedSuspicionTable', () => {
  it('renders private cards without exposing other hidden identities and submits an investigation', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    expect(wrapper.findAll('.integrity-card')).toHaveLength(12)
    expect(wrapper.findAll('.suspect-board')[0]?.text()).toContain('探员')
    expect(wrapper.findAll('.suspect-board')[1]?.text()).not.toContain('探员')

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

  it('shows the ordered response window and plays a legal response card', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const actionWithResult = vi.spyOn(arcade, 'actionWithResult').mockResolvedValue(true)
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot(true) },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.urgent-panel').text()).toContain('宣布射击')
    await wrapper.findAll('.equipment-actions button')[0]?.trigger('click')
    await wrapper.get('.suspicion-modal select').setValue('0')
    await wrapper.get('.suspicion-modal .primary-button').trigger('click')

    expect(actionWithResult).toHaveBeenCalledWith('play_equipment', {
      cardId: 'k9_unit',
      targetSeat: 0,
    })
  })

  it('allows an all-revealed player to arm without selecting an integrity card', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DepartedSuspicionTable, {
      props: { snapshot: snapshot(false, true) },
      global: { plugins: [pinia] },
    })

    await wrapper.findAll('.action-grid button')[2]?.trigger('click')
    expect(wrapper.get('.action-cost-note').text()).toContain('无需再公开底细')
    const selects = wrapper.findAll('.action-form select')
    expect(selects).toHaveLength(1)
    await selects[0]?.setValue('1')
    await wrapper.get('.action-form .primary-button').trigger('click')

    expect(action).toHaveBeenCalledWith('arm', { targetSeat: 1 })
  })
})
