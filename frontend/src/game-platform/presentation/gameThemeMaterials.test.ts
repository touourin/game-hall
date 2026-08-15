import { gameThemeMaterials } from './gameThemeMaterials'

describe('game theme materials', () => {
  it('为所有官方游戏提供同一套三主题材质契约', () => {
    const aurora = gameThemeMaterials('emerald')
    const titanium = gameThemeMaterials('midnight')
    const moonWhite = gameThemeMaterials('royal')

    expect(aurora.scene.center).toBe('#0a2432')
    expect(titanium.scene.center).toBe('#29251f')
    expect(moonWhite.scene.center).toBe('#d9e0e3')
    expect(Object.keys(titanium)).toEqual(Object.keys(aurora))
    expect(Object.keys(moonWhite)).toEqual(Object.keys(aurora))
  })

  it('月白材质使用深色场景文字并保留清晰边缘', () => {
    const moonWhite = gameThemeMaterials('royal')

    expect(moonWhite.copy.onStage).toBe('#26363d')
    expect(moonWhite.stage.innerEdge).toContain('255, 255, 255')
    expect(moonWhite.semantic.dangerStrong).not.toBe(moonWhite.semantic.successStrong)
  })
})
