import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'
import type { ThemeName } from '../../theme'

export interface CriticalCrossingPalette {
  center: string
  edge: string
  grid: string
  pulse: string
  pulseGlow: string
  gate: string
  gateGlow: string
  boundary: string
  boundaryCritical: string
  core: string
  coreEdge: string
  coreCenter: string
}

export function criticalCrossingPalette(theme: ThemeName): CriticalCrossingPalette {
  const material = gameThemeMaterials(theme)

  return {
    center: material.scene.center,
    edge: material.scene.bottom,
    grid: material.scene.grid,
    pulse: material.semantic.danger,
    pulseGlow: material.semantic.dangerStrong,
    gate: material.semantic.success,
    gateGlow: material.semantic.successStrong,
    boundary: material.semantic.warningGlow,
    boundaryCritical: material.semantic.dangerGlow,
    core: material.scene.fog,
    coreEdge: material.stage.edge,
    coreCenter: material.metal.core,
  }
}
