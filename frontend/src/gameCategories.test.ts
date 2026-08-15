import { GAME_CATALOG } from './gameCatalog'
import { buildOfficialGameCategories } from './gameCategories'

const officialGames = GAME_CATALOG.filter((game) => game.source === 'official')

describe('official game categories', () => {
  it('assigns every official game to exactly one product category', () => {
    const categories = buildOfficialGameCategories(officialGames)
    const categorizedKeys = categories.flatMap((category) => (
      category.games.map((game) => game.key)
    ))

    expect(categories.map((category) => category.name)).toEqual([
      '棋类竞技',
      '推理社交',
      '扑克牌类',
      '单人挑战',
      '多人派对',
    ])
    expect(categories.map((category) => category.games.length)).toEqual([5, 3, 2, 7, 2])
    expect(new Set(categorizedKeys).size).toBe(officialGames.length)
    expect(categorizedKeys).toHaveLength(officialGames.length)
  })

  it('fails loudly when a newly registered game has not been classified', () => {
    const unclassifiedGame = GAME_CATALOG.find((game) => game.source === 'third_party')!

    expect(() => buildOfficialGameCategories([
      ...officialGames,
      unclassifiedGame,
    ])).toThrow(`官方游戏尚未分类：${unclassifiedGame.key}`)
  })
})
