import { deepShaftPalette } from './deepShaftPalettes'
import { deepShaftProgress } from './deepShaftRenderer'
import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'

describe('deep shaft presentation', () => {
  it('为四套大厅主题提供不同且完整的平台材质', () => {
    const aurora = deepShaftPalette('emerald')
    const titanium = deepShaftPalette('midnight')
    const moonWhite = deepShaftPalette('royal')
    const orangeIvory = deepShaftPalette('amber')

    expect(new Set([
      aurora.backgroundCenter,
      titanium.backgroundCenter,
      moonWhite.backgroundCenter,
      orangeIvory.backgroundCenter,
    ]).size).toBe(4)
    expect(moonWhite.backgroundCenter).toBe(gameThemeMaterials('royal').scene.center)
    expect(titanium.podBody).toBe(gameThemeMaterials('midnight').metal.body)
    expect(Object.keys(aurora.platforms)).toHaveLength(6)
    expect(aurora.platforms.spikes.detail).not.toBe(aurora.platforms.normal.detail)
    expect(titanium.platforms.spring.detail).not.toBe(titanium.platforms.crumble.detail)
    expect(Object.keys(orangeIvory.platforms)).toHaveLength(6)
    expect(orangeIvory.podCore).toBe(gameThemeMaterials('amber').metal.core)
  })

  it('将楼层进度限制在 0 到 100 之间', () => {
    expect(deepShaftProgress(-8)).toBe(0)
    expect(deepShaftProgress(42)).toBe(42)
    expect(deepShaftProgress(108)).toBe(100)
  })
})
