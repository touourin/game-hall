import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import GameHall from './GameHall.vue'

describe('GameHall', () => {
  it('shows eleven games and selects the requested game', async () => {
    const wrapper = mount(GameHall, {
      props: {
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          nextRenameAt: null,
          createdAt: '2026-08-01T00:00:00Z',
        },
        busy: false,
        error: null,
      },
      global: { plugins: [createPinia()] },
    })

    const gameCards = wrapper.findAll('.game-card')
    expect(gameCards).toHaveLength(11)
    expect(wrapper.text()).toContain('军旗')
    expect(wrapper.text()).toContain('反应挑战')
    expect(wrapper.text()).toContain('舒尔特方格')
    expect(wrapper.text()).toContain('扫雷')
    expect(wrapper.text()).toContain('汉诺塔')
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
})
