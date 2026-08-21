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
      dealNumber: 1,
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
      revealedHands: {},
      teams: { p1: 'landlord', p2: 'farmer', p3: 'farmer' },
      lastPlay: null,
      lastPlayPlayerId: null,
      multiplier: 1,
      multiplierEvents: [],
      wildRank: null,
      wildLabel: null,
      history: [],
      scores: {},
      settlement: null,
    },
  }
}

function handFromRanks(...ranks: number[]): Array<Record<string, unknown>> {
  const suits = ['spade', 'heart', 'club', 'diamond'] as const
  return ranks.map((rank, index) => ({
    id: `${rank}-${index}`,
    rank,
    label: String(rank),
    suit: suits[index % suits.length],
  }))
}

describe('DoudizhuTable', () => {
  it.each([
    { selfSeat: 0, leftPlayer: '玩家二', rightPlayer: '玩家三' },
    { selfSeat: 1, leftPlayer: '玩家三', rightPlayer: '玩家一' },
    { selfSeat: 2, leftPlayer: '玩家一', rightPlayer: '玩家二' },
  ])('从 $selfSeat 号座位看都按顺时针排列对手', ({ selfSeat, leftPlayer, rightPlayer }) => {
    const next = playingSnapshot()
    next.self = next.players[selfSeat]!
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: next },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.opponent-1').text()).toContain(leftPlayer)
    expect(wrapper.get('.opponent-2').text()).toContain(rightPlayer)
  })

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

  it.each([
    {
      name: '对子拆作单翅膀',
      ranks: [4, 5, 5, 5, 6, 6, 6, 7, 7, 7, 9, 9],
      label: '飞机带单',
    },
    {
      name: '对子拆作四带二',
      ranks: [6, 6, 6, 6, 8, 8],
      label: '四带二',
    },
    {
      name: '双翅膀保持对子结构',
      ranks: [3, 3, 3, 4, 4, 4, 7, 7, 8, 8],
      label: '飞机带对',
    },
  ])('识别$name', async ({ ranks, label }) => {
    const next = playingSnapshot()
    ;(next.game.hand as Array<Record<string, unknown>>) = handFromRanks(...ranks)
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: next },
      global: { plugins: [createPinia()] },
    })

    for (const card of wrapper.findAll('.playing-card')) await card.trigger('click')

    expect(wrapper.get('.selection-feedback').text()).toContain(label)
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

  it('labels DouZero opponents in the playing table', () => {
    const next = playingSnapshot()
    next.players[1] = {
      ...next.players[1]!,
      isBot: true,
      botDifficulty: 'douzero',
    }
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: next },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.opponent-1 .ai-badge').text()).toBe('AI · DouZero')
  })

  it('shows revealed opponent cards and lets the player reveal outside their turn', async () => {
    const next = playingSnapshot()
    next.game.currentPlayerId = 'p2'
    next.game.revealedHands = {
      p2: [
        { id: '7-spade', rank: 7, label: '7', suit: 'spade' },
        { id: '8-heart', rank: 8, label: '8', suit: 'heart' },
      ],
    }
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: next },
      global: { plugins: [pinia] },
    })

    expect(wrapper.findAll('.opponent-1 .revealed-hand .playing-card')).toHaveLength(2)
    expect(wrapper.find('.opponent-1 .opponent-card-stack').exists()).toBe(false)
    await wrapper.get('.reveal-hand-button').trigger('click')

    expect(action).toHaveBeenCalledWith('reveal_hand')
  })

  it('deals the opening hand one card at a time', async () => {
    vi.useFakeTimers()
    const bidding = playingSnapshot()
    bidding.phase = 'bidding'
    bidding.game = {
      ...(bidding.game as Record<string, unknown>),
      phase: 'bidding',
      dealNumber: 1,
      bids: [],
      biddingMode: 'call',
      currentPlayerId: 'p1',
      hand: handFromRanks(...Array.from({ length: 17 }, (_, index) => 3 + (index % 13))),
      cardCounts: { p1: 17, p2: 17, p3: 17 },
      teams: {},
    }
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: bidding },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.hand .playing-card')).toHaveLength(1)
    expect(wrapper.get('.self-hand-status').text()).toContain('正在发牌 1 / 17')
    expect(wrapper.findAll('.card-count').map((count) => count.text())).toEqual(['1张', '1张'])

    await vi.advanceTimersByTimeAsync(16 * 90)

    expect(wrapper.findAll('.hand .playing-card')).toHaveLength(17)
    expect(wrapper.get('.self-hand-status').text()).toContain('请看牌后决定是否叫地主')
    expect(wrapper.findAll('.card-count').map((count) => count.text())).toEqual(['17张', '17张'])
    wrapper.unmount()
    vi.useRealTimers()
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
      hand: [{ id: '3-spade', rank: 3, label: '3', suit: 'spade' }],
    }
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(DoudizhuTable, {
      props: { snapshot: bidding },
      global: { plugins: [pinia] },
    })

    expect(wrapper.text()).toContain('轮到你叫地主')
    expect(wrapper.get('.self-hand-header').text()).toContain('请看牌后决定是否叫地主')
    expect(wrapper.findAll('.playing-card')).toHaveLength(1)
    expect(wrapper.get('.playing-card').attributes('disabled')).toBeDefined()
    expect(wrapper.find('.counter-panel').exists()).toBe(false)
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
})
