import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import MonopolyBoard from './MonopolyBoard.vue'

function board() {
  return Array.from({ length: 24 }, (_, index) => ({
    index,
    name: index === 1 ? '星河街' : index === 0 ? '梦想启程' : `城市 ${index}`,
    type: index === 1 ? 'property' : index === 0 ? 'start' : 'rest',
    ...(index === 1
      ? {
          group: 'sky',
          groupLabel: '星空蓝',
          color: '#58a7d8',
          price: 800,
          baseRent: 160,
          upgradeCost: 400,
        }
      : {}),
    ownerId: null,
    ownerName: null,
    ownerColor: null,
    houses: 0,
    rent: index === 1 ? 160 : undefined,
    groupComplete: false,
  }))
}

function snapshot(turnStage: 'await_roll' | 'await_purchase' = 'await_roll'): ArcadeSnapshot {
  const cells = board()
  return {
    revision: 1,
    roomCode: 'RICH',
    gameKey: 'monopoly',
    gameName: '大富翁',
    options: { startingCash: 8000, maxRounds: 20 },
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', name: '玩家一', seat: 0 },
    players: [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '玩家二', seat: 1, connected: true, isHost: false },
    ],
    requiredPlayers: 4,
    minimumPlayers: 2,
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
      board: cells,
      players: [
        { id: 'p1', name: '玩家一', seat: 0, color: '#ef6f6c', position: turnStage === 'await_purchase' ? 1 : 0, cash: 8000, netWorth: 8000, propertyCount: 0, bankrupt: false, jailedTurns: 0, isCurrent: true },
        { id: 'p2', name: '玩家二', seat: 1, color: '#57a4e5', position: 0, cash: 8000, netWorth: 8000, propertyCount: 0, bankrupt: false, jailedTurns: 0, isCurrent: false },
      ],
      currentPlayerId: 'p1',
      turnStage,
      lastRoll: turnStage === 'await_purchase' ? [3, 4] : null,
      currentRound: 1,
      maxRounds: 20,
      turnNumber: 1,
      passStartBonus: 1200,
      lastEvent: turnStage === 'await_purchase' ? '玩家一抵达星河街' : '玩家一先行',
      history: ['玩家一先行'],
      currentCell: turnStage === 'await_purchase' ? cells[1] : cells[0],
      standings: [
        { playerId: 'p1', name: '玩家一', netWorth: 8000, bankrupt: false },
        { playerId: 'p2', name: '玩家二', netWorth: 8000, bankrupt: false },
      ],
      legalActions: {
        canRoll: turnStage === 'await_roll',
        canBuy: turnStage === 'await_purchase',
        canDecline: turnStage === 'await_purchase',
        canUpgrade: false,
        canDeclineUpgrade: false,
      },
    },
  }
}

describe('MonopolyBoard', () => {
  it('renders the full city loop and rolls from the center console', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(MonopolyBoard, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    expect(wrapper.findAll('.fortune-cell')).toHaveLength(24)
    expect(wrapper.text()).toContain('第 1 / 20 回合')
    expect(wrapper.text()).toContain('梦想启程')
    await wrapper.get('.fortune-primary').trigger('click')

    expect(action).toHaveBeenCalledWith('roll')
  })

  it('offers buy and decline actions after landing on an unowned property', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(MonopolyBoard, {
      props: { snapshot: snapshot('await_purchase') },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('购买 ¥800')
    expect(wrapper.text()).toContain('暂不购买')
    await wrapper.get('.fortune-primary').trigger('click')

    expect(action).toHaveBeenCalledWith('buy_property')
  })
})
