import { mount } from '@vue/test-utils'
import GameCardArtwork from './GameCardArtwork.vue'
import ThirdPartyGamesModal from './ThirdPartyGamesModal.vue'
import type { GameCatalogItem } from '../types/arcade'

const pluginGame: GameCatalogItem = {
  key: 'plugin-counter-demo',
  name: '计数挑战',
  players: '1–4 人',
  description: '第三方插件示例',
}

describe('ThirdPartyGamesModal', () => {
  it('shows enabled plugin games and selects one', async () => {
    const wrapper = mount(ThirdPartyGamesModal, {
      props: { games: [pluginGame] },
    })

    expect(wrapper.text()).toContain('计数挑战')
    expect(wrapper.text()).toContain('1–4 人')
    expect(wrapper.getComponent(GameCardArtwork).props()).toMatchObject({
      gameKey: 'plugin-counter-demo',
      compact: true,
    })
    await wrapper.get('.third-party-game-option').trigger('click')

    expect(wrapper.emitted('select')?.[0]?.[0]).toEqual(pluginGame)
  })

  it('shows an empty state and can close', async () => {
    const wrapper = mount(ThirdPartyGamesModal, {
      props: { games: [] },
    })

    expect(wrapper.get('[role="status"]').text()).toContain('暂未启用第三方游戏')
    await wrapper.get('[aria-label="关闭第三方游戏"]').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })
})
