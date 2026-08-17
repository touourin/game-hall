import { GAME_CATALOG } from './gameCatalog'
import { buildGameCategories } from './gameCategories'

const officialGames = GAME_CATALOG.filter((game) => game.source === 'official')
const communityGames = GAME_CATALOG.filter((game) => game.source === 'community')

describe('game categories', () => {
  it('assigns every published game to exactly one product category', () => {
    const categories = buildGameCategories(GAME_CATALOG)
    const categorizedKeys = categories.flatMap((category) => (
      category.games.map((game) => game.key)
    ))

    expect(categories.map((category) => category.name)).toEqual([
      '棋类竞技',
      '推理社交',
      '扑克牌类',
      '单人挑战',
      '多人派对',
      '社区游戏',
    ])
    expect(categories.map((category) => category.games.length)).toEqual([
      5,
      3,
      2,
      7,
      2,
      communityGames.length,
    ])
    expect(new Set(categorizedKeys).size).toBe(GAME_CATALOG.length)
    expect(categorizedKeys).toHaveLength(GAME_CATALOG.length)
  })

  it('automatically places newly registered community games in the community category', () => {
    const pluginGame = {
      ...officialGames[0]!,
      key: 'plugin-new-community-game' as const,
      source: 'community' as const,
    }

    const community = buildGameCategories([
      ...officialGames,
      pluginGame,
    ]).find((category) => category.id === 'community')

    expect(community?.games).toEqual([pluginGame])
  })

  it('fails loudly when a newly registered game has not been classified', () => {
    const unclassifiedGame = {
      ...officialGames[0]!,
      key: 'plugin-unclassified-game' as const,
    }

    expect(() => buildGameCategories([
      ...officialGames,
      unclassifiedGame,
    ])).toThrow(`官方游戏尚未分类：${unclassifiedGame.key}`)
  })
})
