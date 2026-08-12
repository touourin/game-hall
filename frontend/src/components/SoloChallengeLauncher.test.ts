import { mount } from '@vue/test-utils'
import type { ArcadeGameKey } from '../types/arcade'
import SoloChallengeLauncher from './SoloChallengeLauncher.vue'

describe('SoloChallengeLauncher', () => {
  it.each<ArcadeGameKey>(['reaction', 'schulte', 'minesweeper', 'hanoi', 'tetris'])(
    'does not render a decorative sequence number for %s',
    (gameKey) => {
      const wrapper = mount(SoloChallengeLauncher, {
        props: {
          gameKey,
          modelValue: {},
        },
      })

      expect(wrapper.find('.solo-visual-index').exists()).toBe(false)
      expect(wrapper.get('.solo-protocol b').text()).toBe('SOLO')
      expect(wrapper.text()).not.toMatch(/SOLO \/ 0\d/)
    },
  )
})
