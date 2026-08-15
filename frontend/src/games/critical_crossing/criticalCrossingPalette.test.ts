import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'
import { criticalCrossingPalette } from './criticalCrossingPalette'

describe('critical crossing palette', () => {
  it.each(['emerald', 'midnight', 'royal'] as const)(
    '让 %s 竞技场继承全局游戏主题材质',
    (theme) => {
      const palette = criticalCrossingPalette(theme)
      const material = gameThemeMaterials(theme)

      expect(palette.center).toBe(material.scene.center)
      expect(palette.edge).toBe(material.scene.bottom)
      expect(palette.gate).toBe(material.semantic.success)
      expect(palette.pulse).toBe(material.semantic.danger)
    },
  )
})
