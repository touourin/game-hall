import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { COMMUNITY_GAME_REGISTRATIONS } from '../communityGameRegistry'
import { useArcadeStore } from '../stores/arcade'
import GameHall from './GameHall.vue'

describe('GameHall', () => {
  it('shows category modules before selecting a game from a category', async () => {
    const wrapper = mount(GameHall, {
      props: {
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.game-category-card')).toHaveLength(6)
    expect(wrapper.findAll('.game-library-card')).toHaveLength(0)
    expect(wrapper.findAll('.category-card-art')).toHaveLength(6)
    expect(wrapper.find('.hall-hub').exists()).toBe(true)
    expect(wrapper.find('.hall-hub .art-go').exists()).toBe(true)
    expect(wrapper.find('.lobby-room-panel').exists()).toBe(true)
    expect(wrapper.find('.hall-mobile-dock').exists()).toBe(true)
    expect(wrapper.find('[aria-label="查看游戏分类"]').exists()).toBe(true)
    expect(wrapper.find('[aria-label="手机端：游戏分类"]').exists()).toBe(true)
    expect(wrapper.findAll('.account-bar-actions button')).toHaveLength(3)
    expect(wrapper.get('.account-bar-actions [aria-label="查看全部战绩"]').text()).toContain('全部战绩')
    expect(wrapper.get('[aria-label="退出登录"]').text()).toContain('退出')
    expect(wrapper.get('[aria-label="打开设置"]').attributes('aria-label')).toBe('打开设置')
    expect(wrapper.get('[aria-label="查看社区游戏分类"]').text()).toContain('社区游戏')
    expect(wrapper.get('[aria-label="查看社区游戏分类"]').text()).toContain(
      `${COMMUNITY_GAME_REGISTRATIONS.length} 款游戏`,
    )
    await wrapper.get('.account-bar-actions [aria-label="打开设置"]').trigger('click')
    expect(wrapper.emitted('settings')).toHaveLength(1)
    await wrapper.get('[aria-label="查看社区游戏分类"]').trigger('click')
    expect(wrapper.findAll('.game-library-card')).toHaveLength(COMMUNITY_GAME_REGISTRATIONS.length)
    for (const registration of COMMUNITY_GAME_REGISTRATIONS) {
      expect(wrapper.text()).toContain(registration.catalog.name)
    }
    if (!COMMUNITY_GAME_REGISTRATIONS.length) {
      expect(wrapper.get('[role="status"]').text()).toContain('社区作品正在准备中')
    }
    await wrapper.get('[aria-label="返回游戏分类"]').trigger('click')
    expect(wrapper.get('.account-identity-copy').text()).toContain('玩家账号 · tester')
    expect(wrapper.get('.hall-title-block').text()).toContain('竞技大厅')
    expect(wrapper.get('.hall-system-metrics').text()).toContain('0 个房间')
    expect(wrapper.text()).toContain('选择游戏分类')
    expect(wrapper.text()).not.toContain('全部游戏')
    expect(wrapper.text()).not.toContain('PRIVATE')
    expect(wrapper.text()).not.toContain('私人席位')
    expect(wrapper.text()).not.toContain('11 款游戏')
    expect(wrapper.text()).not.toContain('本周主桌')
    expect(wrapper.text()).not.toContain('快速启动')
    expect(wrapper.text()).not.toContain('Swap2')

    await wrapper.get('[aria-label="查看棋类竞技分类"]').trigger('click')
    const gameCards = wrapper.findAll('.game-library-card')
    expect(gameCards).toHaveLength(5)
    expect(wrapper.text()).toContain('军旗')
    expect(wrapper.text()).toContain('国际象棋')
    expect(wrapper.find('.art-chess img').attributes('src')).toContain('chess')
    expect(wrapper.text()).toContain('秘密布阵，沿铁路突袭敌旗')

    await wrapper.get('[aria-label="查看游戏分类"]').trigger('click')
    expect(wrapper.findAll('.game-category-card')).toHaveLength(6)
    expect(wrapper.findAll('.game-library-card')).toHaveLength(0)
    await wrapper.get('[aria-label="查看棋类竞技分类"]').trigger('click')

    const gomoku = wrapper.findAll('.game-library-card').find(
      (card) => card.text().includes('五子棋'),
    )
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
          createdAt: '2026-08-02T00:00:00Z',
          isGuest: true,
        },
      },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.text()).toContain('游客席位 · 对局不计战绩')
    expect(wrapper.find('[aria-label="查看全部战绩"]').exists()).toBe(false)
    expect(wrapper.find('[aria-label="退出游客模式"]').exists()).toBe(true)
    expect(wrapper.find('.hall-mobile-dock').exists()).toBe(true)
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
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.hall-system-metrics').text()).toContain('6 位玩家')
    expect(wrapper.get('.hall-hub-copy').text()).toContain('冠军桌')
    await wrapper.get('.lobby-room-row').trigger('click')
    expect(wrapper.emitted('openRoom')?.[0]?.[0]).toEqual({
      gameKey: 'avalon',
      roomCode: 'NX42',
    })
  })
})
