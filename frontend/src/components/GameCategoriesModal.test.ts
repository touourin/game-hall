import { mount } from '@vue/test-utils'
import { GAME_CATALOG } from '../gameCatalog'
import GameCategoriesModal from './GameCategoriesModal.vue'

describe('GameCategoriesModal', () => {
  const officialGames = GAME_CATALOG.filter((game) => !game.key.startsWith('plugin-'))

  it('groups every official game by its registered category', async () => {
    const wrapper = mount(GameCategoriesModal, {
      props: { games: officialGames },
    })

    expect(wrapper.get('[role="dialog"]').attributes('aria-label')).toBe('游戏分类')
    expect(wrapper.findAll('.category-section')).toHaveLength(6)
    expect(wrapper.findAll('.category-game-grid > button')).toHaveLength(18)
    expect(wrapper.text()).toContain('棋类竞技')
    expect(wrapper.text()).toContain('5 款游戏')
    expect(wrapper.text()).toContain('个人挑战')
    expect(wrapper.text()).toContain('7 款游戏')

    await wrapper.get('[aria-label="从棋类竞技打开国际象棋"]').trigger('click')
    expect(wrapper.emitted('select')?.[0]?.[0]).toMatchObject({
      key: 'chess',
      category: '棋类竞技',
    })
  })
})
