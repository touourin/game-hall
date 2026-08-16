import { pixelPushPalette } from './pixelPushPalettes'
import { pixelPushArenaDimensions } from './pixelPushRenderer'
import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'

describe('pixel push presentation', () => {
  it('为四套大厅主题提供独立且完整的擂台材质', () => {
    const twilightBlueSteel = pixelPushPalette('emerald')
    const titanium = pixelPushPalette('midnight')
    const moonCloudCeramic = pixelPushPalette('royal')
    const tangerineGlaze = pixelPushPalette('amber')

    expect(new Set([
      twilightBlueSteel.voidCenter,
      titanium.voidCenter,
      moonCloudCeramic.voidCenter,
      tangerineGlaze.voidCenter,
    ]).size).toBe(4)
    expect(moonCloudCeramic.voidCenter).toBe(gameThemeMaterials('royal').scene.center)
    expect(moonCloudCeramic.arenaTop).toBe(gameThemeMaterials('royal').stage.top)
    expect(moonCloudCeramic.playerName).toBe(gameThemeMaterials('royal').copy.onStage)

    const materialKeys = Object.keys(twilightBlueSteel).sort()
    expect(Object.keys(titanium).sort()).toEqual(materialKeys)
    expect(Object.keys(moonCloudCeramic).sort()).toEqual(materialKeys)
    expect(Object.keys(tangerineGlaze).sort()).toEqual(materialKeys)
    expect(Object.values(moonCloudCeramic).every(Boolean)).toBe(true)
    expect(Object.values(tangerineGlaze).every(Boolean)).toBe(true)
  })

  it('让四套材质共享完全相同的收缩几何', () => {
    const open = pixelPushArenaDimensions('moon_station', 0)
    const closed = pixelPushArenaDimensions('moon_station', 1_000)

    expect(open).toEqual({ halfWidth: 4_200, halfHeight: 2_700, radius: 760 })
    expect(closed).toEqual({ halfWidth: 2_050, halfHeight: 1_550, radius: 760 })
  })
})
