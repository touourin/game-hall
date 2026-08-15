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

const AURORA_MIST: GameThemeMaterials = {
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

const WARM_TITANIUM: GameThemeMaterials = {
  scene: {
    top: '#191713',
    center: '#29251f',
    bottom: '#090908',
    glow: 'rgba(181, 139, 93, .12)',
    grid: 'rgba(211, 188, 154, .06)',
    fog: 'rgba(159, 123, 82, .08)',
    particle: 'rgba(222, 199, 166, .28)',
  },
  stage: {
    top: '#51483b',
    bottom: '#302b25',
    edge: '#c5a67f',
    innerEdge: 'rgba(235, 216, 190, .36)',
    detail: '#756451',
    glow: 'rgba(177, 132, 88, .38)',
    shadow: 'rgba(4, 3, 2, .58)',
  },
  metal: {
    body: '#c7b8a5',
    side: '#514337',
    edge: '#f0dfc9',
    glass: '#504d45',
    core: '#bd9b72',
    glow: 'rgba(185, 145, 104, .6)',
  },
  copy: {
    primary: '#f5eadb',
    secondary: '#d3c2ad',
    onStage: '#f5eadb',
    onStageOutline: 'rgba(16, 13, 10, .9)',
  },
  semantic: {
    danger: '#c76563',
    dangerStrong: '#d87472',
    dangerGlow: 'rgba(193, 77, 75, .58)',
    warning: '#b99168',
    warningStrong: '#dbbb77',
    warningGlow: 'rgba(202, 155, 84, .7)',
    success: '#849d8b',
    successStrong: '#a8c5b4',
    successGlow: 'rgba(123, 164, 147, .36)',
  },
}

const MOON_WHITE: GameThemeMaterials = {
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

export const GAME_THEME_MATERIALS: Readonly<Record<ThemeName, GameThemeMaterials>> = {
  emerald: AURORA_MIST,
  midnight: WARM_TITANIUM,
  royal: MOON_WHITE,
}

export function gameThemeMaterials(theme: ThemeName): GameThemeMaterials {
  return GAME_THEME_MATERIALS[theme]
}
