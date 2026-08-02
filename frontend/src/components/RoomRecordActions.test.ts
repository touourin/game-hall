import { shallowMount } from '@vue/test-utils'
import LeaderboardModal from './LeaderboardModal.vue'
import RoomRecordActions from './RoomRecordActions.vue'
import StatsModal from './StatsModal.vue'

describe('RoomRecordActions', () => {
  it('opens and closes the shared stats and leaderboard modals', async () => {
    const wrapper = shallowMount(RoomRecordActions, {
      props: {
        accountId: 'account-1',
        gameKey: 'avalon',
        gameName: '阿瓦隆',
      },
    })

    await wrapper.get('[aria-label="查看我的战绩"]').trigger('click')
    expect(wrapper.getComponent(StatsModal).props()).toMatchObject({
      gameKey: 'avalon',
      gameName: '阿瓦隆',
    })
    await wrapper.getComponent(StatsModal).vm.$emit('close')
    expect(wrapper.findComponent(StatsModal).exists()).toBe(false)

    await wrapper.get('[aria-label="查看排行榜"]').trigger('click')
    expect(wrapper.getComponent(LeaderboardModal).props()).toMatchObject({
      accountId: 'account-1',
      gameKey: 'avalon',
      gameName: '阿瓦隆',
    })
    await wrapper.getComponent(LeaderboardModal).vm.$emit('close')
    expect(wrapper.findComponent(LeaderboardModal).exists()).toBe(false)
  })

  it('lets guests view the leaderboard without exposing personal stats', () => {
    const wrapper = shallowMount(RoomRecordActions, {
      props: {
        accountId: 'guest:1',
        gameKey: 'gomoku',
        gameName: '五子棋',
        guest: true,
      },
    })

    expect(wrapper.find('[aria-label="查看我的战绩"]').exists()).toBe(false)
    expect(wrapper.find('[aria-label="查看排行榜"]').exists()).toBe(true)
  })
})
