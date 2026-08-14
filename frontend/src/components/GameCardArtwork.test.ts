import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import type { BuiltinArcadeGameKey } from '../types/arcade'
import { applyTheme } from '../theme'
import GameCardArtwork from './GameCardArtwork.vue'

const artworkSlugs: Record<BuiltinArcadeGameKey, string> = {
  avalon: 'avalon',
  chess: 'chess',
  departed_suspicion: 'departed-suspicion',
  one_night_werewolf: 'one-night-werewolf',
  gomoku: 'gomoku',
  xiangqi: 'xiangqi',
  go: 'go',
  poker: 'poker',
  doudizhu: 'doudizhu',
  junqi: 'junqi',
  reaction: 'reaction',
  deep_shaft: 'deep-shaft',
  schulte: 'schulte',
  survive_three_seconds: 'survive-three-seconds',
  minesweeper: 'minesweeper',
  hanoi: 'hanoi',
  tetris: 'tetris',
  monopoly: 'monopoly',
}

describe('GameCardArtwork', () => {
  beforeEach(() => applyTheme('emerald'))

  it.each(Object.entries(artworkSlugs))('maps %s to its dark premium icon asset', (gameKey, slug) => {
    const wrapper = mount(GameCardArtwork, {
      props: { gameKey: gameKey as BuiltinArcadeGameKey },
    })

    expect(wrapper.classes()).toContain(`art-${gameKey}`)
    expect(wrapper.get('img').attributes('src')).toContain(`${slug}-dark`)
    expect(wrapper.find('.game-card-art-fallback').exists()).toBe(false)
  })

  it('loads only the material variant used by the current theme', async () => {
    const wrapper = mount(GameCardArtwork, { props: { gameKey: 'go' } })

    expect(wrapper.findAll('img')).toHaveLength(1)
    expect(wrapper.get('img').attributes('src')).toContain('go-dark')

    applyTheme('royal')
    await nextTick()

    expect(wrapper.findAll('img')).toHaveLength(1)
    expect(wrapper.get('img').attributes('src')).toContain('go-light')
  })

  it('keeps a visual fallback for a plugin key', () => {
    const wrapper = mount(GameCardArtwork, {
      props: { gameKey: 'plugin-example' },
    })

    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('.game-card-art-fallback').exists()).toBe(true)
  })
})
