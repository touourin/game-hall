import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { THIRD_PARTY_GAME_PLUGINS } from '../thirdPartyGameRegistry'
import { useArcadeStore } from '../stores/arcade'
import GameHall from './GameHall.vue'

describe('GameHall', () => {
  it('shows thirteen games and selects the requested game', async () => {
    const wrapper = mount(GameHall, {
      props: {
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          nextRenameAt: null,
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [createPinia()] },
    })

    const gameCards = wrapper.findAll('.game-card')
    expect(gameCards).toHaveLength(13)
    expect(wrapper.findAll('.nexus-game-module .game-card-art')).toHaveLength(13)
    expect(wrapper.find('.art-avalon img').attributes('src')).toContain('avalon')
    expect(wrapper.find('.nexus-feature').exists()).toBe(true)
    expect(wrapper.find('.nexus-feature .art-avalon').exists()).toBe(true)
    expect(wrapper.find('.nexus-live-rooms').exists()).toBe(true)
    expect(wrapper.find('.nexus-mobile-dock').exists()).toBe(true)
    expect(wrapper.findAll('.account-bar-actions button')).toHaveLength(3)
    expect(wrapper.get('.account-bar-actions [aria-label="查看全部战绩"]').text()).toContain('全部战绩')
    expect(wrapper.get('[aria-label="退出登录"]').text()).toContain('退出')
    expect(wrapper.get('[aria-label="打开设置"]').attributes('aria-label')).toBe('打开设置')
    expect(wrapper.get('[aria-label="打开第三方游戏入口"]').text()).toContain('第三方游戏')
    expect(wrapper.get('[aria-label="打开第三方游戏入口"]').text()).toContain(
      `${THIRD_PARTY_GAME_PLUGINS.length} 款已启用`,
    )
    await wrapper.get('.account-bar-actions [aria-label="打开设置"]').trigger('click')
    expect(wrapper.emitted('settings')).toHaveLength(1)
    await wrapper.get('[aria-label="打开第三方游戏入口"]').trigger('click')
    expect(wrapper.find('[role="dialog"][aria-label="第三方游戏"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('数字密匣')
    expect(wrapper.text()).toContain('星石争夺')
    await wrapper.get('[aria-label="关闭第三方游戏"]').trigger('click')
    expect(wrapper.find('[role="dialog"][aria-label="第三方游戏"]').exists()).toBe(false)
    expect(wrapper.get('.account-identity-copy').text()).toContain('玩家账号 · tester')
    expect(wrapper.get('.nexus-title-block').text()).toContain('竞技大厅')
    expect(wrapper.get('.nexus-system-metrics').text()).toContain('0 ROOMS')
    expect(wrapper.text()).not.toContain('PRIVATE')
    expect(wrapper.text()).not.toContain('私人席位')
    expect(wrapper.text()).not.toContain('11 款游戏')
    expect(wrapper.text()).not.toContain('本周主桌')
    expect(wrapper.text()).toContain('军旗')
    expect(wrapper.text()).toContain('秘密布阵，沿铁路突袭敌旗')
    expect(wrapper.text()).not.toContain('Swap2')
    expect(wrapper.text()).toContain('反应挑战')
    expect(wrapper.text()).toContain('舒尔特方格')
    expect(wrapper.text()).toContain('扫雷')
    expect(wrapper.text()).toContain('汉诺塔')
    expect(wrapper.text()).toContain('大富翁')
    expect(wrapper.text()).toContain('无间疑云')
    expect(gameCards.findIndex((card) => card.text().includes('德州扑克'))).toBeLessThan(
      gameCards.findIndex((card) => card.text().includes('斗地主')),
    )
    const gomoku = gameCards.find((card) => card.text().includes('五子棋'))
    expect(gomoku).toBeDefined()
    await gomoku!.trigger('click')

    expect(wrapper.emitted('select')?.[0]?.[0]).toMatchObject({
      key: 'gomoku',
      name: '五子棋',
    })
  })

  it('shows a guest seat without personal-record actions', () => {
    const wrapper = mount(GameHall, {
      props: {
        account: {
          id: 'guest:1',
          username: '',
          playerName: '临时骑士',
          nextRenameAt: null,
          createdAt: '2026-08-02T00:00:00Z',
          isGuest: true,
        },
      },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('游客席位 · 对局不计战绩')
    expect(wrapper.find('[aria-label="查看全部战绩"]').exists()).toBe(false)
    expect(wrapper.find('[aria-label="退出游客模式"]').exists()).toBe(true)
    expect(wrapper.find('.nexus-mobile-dock').exists()).toBe(true)
    expect(wrapper.find('[aria-label="打开设置"]').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('好友')
  })

  it('uses the real lobby signal and opens the selected live room', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    arcade.availableRooms = [{
      roomCode: 'NX42',
      roomName: '冠军桌',
      gameKey: 'avalon',
      gameName: '阿瓦隆',
      hostName: '测试房主',
      playerCount: 6,
      maxPlayers: 10,
      options: {},
      phase: 'lobby',
    }]
    const wrapper = mount(GameHall, {
      props: {
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          nextRenameAt: null,
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.nexus-system-metrics').text()).toContain('6 ONLINE')
    expect(wrapper.get('.nexus-feature-copy').text()).toContain('冠军桌')
    await wrapper.get('.nexus-room-row').trigger('click')
    expect(wrapper.emitted('openRoom')?.[0]?.[0]).toEqual({
      gameKey: 'avalon',
      roomCode: 'NX42',
    })
  })
})
