import { mount } from '@vue/test-utils'
import { GAME_CATALOG } from '../gameCatalog'
import GameCategoryBrowser from './GameCategoryBrowser.vue'

const communityGames = GAME_CATALOG.filter((game) => game.source === 'third_party')

describe('GameCategoryBrowser', () => {
  it('shows category modules before revealing the games in a category', async () => {
    const wrapper = mount(GameCategoryBrowser, {
      props: {
        games: GAME_CATALOG,
        roomCounts: { go: 2, chess: 1 },
      },
    })

    expect(wrapper.findAll('.game-category-card')).toHaveLength(6)
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
    expect(wrapper.findAll('.game-category-card')).toHaveLength(6)
    expect(wrapper.findAll('.game-library-card')).toHaveLength(0)
  })

  it('uses one dedicated mural for every category instead of composing game artwork', () => {
    const wrapper = mount(GameCategoryBrowser, {
      props: { games: GAME_CATALOG, roomCounts: {} },
    })

    expect(wrapper.findAll('.category-card-art')).toHaveLength(6)
    expect(wrapper.findAll('.category-artwork')).toHaveLength(6)
    expect(wrapper.findAll('.category-art-meta')).toHaveLength(6)
    expect(wrapper.find('.category-art-tile').exists()).toBe(false)
  })

  it('presents community games with the same full-size cards as official games', async () => {
    const wrapper = mount(GameCategoryBrowser, {
      props: { games: GAME_CATALOG, roomCounts: {} },
    })

    await wrapper.get('[aria-label="查看社区游戏分类"]').trigger('click')

    expect(wrapper.findAll('.game-library-card')).toHaveLength(communityGames.length)
    expect(wrapper.find('.game-card-art--compact').exists()).toBe(false)
    if (communityGames.length) {
      expect(wrapper.text()).toContain(communityGames[0]!.name)
    } else {
      expect(wrapper.get('[role="status"]').text()).toContain('社区作品正在准备中')
    }
  })
})
