import { gameThemeMaterials } from './gameThemeMaterials'

describe('game theme materials', () => {
  it('为所有官方游戏提供同一套四主题材质契约', () => {
    const twilightBlueSteel = gameThemeMaterials('emerald')
    const titanium = gameThemeMaterials('midnight')
    const moonCloudCeramic = gameThemeMaterials('royal')
    const tangerineGlaze = gameThemeMaterials('amber')

    expect(twilightBlueSteel.scene.center).toBe('#0a2432')
    expect(titanium.scene.center).toBe('#121a1f')
    expect(moonCloudCeramic.scene.center).toBe('#d9e0e3')
    expect(tangerineGlaze.scene.center).toBe('#ffe7c7')
    expect(Object.keys(titanium)).toEqual(Object.keys(twilightBlueSteel))
    expect(Object.keys(moonCloudCeramic)).toEqual(Object.keys(twilightBlueSteel))
    expect(Object.keys(tangerineGlaze)).toEqual(Object.keys(twilightBlueSteel))
    expect(titanium.stage.edge).toBe('#8ea9b8')
    expect(tangerineGlaze.stage.edge).toBe('#f26a13')
  })

  it('月白云瓷使用深色场景文字并保留清晰边缘', () => {
    const moonCloudCeramic = gameThemeMaterials('royal')

    expect(moonCloudCeramic.copy.onStage).toBe('#26363d')
    expect(moonCloudCeramic.stage.innerEdge).toContain('255, 255, 255')
    expect(moonCloudCeramic.semantic.dangerStrong).not.toBe(moonCloudCeramic.semantic.successStrong)
  })

  it('曜石黑钛不再沿用暖棕材质', () => {
    const titanium = JSON.stringify(gameThemeMaterials('midnight'))

    expect(titanium).not.toContain('#29251f')
    expect(titanium).not.toContain('#b99168')
    expect(titanium).not.toContain('185, 145, 104')
  })
})
