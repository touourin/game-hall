import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'
import type { ThemeName } from '../../theme'

export interface PixelPushPalette {
  voidTop: string
  voidCenter: string
  voidBottom: string
  voidGlow: string
  particle: string
  arenaTop: string
  arenaBottom: string
  arenaEdge: string
  arenaInnerEdge: string
  arenaGrid: string
  arenaGlow: string
  dangerEdge: string
  dangerGlow: string
  pulseCore: string
  pulseGlow: string
  robotOutline: string
  robotFace: string
  robotEye: string
  robotHighlight: string
  playerShadow: string
  playerName: string
  playerNameOutline: string
  brace: string
  braceSoft: string
  impact: string
}

interface RobotMaterial {
  outline: string
  face: string
  eye: string
  highlight: string
  brace: string
  braceSoft: string
}

const ROBOT_MATERIALS: Readonly<Record<ThemeName, RobotMaterial>> = {
  emerald: {
    outline: '#051116',
    face: '#07131a',
    eye: '#e9ffff',
    highlight: 'rgba(255, 255, 255, .2)',
    brace: '#b9ecff',
    braceSoft: 'rgba(255, 255, 255, .34)',
  },
  midnight: {
    outline: '#181511',
    face: '#2a241d',
    eye: '#fff0d9',
    highlight: 'rgba(255, 240, 217, .2)',
    brace: '#d2c6ad',
    braceSoft: 'rgba(243, 225, 198, .28)',
  },
  royal: {
    outline: '#485960',
    face: '#405159',
    eye: '#ffffff',
    highlight: 'rgba(255, 255, 255, .48)',
    brace: '#3f7891',
    braceSoft: 'rgba(255, 255, 255, .72)',
  },
}

export function pixelPushPalette(theme: ThemeName): PixelPushPalette {
  const material = gameThemeMaterials(theme)
  const robot = ROBOT_MATERIALS[theme]

  return {
    voidTop: material.scene.top,
    voidCenter: material.scene.center,
    voidBottom: material.scene.bottom,
    voidGlow: material.scene.glow,
    particle: material.scene.particle,
    arenaTop: material.stage.top,
    arenaBottom: material.stage.bottom,
    arenaEdge: material.stage.edge,
    arenaInnerEdge: material.stage.innerEdge,
    arenaGrid: material.scene.grid,
    arenaGlow: material.stage.glow,
    dangerEdge: material.semantic.dangerStrong,
    dangerGlow: material.semantic.dangerGlow,
    pulseCore: material.semantic.warningStrong,
    pulseGlow: material.semantic.warningGlow,
    robotOutline: robot.outline,
    robotFace: robot.face,
    robotEye: robot.eye,
    robotHighlight: robot.highlight,
    playerShadow: material.stage.shadow,
    playerName: material.copy.onStage,
    playerNameOutline: material.copy.onStageOutline,
    brace: robot.brace,
    braceSoft: robot.braceSoft,
    impact: material.semantic.warningStrong,
  }
}
