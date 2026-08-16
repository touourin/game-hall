import { flushPromises, mount } from '@vue/test-utils'
import { loadLeaderboard } from '../stats'
import LeaderboardModal from './LeaderboardModal.vue'

vi.mock('../stats', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../stats')>()
  return {
    ...actual,
    loadLeaderboard: vi.fn(),
  }
})

describe('LeaderboardModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('teleports the room leaderboard outside layout containers', async () => {
    vi.mocked(loadLeaderboard).mockResolvedValue([])
    const roomLayout = document.createElement('main')
    roomLayout.className = 'adaptive-layout-root'
    document.body.append(roomLayout)

    const wrapper = mount(LeaderboardModal, {
      attachTo: roomLayout,
      props: {
        accountId: 'account-1',
        gameKey: 'tetris',
        gameName: '落块挑战',
        gameMode: 'timed_180',
      },
    })
    await flushPromises()

    const backdrop = document.body.querySelector('.base-modal-backdrop')
    expect(backdrop?.parentElement).toBe(document.body)
    expect(roomLayout.querySelector('.base-modal-backdrop')).toBeNull()

    wrapper.unmount()
    roomLayout.remove()
  })

  it('separates classic and Shadow Merlin court-undercurrent rankings', async () => {
    vi.mocked(loadLeaderboard).mockResolvedValue([])

    const wrapper = mount(LeaderboardModal, {
      props: {
        accountId: 'account-1',
        gameKey: 'avalon',
        gameName: '阿瓦隆',
      },
      global: { stubs: { teleport: true } },
    })
    await flushPromises()

    expect(loadLeaderboard).toHaveBeenCalledWith(
      'avalon',
      'standard',
      undefined,
    )

    await wrapper.findAll('.stats-mode-tabs button')[1]!.trigger('click')
    await flushPromises()
    expect(loadLeaderboard).toHaveBeenLastCalledWith(
      'avalon',
      'court_undercurrent',
      'classic',
    )

    await wrapper.findAll('.stats-mode-tabs button')[2]!.trigger('click')
    await flushPromises()
    expect(loadLeaderboard).toHaveBeenLastCalledWith(
      'avalon',
      'court_undercurrent',
      'shadow_merlin',
    )
    expect(wrapper.get('h2').text()).toContain('暗影梅林')
  })

  it('loads the selected Tetris duration leaderboard', async () => {
    vi.mocked(loadLeaderboard).mockResolvedValue([])

    const wrapper = mount(LeaderboardModal, {
      props: {
        accountId: 'account-1',
        gameKey: 'tetris',
        gameName: '落块挑战',
        gameMode: 'timed_180',
      },
      global: { stubs: { teleport: true } },
    })
    await flushPromises()

    expect(loadLeaderboard).toHaveBeenCalledWith('tetris', 'timed_180', undefined)
    expect(wrapper.get('h2').text()).toContain('3 分钟限时')
    expect(wrapper.findAll('.stats-mode-tabs button')).toHaveLength(4)

    await wrapper.findAll('.stats-mode-tabs button')[0]!.trigger('click')
    await flushPromises()
    expect(loadLeaderboard).toHaveBeenLastCalledWith('tetris', 'timed_60', undefined)
  })

  it('locks mode filters when opened from an existing room', async () => {
    vi.mocked(loadLeaderboard).mockResolvedValue([])

    const wrapper = mount(LeaderboardModal, {
      props: {
        accountId: 'account-1',
        gameKey: 'tetris',
        gameName: '落块挑战',
        gameMode: 'timed_300',
        fixedGameMode: true,
      },
      global: { stubs: { teleport: true } },
    })
    await flushPromises()

    expect(wrapper.find('.stats-mode-tabs').exists()).toBe(false)
    expect(wrapper.get('h2').text()).toContain('5 分钟限时')
  })

  it('renders missing score data safely', async () => {
    vi.mocked(loadLeaderboard).mockResolvedValue([{
      rank: 1,
      accountId: 'account-1',
      playerName: '玩家一号',
      games: 1,
      wins: 0,
      draws: 0,
      winRate: 0,
      bestMs: null,
      averageMs: null,
      bestScore: null,
      averageScore: null,
    }])

    const wrapper = mount(LeaderboardModal, {
      props: {
        accountId: 'account-1',
        gameKey: 'tetris',
        gameName: '落块挑战',
        gameMode: 'timed_180',
      },
      global: { stubs: { teleport: true } },
    })
    await flushPromises()

    expect(wrapper.get('.leaderboard-list').text()).toContain('平均 —')
    expect(wrapper.get('.leaderboard-list em').text()).toBe('—')
    expect(wrapper.text()).not.toContain('undefined')
    expect(wrapper.text()).not.toContain('NaN')
  })

  it('ignores a stale response after switching modes', async () => {
    type Entry = Awaited<ReturnType<typeof loadLeaderboard>>[number]
    let resolveInitial!: (entries: Entry[]) => void
    let resolveLatest!: (entries: Entry[]) => void
    const initial = new Promise<Entry[]>((resolve) => { resolveInitial = resolve })
    const latest = new Promise<Entry[]>((resolve) => { resolveLatest = resolve })
    vi.mocked(loadLeaderboard)
      .mockImplementationOnce(() => initial)
      .mockImplementationOnce(() => latest)

    const wrapper = mount(LeaderboardModal, {
      props: {
        accountId: 'account-1',
        gameKey: 'tetris',
        gameName: '落块挑战',
        gameMode: 'timed_180',
      },
      global: { stubs: { teleport: true } },
    })
    await wrapper.findAll('.stats-mode-tabs button')[0]!.trigger('click')

    const entry = (playerName: string, score: number): Entry => ({
      rank: 1,
      accountId: playerName,
      playerName,
      games: 1,
      wins: 0,
      draws: 0,
      winRate: 0,
      bestMs: null,
      averageMs: null,
      bestScore: score,
      averageScore: score,
    })
    resolveLatest([entry('新榜单', 20_000)])
    await flushPromises()
    expect(wrapper.text()).toContain('新榜单')

    resolveInitial([entry('旧榜单', 10_000)])
    await flushPromises()
    expect(wrapper.text()).toContain('新榜单')
    expect(wrapper.text()).not.toContain('旧榜单')
  })

  it('shows a load error instead of an empty leaderboard', async () => {
    vi.mocked(loadLeaderboard).mockRejectedValue(new Error('排行榜服务暂时不可用'))

    const wrapper = mount(LeaderboardModal, {
      props: {
        accountId: 'account-1',
        gameKey: 'tetris',
        gameName: '落块挑战',
        gameMode: 'timed_180',
      },
      global: { stubs: { teleport: true } },
    })
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('排行榜服务暂时不可用')
    expect(wrapper.find('.stats-empty').exists()).toBe(false)
  })
})
