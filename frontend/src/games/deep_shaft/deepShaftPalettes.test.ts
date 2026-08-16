import { deepShaftPalette } from './deepShaftPalettes'
import { deepShaftProgress } from './deepShaftRenderer'
import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'

describe('deep shaft presentation', () => {
  it('为四套大厅主题提供不同且完整的平台材质', () => {
    const twilightBlueSteel = deepShaftPalette('emerald')
    const titanium = deepShaftPalette('midnight')
    const moonCloudCeramic = deepShaftPalette('royal')
    const tangerineGlaze = deepShaftPalette('amber')

    expect(new Set([
      twilightBlueSteel.backgroundCenter,
      titanium.backgroundCenter,
      moonCloudCeramic.backgroundCenter,
      tangerineGlaze.backgroundCenter,
    ]).size).toBe(4)
    expect(moonCloudCeramic.backgroundCenter).toBe(gameThemeMaterials('royal').scene.center)
    expect(titanium.podBody).toBe(gameThemeMaterials('midnight').metal.body)
    expect(Object.keys(twilightBlueSteel.platforms)).toHaveLength(6)
    expect(twilightBlueSteel.platforms.spikes.detail).not.toBe(twilightBlueSteel.platforms.normal.detail)
    expect(titanium.platforms.spring.detail).not.toBe(titanium.platforms.crumble.detail)
    expect(Object.keys(tangerineGlaze.platforms)).toHaveLength(6)
    expect(tangerineGlaze.podCore).toBe(gameThemeMaterials('amber').metal.core)
  })

  it('将楼层进度限制在 0 到 100 之间', () => {
    expect(deepShaftProgress(-8)).toBe(0)
    expect(deepShaftProgress(42)).toBe(42)
    expect(deepShaftProgress(108)).toBe(100)
  })
})
