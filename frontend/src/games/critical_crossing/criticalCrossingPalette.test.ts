import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'
import { criticalCrossingPalette } from './criticalCrossingPalette'

describe('critical crossing palette', () => {
  it.each(['emerald', 'midnight', 'royal', 'amber'] as const)(
    '让 %s 竞技场继承全局游戏主题材质',
    (theme) => {
      const palette = criticalCrossingPalette(theme)
      const material = gameThemeMaterials(theme)

      expect(palette.atmosphere).toBe(material.scene.fog)
      expect(palette.deckTop).toBe(material.stage.top)
      expect(palette.overheadObstacle).toBe(material.semantic.successStrong)
      expect(palette.barrier).toBe(material.semantic.dangerStrong)
    },
  )
})
