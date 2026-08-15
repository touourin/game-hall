import { pixelPushPalette } from './pixelPushPalettes'
import { pixelPushArenaDimensions } from './pixelPushRenderer'
import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'

describe('pixel push presentation', () => {
  it('为三套大厅主题提供独立且完整的擂台材质', () => {
    const aurora = pixelPushPalette('emerald')
    const titanium = pixelPushPalette('midnight')
    const moonWhite = pixelPushPalette('royal')

    expect(new Set([
      aurora.voidCenter,
      titanium.voidCenter,
      moonWhite.voidCenter,
    ]).size).toBe(3)
    expect(moonWhite.voidCenter).toBe(gameThemeMaterials('royal').scene.center)
    expect(moonWhite.arenaTop).toBe(gameThemeMaterials('royal').stage.top)
    expect(moonWhite.playerName).toBe(gameThemeMaterials('royal').copy.onStage)

    const materialKeys = Object.keys(aurora).sort()
    expect(Object.keys(titanium).sort()).toEqual(materialKeys)
    expect(Object.keys(moonWhite).sort()).toEqual(materialKeys)
    expect(Object.values(moonWhite).every(Boolean)).toBe(true)
  })

  it('让三套材质共享完全相同的收缩几何', () => {
    const open = pixelPushArenaDimensions('moon_station', 0)
    const closed = pixelPushArenaDimensions('moon_station', 1_000)

    expect(open).toEqual({ halfWidth: 4_200, halfHeight: 2_700, radius: 760 })
    expect(closed).toEqual({ halfWidth: 2_050, halfHeight: 1_550, radius: 760 })
  })
})
