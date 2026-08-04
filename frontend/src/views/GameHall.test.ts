import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import GameHall from './GameHall.vue'

describe('GameHall', () => {
  it('keeps the existing games outside the separate board-game collection', async () => {
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
    expect(gameCards).toHaveLength(11)
    expect(wrapper.findAll('.arcade-section .game-card')).toHaveLength(7)
    expect(wrapper.findAll('.solo-section .game-card')).toHaveLength(4)
    expect(wrapper.findAll('.board-plugin-slot')).toHaveLength(3)
    expect(wrapper.findAll('.game-card-art')).toHaveLength(11)
    expect(wrapper.find('.avalon-card-art-emerald').exists()).toBe(true)
    expect(wrapper.find('.avalon-card-art-midnight').exists()).toBe(true)
    expect(wrapper.find('.avalon-card-art-royal').exists()).toBe(true)
    expect(wrapper.find('.mobile-salon-dock').exists()).toBe(false)
    expect(wrapper.findAll('.account-bar-actions button')).toHaveLength(3)
    expect(wrapper.get('.account-bar-actions [aria-label="查看全部战绩"]').text()).toContain('全部战绩')
    expect(wrapper.get('[aria-label="退出登录"]').text()).toContain('退出')
    expect(wrapper.get('[aria-label="打开设置"]').attributes('aria-label')).toBe('打开设置')
    await wrapper.get('.account-bar-actions [aria-label="打开设置"]').trigger('click')
    expect(wrapper.emitted('settings')).toHaveLength(1)
    expect(wrapper.get('.account-identity-copy').text()).toContain('玩家账号 · tester')
    expect(wrapper.get('.hall-highlights').text()).toBe('实时联机·独立战绩')
    expect(wrapper.text()).not.toContain('PRIVATE')
    expect(wrapper.text()).not.toContain('私人席位')
    expect(wrapper.text()).toContain('桌游合集')
    expect(wrapper.text()).toContain('等待桌游插件')
    expect(wrapper.text()).toContain('独立于现有游戏的桌游插件空间')
    expect(wrapper.text()).toContain('现有 7 款游戏，保持原有入口')
    expect(wrapper.get('.board-game-collection-card').text()).not.toContain('阿瓦隆')
    expect(wrapper.get('.board-game-collection-card').text()).not.toContain('五子棋')
    expect(wrapper.text()).toContain('军旗')
    expect(wrapper.text()).toContain('秘密布阵，沿铁路突袭敌旗')
    expect(wrapper.text()).toContain('反应挑战')
    expect(wrapper.text()).toContain('舒尔特方格')
    expect(wrapper.text()).toContain('扫雷')
    expect(wrapper.text()).toContain('汉诺塔')

    await wrapper.get('.board-game-collection-card').trigger('click')
    expect(wrapper.emitted('openBoardGames')).toHaveLength(1)

    const minesweeper = gameCards.find((card) => card.text().includes('扫雷'))
    expect(minesweeper).toBeDefined()
    await minesweeper!.trigger('click')

    expect(wrapper.emitted('select')?.[0]?.[0]).toMatchObject({
      key: 'minesweeper',
      name: '扫雷',
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
    expect(wrapper.find('.mobile-salon-dock').exists()).toBe(false)
    expect(wrapper.find('[aria-label="打开设置"]').exists()).toBe(true)
  })
})
