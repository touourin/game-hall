import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'
import type { ThemeName } from '../../theme'

export interface CriticalCrossingPalette {
  atmosphere: string
  deckTop: string
  deckBottom: string
  deckEdge: string
  deckDetail: string
  laneMark: string
  rail: string
  railGlow: string
  gap: string
  barrier: string
  barrierGlow: string
  groundObstacle: string
  overheadObstacle: string
  runnerBody: string
  runnerEdge: string
  runnerAccent: string
  runnerSkin: string
  shadow: string
  copy: string
}

export function criticalCrossingPalette(theme: ThemeName): CriticalCrossingPalette {
  const material = gameThemeMaterials(theme)

  return {
    atmosphere: material.scene.fog,
    deckTop: material.stage.top,
    deckBottom: material.stage.bottom,
    deckEdge: material.stage.edge,
    deckDetail: material.stage.detail,
    laneMark: material.stage.innerEdge,
    rail: material.metal.body,
    railGlow: material.stage.glow,
    gap: material.scene.bottom,
    barrier: material.semantic.dangerStrong,
    barrierGlow: material.semantic.dangerGlow,
    groundObstacle: material.semantic.warningStrong,
    overheadObstacle: material.semantic.successStrong,
    runnerBody: material.metal.side,
    runnerEdge: material.metal.edge,
    runnerAccent: '#ff7a48',
    runnerSkin: '#e8a071',
    shadow: material.stage.shadow,
    copy: material.copy.onStage,
  }
}
