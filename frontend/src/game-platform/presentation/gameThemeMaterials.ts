import type { ThemeName } from '../../theme'

export interface GameThemeMaterials {
  scene: {
    top: string
    center: string
    bottom: string
    glow: string
    grid: string
    fog: string
    particle: string
  }
  stage: {
    top: string
    bottom: string
    edge: string
    innerEdge: string
    detail: string
    glow: string
    shadow: string
  }
  metal: {
    body: string
    side: string
    edge: string
    glass: string
    core: string
    glow: string
  }
  copy: {
    primary: string
    secondary: string
    onStage: string
    onStageOutline: string
  }
  semantic: {
    danger: string
    dangerStrong: string
    dangerGlow: string
    warning: string
    warningStrong: string
    warningGlow: string
    success: string
    successStrong: string
    successGlow: string
  }
}

const TWILIGHT_BLUE_STEEL: GameThemeMaterials = {
  scene: {
    top: '#071522',
    center: '#0a2432',
    bottom: '#020810',
    glow: 'rgba(80, 183, 205, .16)',
    grid: 'rgba(102, 170, 205, .08)',
    fog: 'rgba(75, 164, 188, .1)',
    particle: 'rgba(139, 233, 236, .42)',
  },
  stage: {
    top: '#1b4650',
    bottom: '#102b35',
    edge: '#67dfe1',
    innerEdge: 'rgba(181, 242, 242, .42)',
    detail: '#4e788d',
    glow: 'rgba(71, 217, 228, .48)',
    shadow: 'rgba(2, 8, 11, .64)',
  },
  metal: {
    body: '#b6ccd8',
    side: '#243f51',
    edge: '#e7f4fb',
    glass: '#315f78',
    core: '#7be2dc',
    glow: 'rgba(93, 216, 211, .72)',
  },
  copy: {
    primary: '#f4ffff',
    secondary: '#a9c8dc',
    onStage: '#f4ffff',
    onStageOutline: 'rgba(2, 8, 13, .88)',
  },
  semantic: {
    danger: '#d86c7c',
    dangerStrong: '#ff6680',
    dangerGlow: 'rgba(255, 80, 108, .67)',
    warning: '#d9b55f',
    warningStrong: '#ffdc75',
    warningGlow: 'rgba(255, 207, 88, .78)',
    success: '#56b6a8',
    successStrong: '#7be2dc',
    successGlow: 'rgba(93, 216, 211, .52)',
  },
}

const OBSIDIAN_TITANIUM: GameThemeMaterials = {
  scene: {
    top: '#0c1114',
    center: '#121a1f',
    bottom: '#030506',
    glow: 'rgba(125, 156, 171, .14)',
    grid: 'rgba(177, 202, 214, .065)',
    fog: 'rgba(101, 128, 140, .09)',
    particle: 'rgba(195, 218, 228, .3)',
  },
  stage: {
    top: '#252d32',
    bottom: '#11171a',
    edge: '#8ea9b8',
    innerEdge: 'rgba(224, 238, 245, .34)',
    detail: '#5d727e',
    glow: 'rgba(125, 160, 178, .38)',
    shadow: 'rgba(0, 1, 2, .68)',
  },
  metal: {
    body: '#aebdc5',
    side: '#28343a',
    edge: '#edf5f8',
    glass: '#49616d',
    core: '#93afbd',
    glow: 'rgba(142, 177, 194, .58)',
  },
  copy: {
    primary: '#f1f6f8',
    secondary: '#aebdc5',
    onStage: '#f1f6f8',
    onStageOutline: 'rgba(1, 4, 5, .92)',
  },
  semantic: {
    danger: '#cf6d73',
    dangerStrong: '#e37b82',
    dangerGlow: 'rgba(218, 91, 102, .58)',
    warning: '#c6a35f',
    warningStrong: '#e3c174',
    warningGlow: 'rgba(218, 177, 91, .64)',
    success: '#6fae9d',
    successStrong: '#8bcab8',
    successGlow: 'rgba(111, 190, 168, .4)',
  },
}

const MOON_CLOUD_CERAMIC: GameThemeMaterials = {
  scene: {
    top: '#eef1f2',
    center: '#d9e0e3',
    bottom: '#c7d0d5',
    glow: 'rgba(255, 255, 255, .68)',
    grid: 'rgba(55, 77, 88, .075)',
    fog: 'rgba(255, 255, 255, .28)',
    particle: 'rgba(68, 91, 102, .2)',
  },
  stage: {
    top: '#f0f1ec',
    bottom: '#c3cdcf',
    edge: '#3e796e',
    innerEdge: 'rgba(255, 255, 255, .82)',
    detail: '#788b8e',
    glow: 'rgba(62, 140, 126, .28)',
    shadow: 'rgba(50, 67, 75, .24)',
  },
  metal: {
    body: '#f3f1e9',
    side: '#9eaaad',
    edge: '#ffffff',
    glass: '#6f8993',
    core: '#3e8c7d',
    glow: 'rgba(65, 145, 127, .42)',
  },
  copy: {
    primary: '#26363d',
    secondary: '#46565e',
    onStage: '#26363d',
    onStageOutline: 'rgba(255, 255, 255, .94)',
  },
  semantic: {
    danger: '#bc625d',
    dangerStrong: '#bf5f5b',
    dangerGlow: 'rgba(188, 79, 73, .34)',
    warning: '#8f682f',
    warningStrong: '#9a6b25',
    warningGlow: 'rgba(183, 125, 43, .38)',
    success: '#4f927b',
    successStrong: '#3e8c7d',
    successGlow: 'rgba(65, 145, 127, .28)',
  },
}

const TANGERINE_GLAZE: GameThemeMaterials = {
  scene: {
    top: '#fffaf2',
    center: '#ffe7c7',
    bottom: '#f2cfa9',
    glow: 'rgba(255, 255, 255, .8)',
    grid: 'rgba(122, 75, 43, .08)',
    fog: 'rgba(255, 248, 238, .38)',
    particle: 'rgba(242, 106, 19, .34)',
  },
  stage: {
    top: '#fff4df',
    bottom: '#e4ba8e',
    edge: '#f26a13',
    innerEdge: 'rgba(255, 255, 255, .9)',
    detail: '#9e6b4c',
    glow: 'rgba(242, 106, 19, .38)',
    shadow: 'rgba(105, 60, 31, .25)',
  },
  metal: {
    body: '#fff0df',
    side: '#bd9878',
    edge: '#ffffff',
    glass: '#916e59',
    core: '#f26a13',
    glow: 'rgba(242, 106, 19, .5)',
  },
  copy: {
    primary: '#35251d',
    secondary: '#675347',
    onStage: '#35251d',
    onStageOutline: 'rgba(255, 253, 249, .96)',
  },
  semantic: {
    danger: '#b94f48',
    dangerStrong: '#aa413c',
    dangerGlow: 'rgba(185, 79, 72, .34)',
    warning: '#9a6828',
    warningStrong: '#8a5a1f',
    warningGlow: 'rgba(177, 111, 35, .38)',
    success: '#4e8b72',
    successStrong: '#3f785f',
    successGlow: 'rgba(78, 139, 114, .3)',
  },
}

export const GAME_THEME_MATERIALS: Readonly<Record<ThemeName, GameThemeMaterials>> = {
  emerald: TWILIGHT_BLUE_STEEL,
  midnight: OBSIDIAN_TITANIUM,
  royal: MOON_CLOUD_CERAMIC,
  amber: TANGERINE_GLAZE,
}

export function gameThemeMaterials(theme: ThemeName): GameThemeMaterials {
  return GAME_THEME_MATERIALS[theme]
}
