import { gameThemeMaterials } from './gameThemeMaterials'

describe('game theme materials', () => {
  it('为所有官方游戏提供同一套四主题材质契约', () => {
    const aurora = gameThemeMaterials('emerald')
    const titanium = gameThemeMaterials('midnight')
    const moonWhite = gameThemeMaterials('royal')
    const orangeIvory = gameThemeMaterials('amber')

    expect(aurora.scene.center).toBe('#0a2432')
    expect(titanium.scene.center).toBe('#121a1f')
    expect(moonWhite.scene.center).toBe('#d9e0e3')
    expect(orangeIvory.scene.center).toBe('#f6eadf')
    expect(Object.keys(titanium)).toEqual(Object.keys(aurora))
    expect(Object.keys(moonWhite)).toEqual(Object.keys(aurora))
    expect(Object.keys(orangeIvory)).toEqual(Object.keys(aurora))
    expect(titanium.stage.edge).toBe('#8ea9b8')
    expect(orangeIvory.stage.edge).toBe('#c45124')
  })

  it('月白材质使用深色场景文字并保留清晰边缘', () => {
    const moonWhite = gameThemeMaterials('royal')

    expect(moonWhite.copy.onStage).toBe('#26363d')
    expect(moonWhite.stage.innerEdge).toContain('255, 255, 255')
    expect(moonWhite.semantic.dangerStrong).not.toBe(moonWhite.semantic.successStrong)
  })

  it('曜石黑钛不再沿用暖棕材质', () => {
    const titanium = JSON.stringify(gameThemeMaterials('midnight'))

    expect(titanium).not.toContain('#29251f')
    expect(titanium).not.toContain('#b99168')
    expect(titanium).not.toContain('185, 145, 104')
  })
})
