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
  beforeEach(() => {
    vi.clearAllMocks()
  })

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
      details: {
        players: [
          { id: 'black', name: '棋手一', seat: 0, role: 'black', alignment: 'black' },
        ],
      },
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
    expect(wrapper.get('.match-player-list').text()).toContain('黑方')
    expect(wrapper.get('.stats-back').attributes('aria-label')).toBe(
      '返回战绩列表',
    )
    await wrapper.get('.stats-back').trigger('click')
    expect(wrapper.find('.match-history-list').exists()).toBe(true)
  })

  it('separates Avalon modes and replays the full court-undercurrent ending', async () => {
    vi.mocked(loadPersonalStats).mockResolvedValue({
      summary: {
        games: 1,
        wins: 1,
        draws: 0,
        losses: 0,
        winRate: 100,
        goodGames: 0,
        goodWins: 0,
        evilGames: 1,
        evilWins: 1,
        bestMs: null,
        averageMs: null,
        missionRouteGames: 0,
        recruitmentAttempts: 1,
        recruitmentHits: 1,
        dissentingAssassinationAttempts: 1,
        dissentingAssassinationHits: 1,
      },
      history: [
        {
          id: 'court-1',
          gameKey: 'avalon',
          gameName: '阿瓦隆',
          roomCode: 'DARK',
          playerCount: 5,
          winner: 'evil',
          reason: '心怀异念之臣成功刺杀了梅林',
          ranked: true,
          assassinationHit: true,
          endedAt: '2026-08-01T00:10:00+00:00',
          playerName: '异念玩家',
          role: 'dissenting_courtier',
          alignment: 'evil',
          won: true,
          outcome: 'win',
          scoreMs: null,
          gameMode: 'court_undercurrent',
        },
      ],
    })
    vi.mocked(loadMatchDetail).mockResolvedValue({
      id: 'court-1',
      gameKey: 'avalon',
      gameName: '阿瓦隆',
      roomCode: 'DARK',
      gameMode: 'court_undercurrent',
      playerCount: 5,
      winner: 'evil',
      reason: '心怀异念之臣成功刺杀了梅林',
      ranked: true,
      assassinationHit: true,
      recruitmentHit: true,
      endingRoute: 'dissenting_assassination',
      startedAt: '2026-08-01T00:00:00+00:00',
      endedAt: '2026-08-01T00:10:00+00:00',
      details: {
        mode: 'court_undercurrent',
        players: [
          { id: 'p1', name: '刺客玩家', seat: 0, role: 'assassin', alignment: 'evil' },
          {
            id: 'p2',
            name: '异念玩家',
            seat: 1,
            role: 'dissenting_courtier',
            alignment: 'evil',
            initialAlignment: 'good',
            finalAlignment: 'evil',
            transformed: true,
          },
          { id: 'p3', name: '梅林玩家', seat: 2, role: 'merlin', alignment: 'good' },
        ],
        courtUndercurrent: {
          daggerCandidateIds: ['p2', 'p3'],
          daggerTargetId: 'p2',
          daggerHit: true,
          transformedPlayerId: 'p2',
          eligibleTargetIds: ['p3'],
          assassinationTargetId: 'p3',
        },
      },
    })

    const wrapper = mount(StatsModal, {
      props: { gameKey: 'avalon', gameName: '阿瓦隆' },
    })
    await flushPromises()

    expect(loadPersonalStats).toHaveBeenCalledWith(
      'avalon',
      'standard',
      undefined,
    )
    await wrapper.findAll('.stats-mode-tabs button')[1]!.trigger('click')
    await flushPromises()
    expect(loadPersonalStats).toHaveBeenLastCalledWith(
      'avalon',
      'court_undercurrent',
      'classic',
    )
    expect(wrapper.get('.court-balance-summary').text()).toContain('授刃命中')

    await wrapper.findAll('.stats-mode-tabs button')[2]!.trigger('click')
    await flushPromises()
    expect(loadPersonalStats).toHaveBeenLastCalledWith(
      'avalon',
      'court_undercurrent',
      'shadow_merlin',
    )
    expect(wrapper.get('h2').text()).toContain('暗影梅林')

    await wrapper.get('.match-history-list button').trigger('click')
    await flushPromises()

    await vi.waitFor(() => {
      expect(wrapper.find('.match-court-timeline').exists()).toBe(true)
    })

    expect(wrapper.get('.match-mode-label').text()).toContain('王庭暗流')
    expect(wrapper.get('.match-court-timeline').text()).toContain('授刃成功')
    expect(wrapper.get('.match-court-timeline').text()).toContain('命中梅林')
    expect(wrapper.get('.match-player-list').text()).toContain('已转化')
  })

  it('loads Tetris history for the selected timed mode', async () => {
    vi.mocked(loadPersonalStats).mockResolvedValue({
      summary: {
        games: 0,
        wins: 0,
        draws: 0,
        losses: 0,
        winRate: 0,
        goodGames: 0,
        goodWins: 0,
        evilGames: 0,
        evilWins: 0,
        bestMs: null,
        averageMs: null,
        bestScore: null,
        averageScore: null,
      },
      history: [],
    })

    const wrapper = mount(StatsModal, {
      props: {
        gameKey: 'tetris',
        gameName: '落块挑战',
        gameMode: 'timed_300',
      },
    })
    await flushPromises()

    expect(loadPersonalStats).toHaveBeenCalledWith('tetris', 'timed_300', undefined)
    expect(wrapper.get('h2').text()).toContain('5 分钟限时')
    expect(wrapper.findAll('.stats-mode-tabs button')).toHaveLength(4)

    await wrapper.findAll('.stats-mode-tabs button')[3]!.trigger('click')
    await flushPromises()
    expect(loadPersonalStats).toHaveBeenLastCalledWith('tetris', 'standard', undefined)
    expect(wrapper.get('h2').text()).toContain('无限挑战')
  })

  it('formats mixed all-game history with each record module', async () => {
    vi.mocked(loadPersonalStats).mockResolvedValue({
      summary: {
        games: 2,
        wins: 1,
        draws: 0,
        losses: 1,
        winRate: 50,
        goodGames: 0,
        goodWins: 0,
        evilGames: 0,
        evilWins: 0,
        bestMs: null,
        averageMs: null,
      },
      history: [
        {
          id: 'reaction-1',
          gameKey: 'reaction',
          gameName: '反应挑战',
          roomCode: 'FAST',
          playerCount: 1,
          winner: 'completed',
          reason: '测试完成',
          ranked: true,
          assassinationHit: null,
          endedAt: '2026-08-01T00:10:00+00:00',
          playerName: '玩家',
          role: 'tester',
          alignment: 'solo',
          won: true,
          outcome: 'completed',
          scoreMs: 284,
        },
        {
          id: 'tetris-1',
          gameKey: 'tetris',
          gameName: '落块挑战',
          roomCode: 'DROP',
          playerCount: 1,
          winner: 'completed',
          reason: '无限模式结束',
          ranked: true,
          assassinationHit: null,
          endedAt: '2026-08-01T00:20:00+00:00',
          playerName: '玩家',
          role: 'stacker',
          alignment: 'solo',
          won: true,
          outcome: 'completed',
          scoreMs: null,
          scoreValue: 18_600,
        },
      ],
    })

    const wrapper = mount(StatsModal)
    await flushPromises()

    const entries = wrapper.findAll('.match-history-list button')
    expect(entries[0]!.text()).toContain('三轮平均 · 284 ms')
    expect(entries[1]!.text()).toContain('最终得分 · 18,600 分')
  })
})
