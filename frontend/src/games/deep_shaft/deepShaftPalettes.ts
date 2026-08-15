import { gameThemeMaterials } from '../../game-platform/presentation/gameThemeMaterials'
import type { ThemeName } from '../../theme'
import type { PlatformKind } from './deepShaftEngine'

export interface ShaftMaterial {
  top: string
  side: string
  edge: string
  detail: string
  glow: string
}

export interface DeepShaftPalette {
  backgroundTop: string
  backgroundCenter: string
  backgroundBottom: string
  wall: string
  wallEdge: string
  grid: string
  rail: string
  railEdge: string
  railJoint: string
  fog: string
  depthText: string
  pressure: string
  pressureGlow: string
  podBody: string
  podSide: string
  podEdge: string
  podGlass: string
  podCore: string
  podGlow: string
  platforms: Record<PlatformKind, ShaftMaterial>
}

interface ShaftStructureMaterial {
  wall: string
  wallEdge: string
  rail: string
  railEdge: string
  railJoint: string
  platforms: Record<PlatformKind, ShaftMaterial>
}

const SHAFT_STRUCTURES: Readonly<Record<ThemeName, ShaftStructureMaterial>> = {
  emerald: {
    wall: 'rgba(14, 35, 51, .82)',
    wallEdge: 'rgba(152, 205, 236, .2)',
    rail: '#1c4054',
    railEdge: '#7aa7bf',
    railJoint: '#b8d7e8',
    platforms: {
      normal: { top: '#8ca7b6', side: '#263e4c', edge: '#d6e8f1', detail: '#4e788d', glow: 'rgba(98, 185, 206, .24)' },
      spikes: { top: '#9d6d76', side: '#492830', edge: '#f2b3bb', detail: '#f18a98', glow: 'rgba(218, 82, 106, .34)' },
      crumble: { top: '#9b887a', side: '#43362e', edge: '#e0c4ad', detail: '#6d4d3e', glow: 'rgba(205, 151, 103, .26)' },
      conveyor_left: { top: '#6c94a7', side: '#203e50', edge: '#b9dce9', detail: '#7ce0dc', glow: 'rgba(72, 193, 196, .3)' },
      conveyor_right: { top: '#6c94a7', side: '#203e50', edge: '#b9dce9', detail: '#7ce0dc', glow: 'rgba(72, 193, 196, .3)' },
      spring: { top: '#7e779b', side: '#302c4d', edge: '#cbc1ee', detail: '#aa9de5', glow: 'rgba(145, 117, 222, .34)' },
    },
  },
  midnight: {
    wall: 'rgba(46, 41, 34, .86)',
    wallEdge: 'rgba(229, 204, 168, .17)',
    rail: '#4b4034',
    railEdge: '#b18e6b',
    railJoint: '#e1c8aa',
    platforms: {
      normal: { top: '#a89b88', side: '#463c31', edge: '#ded0bd', detail: '#756451', glow: 'rgba(185, 145, 104, .2)' },
      spikes: { top: '#9d706c', side: '#4b2d2b', edge: '#e6b2a9', detail: '#cf756f', glow: 'rgba(186, 83, 79, .28)' },
      crumble: { top: '#ae8d6d', side: '#4a3526', edge: '#e8c6a3', detail: '#714930', glow: 'rgba(199, 139, 83, .24)' },
      conveyor_left: { top: '#788d86', side: '#303e39', edge: '#bdcec6', detail: '#95b6a9', glow: 'rgba(123, 164, 147, .22)' },
      conveyor_right: { top: '#788d86', side: '#303e39', edge: '#bdcec6', detail: '#95b6a9', glow: 'rgba(123, 164, 147, .22)' },
      spring: { top: '#857b8c', side: '#3d3543', edge: '#cfc1d4', detail: '#aa94b1', glow: 'rgba(145, 117, 158, .25)' },
    },
  },
  royal: {
    wall: 'rgba(246, 247, 244, .82)',
    wallEdge: 'rgba(72, 92, 102, .18)',
    rail: '#aab4b8',
    railEdge: '#f9faf7',
    railJoint: '#66757d',
    platforms: {
      normal: { top: '#e8e6dd', side: '#a8b0b0', edge: '#ffffff', detail: '#788b8e', glow: 'rgba(73, 139, 124, .16)' },
      spikes: { top: '#dfcbc6', side: '#ad817b', edge: '#fff3ee', detail: '#be645d', glow: 'rgba(188, 82, 74, .2)' },
      crumble: { top: '#ded2c1', side: '#ad9780', edge: '#fff7e9', detail: '#8f7155', glow: 'rgba(174, 126, 79, .16)' },
      conveyor_left: { top: '#d5e2e0', side: '#8ea7a4', edge: '#f7ffff', detail: '#3d8f81', glow: 'rgba(61, 143, 129, .18)' },
      conveyor_right: { top: '#d5e2e0', side: '#8ea7a4', edge: '#f7ffff', detail: '#3d8f81', glow: 'rgba(61, 143, 129, .18)' },
      spring: { top: '#d9d5e2', side: '#9b93ad', edge: '#fffaff', detail: '#766b99', glow: 'rgba(118, 101, 155, .18)' },
    },
  },
}

export function deepShaftPalette(theme: ThemeName): DeepShaftPalette {
  const material = gameThemeMaterials(theme)
  const structure = SHAFT_STRUCTURES[theme]

  return {
    backgroundTop: material.scene.top,
    backgroundCenter: material.scene.center,
    backgroundBottom: material.scene.bottom,
    wall: structure.wall,
    wallEdge: structure.wallEdge,
    grid: material.scene.grid,
    rail: structure.rail,
    railEdge: structure.railEdge,
    railJoint: structure.railJoint,
    fog: material.scene.fog,
    depthText: material.copy.secondary,
    pressure: material.semantic.danger,
    pressureGlow: material.semantic.dangerGlow,
    podBody: material.metal.body,
    podSide: material.metal.side,
    podEdge: material.metal.edge,
    podGlass: material.metal.glass,
    podCore: material.metal.core,
    podGlow: material.metal.glow,
    platforms: structure.platforms,
  }
}
