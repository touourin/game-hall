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
  it('separates classic and Shadow Merlin court-undercurrent rankings', async () => {
    vi.mocked(loadLeaderboard).mockResolvedValue([])

    const wrapper = mount(LeaderboardModal, {
      props: {
        accountId: 'account-1',
        gameKey: 'avalon',
        gameName: '阿瓦隆',
      },
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
})
