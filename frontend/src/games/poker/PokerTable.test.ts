import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import PokerTable from './PokerTable.vue'

function card(id: string, rankLabel: string, suitSymbol: string, red = false) {
  return { id, rank: 14, rankLabel, suit: 'spade', suitSymbol, red }
}

function snapshot(showdown = false): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'TEST',
    gameKey: 'poker',
    gameName: '德州扑克',
    options: { startingChips: 1000, smallBlind: 10 },
    phase: showdown ? 'finished' : 'playing',
    hostId: 'p1',
    self: { id: 'p1', name: '玩家一', seat: 0 },
    players: [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '玩家二', seat: 1, connected: true, isHost: false },
    ],
    requiredPlayers: 8,
    minimumPlayers: 2,
    roundNumber: 1,
    winner: showdown ? 'poker' : null,
    winnerPlayerIds: showdown ? ['p1'] : [],
    winReason: showdown ? '玩家一赢得本局' : null,
    actions: {
      canStart: false,
      canRestart: showdown,
      canAct: !showdown,
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
      street: showdown ? 'showdown' : 'preflop',
      streetLabel: showdown ? '摔牌' : '翻牌前',
      communityCards: [card('board-a', 'A', '♠')],
      pot: 60,
      currentBet: 20,
      smallBlind: 10,
      bigBlind: 20,
      startingChips: 1000,
      actionPlayerId: showdown ? null : 'p1',
      dealerPlayerId: 'p1',
      showdown,
      sidePots: [],
      history: [{ street: 'preflop', playerId: 'p2', action: 'big_blind', amount: 20 }],
      handNumber: 1,
      lastHandReason: showdown ? '玩家一赢得本手' : null,
      nextHandReadyPlayerIds: [],
      requiredNextHandReadyCount: 2,
      canReadyNextHand: false,
      eliminatedIds: [],
      legalActions: showdown
        ? { canAct: false, canFold: false, canCheck: false, canCall: false, canRaise: false, canAllIn: false, callAmount: 0, minimumRaiseTo: 0, maximumRaiseTo: 0 }
        : { canAct: true, canFold: true, canCheck: false, canCall: true, canRaise: true, canAllIn: true, callAmount: 20, minimumRaiseTo: 40, maximumRaiseTo: 1000 },
      players: [
        { id: 'p1', name: '玩家一', seat: 0, chips: 1000, streetBet: 0, totalBet: 0, folded: false, allIn: false, isDealer: true, isSmallBlind: true, isBigBlind: false, isActing: !showdown, cards: [card('as', 'A', '♠'), card('kh', 'K', '♥', true)], cardCount: 2, handName: showdown ? '一对' : null, payout: showdown ? 60 : 0, eliminated: false, readyNextHand: false },
        { id: 'p2', name: '玩家二', seat: 1, chips: 980, streetBet: 20, totalBet: 20, folded: false, allIn: false, isDealer: false, isSmallBlind: false, isBigBlind: true, isActing: false, cards: showdown ? [card('qc', 'Q', '♣'), card('jd', 'J', '♦', true)] : [], cardCount: 2, handName: showdown ? '高牌' : null, payout: 0, eliminated: false, readyNextHand: false },
      ],
    },
  }
}

describe('PokerTable', () => {
  it('shows private cards, hidden opponents, and submits betting actions', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(PokerTable, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('底池 60')
    expect(wrapper.findAll('.own-card')).toHaveLength(2)
    expect(wrapper.findAll('.card-back')).toHaveLength(2)
    const call = wrapper.findAll('.primary-actions button').find((button) => button.text().includes('跟注 20'))
    await call?.trigger('click')

    expect(action).toHaveBeenCalledWith('call', {})
  })

  it('calculates half-pot and pot raises after including the call', async () => {
    const wrapper = mount(PokerTable, {
      props: { snapshot: snapshot() },
      global: { plugins: [createPinia()] },
    })
    const buttons = wrapper.findAll('.quick-raises button')
    const input = wrapper.get<HTMLInputElement>('.raise-controls input')

    await buttons.find((button) => button.text() === '1/2 底池')?.trigger('click')
    expect(input.element.value).toBe('60')
    await buttons.find((button) => button.text() === '底池')?.trigger('click')
    expect(input.element.value).toBe('100')
  })

  it('shows the total raise-to amount in action history', () => {
    const current = snapshot()
    current.game.history = [{
      street: 'preflop',
      playerId: 'p2',
      action: 'raise',
      amount: 70,
      streetBet: 90,
    }]
    const wrapper = mount(PokerTable, {
      props: { snapshot: current },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.poker-history').text()).toContain('玩家二加注到90')
    expect(wrapper.get('.poker-history').text()).not.toContain('加注到70')
  })

  it('reveals active opponents at showdown', () => {
    const wrapper = mount(PokerTable, {
      props: { snapshot: snapshot(true) },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.card-back')).toHaveLength(0)
    expect(wrapper.text()).toContain('一对')
    expect(wrapper.text()).toContain('高牌')
    expect(wrapper.text()).toContain('赢得 60')
  })

  it('lets surviving players prepare the next hand', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const current = snapshot(true)
    current.phase = 'between_hands'
    current.winner = null
    current.winnerPlayerIds = []
    current.winReason = null
    current.game.canReadyNextHand = true

    const wrapper = mount(PokerTable, {
      props: { snapshot: current },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.next-hand-panel').text()).toContain('第 1 手牌结束')
    await wrapper.get('.next-hand-panel .ui-button--primary').trigger('click')
    expect(action).toHaveBeenCalledWith('ready_next_hand', {})
  })
})
