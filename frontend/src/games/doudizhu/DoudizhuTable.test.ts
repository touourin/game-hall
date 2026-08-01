import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import DoudizhuTable from './DoudizhuTable.vue'

function playingSnapshot(): ArcadeSnapshot {
  return {
    revision: 3,
    roomCode: 'TEST',
    gameKey: 'doudizhu',
    gameName: '斗地主',
    options: {},
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', name: '玩家一', seat: 0 },
    players: [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '玩家二', seat: 1, connected: true, isHost: false },
      { id: 'p3', name: '玩家三', seat: 2, connected: true, isHost: false },
    ],
    requiredPlayers: 3,
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
      phase: 'playing',
      variant: 'classic',
      currentPlayerId: 'p1',
      bids: [
        { type: 'bid', playerId: 'p1', playerName: '玩家一', decision: 'call' },
        { type: 'bid', playerId: 'p2', playerName: '玩家二', decision: 'pass' },
        { type: 'bid', playerId: 'p3', playerName: '玩家三', decision: 'pass' },
      ],
      biddingMode: 'rob',
      landlordCandidatePlayerId: 'p1',
      landlordPlayerId: 'p1',
      bottomCards: [],
      hand: [{ id: '3-spade', rank: 3, label: '3', suit: 'spade' }],
      cardCounts: { p1: 1, p2: 17, p3: 17 },
      teams: { p1: 'landlord', p2: 'farmer', p3: 'farmer' },
      lastPlay: null,
      lastPlayPlayerId: null,
      multiplier: 1,
      multiplierEvents: [],
      wildRank: null,
      wildLabel: null,
      history: [],
      remainingRanks: {},
      scores: {},
      settlement: null,
    },
  }
}

describe('DoudizhuTable', () => {
  it('renders the three-seat table and explains the selected pattern', async () => {
    const next = playingSnapshot()
    ;(next.game.hand as Array<Record<string, unknown>>) = [
      { id: '7-spade', rank: 7, label: '7', suit: 'spade' },
      { id: '7-heart', rank: 7, label: '7', suit: 'heart' },
    ]
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: next },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.find('.landlord-felt').exists()).toBe(true)
    expect(wrapper.findAll('.opponent')).toHaveLength(2)
    expect(wrapper.get('.self-seat').classes()).toContain('active')
    expect(wrapper.get('.hand').attributes('style')).toContain('--hand-count: 2')

    const cards = wrapper.findAll('.playing-card')
    await cards[0]?.trigger('click')
    await cards[1]?.trigger('click')

    expect(cards.every((card) => card.attributes('aria-pressed') === 'true')).toBe(true)
    expect(wrapper.get('.selection-feedback').text()).toContain('对子')
    expect(wrapper.get('.selection-feedback').text()).toContain('已选 2 张')
  })

  it('highlights the opponent whose turn is in progress', () => {
    const next = playingSnapshot()
    next.game.currentPlayerId = 'p2'
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: next },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.opponent.active').text()).toContain('玩家二')
    expect(wrapper.get('.self-hand-header').text()).toContain('等待玩家二')
    expect(wrapper.get('.selection-feedback').text()).toContain('可提前选择手牌')
  })

  it('selects a card and submits its id', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: playingSnapshot() },
      global: { plugins: [pinia] },
    })

    await wrapper.get('.playing-card').trigger('click')
    expect(wrapper.get('.playing-card').classes()).toContain('selected')
    expect(wrapper.get('.play-actions .primary').attributes('disabled')).toBeUndefined()

    await wrapper.get('.play-actions .primary').trigger('click')
    expect(action).toHaveBeenCalledWith('play', { cardIds: ['3-spade'] })
  })

  it('submits call and rob decisions instead of score bids', async () => {
    const bidding = playingSnapshot()
    bidding.phase = 'bidding'
    bidding.game = {
      ...(bidding.game as Record<string, unknown>),
      phase: 'bidding',
      currentPlayerId: 'p1',
      bids: [],
      biddingMode: 'call',
      landlordCandidatePlayerId: null,
      landlordPlayerId: null,
      teams: {},
      hand: [],
    }
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: bidding },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('轮到你叫地主')
    await wrapper.findAll('.bid-panel button').find((button) => button.text() === '叫地主')?.trigger('click')
    expect(action).toHaveBeenCalledWith('bid', { decision: 'call' })

    const robSnapshot = {
      ...bidding,
      revision: bidding.revision + 1,
      game: {
      ...(bidding.game as Record<string, unknown>),
      biddingMode: 'rob',
      landlordCandidatePlayerId: 'p2',
      },
    }
    await wrapper.setProps({ snapshot: robSnapshot })
    expect(wrapper.text()).toContain('是否抢 玩家二 的地主')
    await wrapper.findAll('.bid-panel button').find((button) => button.text().includes('抢地主 ×2'))?.trigger('click')
    expect(action).toHaveBeenLastCalledWith('bid', { decision: 'rob' })
  })

  it('keeps the score-bidding protocol compatible with older rooms', async () => {
    const legacy = playingSnapshot()
    legacy.phase = 'bidding'
    legacy.game = {
      phase: 'bidding',
      currentPlayerId: 'p1',
      bids: [{ seat: 1, score: 1 }],
      highestBid: 1,
      landlordPlayerId: null,
      bottomCards: [],
      hand: [],
      cardCounts: { p1: 17, p2: 17, p3: 17 },
      teams: {},
      lastPlay: null,
      lastPlayPlayerId: null,
    }
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: legacy },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('轮到你叫地主')
    expect(wrapper.text()).toContain('2号 1')
    expect(wrapper.find('.landlord-tools').exists()).toBe(false)

    const twoPoints = wrapper.findAll('.bid-panel button').find((button) => button.text() === '2 分')
    await twoPoints?.trigger('click')
    expect(action).toHaveBeenCalledWith('bid', { score: 2 })
  })
})
