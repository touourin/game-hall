import { mount } from '@vue/test-utils'
import type { BuiltinArcadeGameKey } from '../types/arcade'
import GameCardArtwork from './GameCardArtwork.vue'

const artworkSlugs: Record<BuiltinArcadeGameKey, string> = {
  avalon: 'avalon',
  departed_suspicion: 'departed-suspicion',
  gomoku: 'gomoku',
  xiangqi: 'xiangqi',
  go: 'go',
  poker: 'poker',
  doudizhu: 'doudizhu',
  junqi: 'junqi',
  reaction: 'reaction',
  schulte: 'schulte',
  minesweeper: 'minesweeper',
  hanoi: 'hanoi',
  monopoly: 'monopoly',
}

describe('GameCardArtwork', () => {
  it.each(Object.entries(artworkSlugs))('maps %s to its premium icon asset', (gameKey, slug) => {
    const wrapper = mount(GameCardArtwork, {
      props: { gameKey: gameKey as BuiltinArcadeGameKey },
    })

    expect(wrapper.classes()).toContain(`art-${gameKey}`)
    expect(wrapper.get('img').attributes('src')).toContain(slug)
    expect(wrapper.find('.game-card-art-fallback').exists()).toBe(false)
  })

  it('keeps a visual fallback for a plugin key', () => {
    const wrapper = mount(GameCardArtwork, {
      props: { gameKey: 'plugin-example' },
    })

    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('.game-card-art-fallback').exists()).toBe(true)
  })
})
