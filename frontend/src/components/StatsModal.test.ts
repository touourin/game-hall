import { flushPromises, mount } from '@vue/test-utils'
import { loadMatchDetail, loadPersonalStats } from '../stats'
import StatsModal from './StatsModal.vue'

vi.mock('../stats', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../stats')>()
  return {
    ...actual,
    loadMatchDetail: vi.fn(),
    loadPersonalStats: vi.fn(),
  }
})

describe('StatsModal', () => {
  it('renders a gomoku draw as a draw in history and match details', async () => {
    vi.mocked(loadPersonalStats).mockResolvedValue({
      summary: {
        games: 1,
        wins: 0,
        draws: 1,
        losses: 0,
        winRate: 0,
        goodGames: 0,
        goodWins: 0,
        evilGames: 0,
        evilWins: 0,
        bestMs: null,
        averageMs: null,
      },
      history: [
        {
          id: 'gomoku-draw',
          gameKey: 'gomoku',
          gameName: '五子棋',
          roomCode: 'DRAW',
          playerCount: 2,
          winner: 'draw',
          reason: '棋盘已满，双方和棋',
          ranked: true,
          assassinationHit: null,
          endedAt: '2026-08-01T00:10:00+00:00',
          playerName: '棋手一',
          role: 'black',
          alignment: 'black',
          won: false,
          outcome: 'draw',
          scoreMs: null,
        },
      ],
    })
    vi.mocked(loadMatchDetail).mockResolvedValue({
      id: 'gomoku-draw',
      gameKey: 'gomoku',
      gameName: '五子棋',
      roomCode: 'DRAW',
      playerCount: 2,
      winner: 'draw',
      reason: '棋盘已满，双方和棋',
      ranked: true,
      assassinationHit: null,
      startedAt: '2026-08-01T00:00:00+00:00',
      endedAt: '2026-08-01T00:10:00+00:00',
      details: { players: [] },
    })

    const wrapper = mount(StatsModal, {
      props: { gameKey: 'gomoku', gameName: '五子棋' },
    })
    await flushPromises()

    expect(wrapper.get('.match-outcome').classes()).toContain('draw')
    expect(wrapper.get('.match-outcome').text()).toBe('和')
    expect(wrapper.get('.match-result-summary').text()).toContain('和 1')
    expect(wrapper.get('.match-result-summary').text()).toContain('负 0')

    await wrapper.get('.match-history-list button').trigger('click')
    await flushPromises()

    expect(wrapper.get('.match-detail-result').classes()).toContain('draw')
    expect(wrapper.get('.match-detail-result strong').text()).toBe('双方和棋')
  })
})
