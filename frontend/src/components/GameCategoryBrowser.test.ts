import { mount } from '@vue/test-utils'
import { GAME_CATALOG } from '../gameCatalog'
import GameCategoryBrowser from './GameCategoryBrowser.vue'

const officialGames = GAME_CATALOG.filter((game) => !game.key.startsWith('plugin-'))

describe('GameCategoryBrowser', () => {
  it('shows category modules before revealing the games in a category', async () => {
    const wrapper = mount(GameCategoryBrowser, {
      props: {
        games: officialGames,
        roomCounts: { go: 2, chess: 1 },
      },
    })

    expect(wrapper.findAll('.game-category-card')).toHaveLength(5)
    expect(wrapper.findAll('.game-library-card')).toHaveLength(0)
    expect(wrapper.get('[aria-label="查看棋类竞技分类"]').text()).toContain('5 款游戏')
    expect(wrapper.get('[aria-label="查看棋类竞技分类"]').text()).toContain('3 个实时房间')

    await wrapper.get('[aria-label="查看棋类竞技分类"]').trigger('click')

    expect(wrapper.findAll('.game-category-card')).toHaveLength(0)
    expect(wrapper.findAll('.game-library-card')).toHaveLength(5)
    expect(wrapper.get('.category-detail-header').text()).toContain('棋类竞技')

    await wrapper.get('[aria-label="打开国际象棋"]').trigger('click')
    expect(wrapper.emitted('select')?.[0]?.[0]).toMatchObject({ key: 'chess' })

    await wrapper.get('[aria-label="返回游戏分类"]').trigger('click')
    expect(wrapper.findAll('.game-category-card')).toHaveLength(5)
    expect(wrapper.findAll('.game-library-card')).toHaveLength(0)
  })

  it('uses wide category artwork instead of presenting category modules as game cards', () => {
    const wrapper = mount(GameCategoryBrowser, {
      props: { games: officialGames, roomCounts: {} },
    })

    expect(wrapper.findAll('.category-card-art')).toHaveLength(5)
    expect(wrapper.findAll('.category-art-tile').length).toBeGreaterThan(5)
    expect(wrapper.find('.category-span-wide').exists()).toBe(true)
    expect(wrapper.find('.category-span-standard').exists()).toBe(true)
  })
})
