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
    wall: 'rgba(18, 25, 29, .88)',
    wallEdge: 'rgba(195, 217, 227, .18)',
    rail: '#2b3940',
    railEdge: '#8fa9b6',
    railJoint: '#d6e5ec',
    platforms: {
      normal: { top: '#899ba4', side: '#28363d', edge: '#dceaf0', detail: '#5d727e', glow: 'rgba(129, 166, 183, .24)' },
      spikes: { top: '#956970', side: '#462a30', edge: '#e9b3ba', detail: '#d4777f', glow: 'rgba(211, 86, 101, .31)' },
      crumble: { top: '#8f8175', side: '#3c332d', edge: '#d8c7b8', detail: '#685448', glow: 'rgba(168, 133, 102, .2)' },
      conveyor_left: { top: '#718e99', side: '#263a43', edge: '#bdd5df', detail: '#8ab9c8', glow: 'rgba(112, 167, 187, .26)' },
      conveyor_right: { top: '#718e99', side: '#263a43', edge: '#bdd5df', detail: '#8ab9c8', glow: 'rgba(112, 167, 187, .26)' },
      spring: { top: '#777b90', side: '#343747', edge: '#c6cbdf', detail: '#9ba1c3', glow: 'rgba(132, 139, 190, .27)' },
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
  amber: {
    wall: 'rgba(255, 241, 223, .88)',
    wallEdge: 'rgba(113, 69, 41, .19)',
    rail: '#c3a084',
    railEdge: '#fffaf2',
    railJoint: '#744d38',
    platforms: {
      normal: { top: '#ffe8cf', side: '#bc9b80', edge: '#ffffff', detail: '#a06a49', glow: 'rgba(242, 106, 19, .2)' },
      spikes: { top: '#e9cdc7', side: '#b47e77', edge: '#fff2ee', detail: '#b94f48', glow: 'rgba(185, 79, 72, .22)' },
      crumble: { top: '#e9d5bd', side: '#b49778', edge: '#fff7e9', detail: '#8a6848', glow: 'rgba(174, 111, 57, .18)' },
      conveyor_left: { top: '#e1e4d9', side: '#98a898', edge: '#fbfff8', detail: '#4e8b72', glow: 'rgba(78, 139, 114, .2)' },
      conveyor_right: { top: '#e1e4d9', side: '#98a898', edge: '#fbfff8', detail: '#4e8b72', glow: 'rgba(78, 139, 114, .2)' },
      spring: { top: '#e4d8e2', side: '#a28fa2', edge: '#fff9ff', detail: '#856a89', glow: 'rgba(133, 106, 137, .2)' },
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
