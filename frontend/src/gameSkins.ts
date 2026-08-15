import type { ArcadeGameKey } from './types/arcade'
import { gameRegistration } from './game-platform/registry'

export type GameSkinId =
  | 'classic-wood'
  | 'ink-wash'
  | 'jade-court'
  | 'midnight-neon'
  | 'celestial-gold'

export type GameSkinTier = '初级' | '中级' | '高级'
export type GameSkinKind = 'board' | 'cards'
export type GameSkinCssVariables = Record<`--game-${string}`, string>

interface GameSkin {
  id: GameSkinId
  name: string
  description: string
  tier: GameSkinTier
  css: GameSkinCssVariables
}

export const GAME_SKIN_STORAGE_KEY = 'game-hall:game-skin'

export const GAME_SKINS: GameSkin[] = [
  {
    id: 'classic-wood',
    name: '原木经典',
    description: '暖木棋盘与传统绿毡牌桌',
    tier: '初级',
    css: {
      '--game-board-surface': '#d5a45d',
      '--game-board-texture': 'linear-gradient(rgba(255,255,255,.05), rgba(98,53,18,.04)), repeating-linear-gradient(90deg, transparent 0 31px, rgba(88,47,17,.035) 32px)',
      '--game-board-frame': '#7b4a20',
      '--game-board-highlight': 'rgba(255,221,151,.42)',
      '--game-board-line': '#65401f',
      '--game-board-label': '#603b1d',
      '--game-piece-surface': 'radial-gradient(circle at 36% 28%, #fff1c8, #efd398 36%, #bd7d35 82%)',
      '--game-piece-rim': '#edc77d',
      '--game-black-stone': 'radial-gradient(circle at 35% 30%, #555, #080808 68%)',
      '--game-white-stone': 'radial-gradient(circle at 35% 30%, #fff, #d7d2c8 70%)',
      '--game-white-stone-border': 'rgba(76,56,32,.22)',
      '--game-felt-surface': 'radial-gradient(ellipse at 50% 42%, #176348 0%, #0d4b38 62%, #08382d 100%)',
      '--game-felt-border': '#5d351d',
      '--game-felt-highlight': '#bc8650',
      '--game-seat-surface': 'rgba(6,46,39,.9)',
      '--game-card-face': 'linear-gradient(145deg, #fffdf6, #ddd9cc)',
      '--game-card-border': '#d8d4c6',
      '--game-card-back': 'repeating-linear-gradient(45deg, #243d55 0 6px, #172c42 6px 12px)',
      '--game-card-back-accent': '#e8c978',
    },
  },
  {
    id: 'ink-wash',
    name: '水墨云笺',
    description: '宣纸肌理与克制的墨色层次',
    tier: '中级',
    css: {
      '--game-board-surface': '#d8d3c3',
      '--game-board-texture': 'radial-gradient(circle at 17% 22%, rgba(55,70,67,.12), transparent 25%), radial-gradient(circle at 82% 72%, rgba(63,79,75,.1), transparent 30%), repeating-linear-gradient(8deg, rgba(255,255,255,.08) 0 1px, transparent 1px 7px)',
      '--game-board-frame': '#303936',
      '--game-board-highlight': 'rgba(230,239,230,.42)',
      '--game-board-line': '#46534f',
      '--game-board-label': '#34423e',
      '--game-piece-surface': 'radial-gradient(circle at 36% 28%, #fffdf5, #d8d3c3 45%, #8e9992 86%)',
      '--game-piece-rim': '#b9c1ba',
      '--game-black-stone': 'radial-gradient(circle at 35% 30%, #4e5b58, #101716 70%)',
      '--game-white-stone': 'radial-gradient(circle at 35% 30%, #fffef7, #c9cec7 72%)',
      '--game-white-stone-border': 'rgba(44,62,57,.28)',
      '--game-felt-surface': 'radial-gradient(ellipse at 48% 38%, #3c504b 0%, #243c39 58%, #152c2a 100%)',
      '--game-felt-border': '#242c2a',
      '--game-felt-highlight': '#89958e',
      '--game-seat-surface': 'rgba(24,41,39,.92)',
      '--game-card-face': 'linear-gradient(145deg, #faf8ee, #d8d8ce)',
      '--game-card-border': '#b7bcb5',
      '--game-card-back': 'repeating-linear-gradient(135deg, #41514e 0 5px, #253532 5px 10px)',
      '--game-card-back-accent': '#d7ded5',
    },
  },
  {
    id: 'jade-court',
    name: '翡翠王庭',
    description: '青玉台面与温润金边细节',
    tier: '中级',
    css: {
      '--game-board-surface': '#7ea58e',
      '--game-board-texture': 'radial-gradient(circle at 22% 18%, rgba(220,255,230,.2), transparent 28%), radial-gradient(circle at 78% 76%, rgba(11,70,53,.2), transparent 34%), repeating-linear-gradient(118deg, transparent 0 24px, rgba(226,255,235,.035) 25px 26px)',
      '--game-board-frame': '#214f40',
      '--game-board-highlight': 'rgba(216,190,117,.62)',
      '--game-board-line': '#244c3d',
      '--game-board-label': '#163d31',
      '--game-piece-surface': 'radial-gradient(circle at 36% 28%, #fffbe7, #e5d4a6 46%, #9b7841 86%)',
      '--game-piece-rim': '#e3ca83',
      '--game-black-stone': 'radial-gradient(circle at 35% 30%, #365b50, #071b15 70%)',
      '--game-white-stone': 'radial-gradient(circle at 35% 30%, #fffde9, #d5d5bd 72%)',
      '--game-white-stone-border': 'rgba(22,62,49,.3)',
      '--game-felt-surface': 'radial-gradient(ellipse at 50% 40%, #178166 0%, #0d5a48 58%, #06382e 100%)',
      '--game-felt-border': '#173e33',
      '--game-felt-highlight': '#d6b862',
      '--game-seat-surface': 'rgba(7,55,44,.9)',
      '--game-card-face': 'linear-gradient(145deg, #fffbe8, #e3d7b8)',
      '--game-card-border': '#d4bc77',
      '--game-card-back': 'repeating-linear-gradient(45deg, #1c6b58 0 5px, #10483c 5px 10px)',
      '--game-card-back-accent': '#f0d57c',
    },
  },
  {
    id: 'midnight-neon',
    name: '霓虹夜局',
    description: '深蓝金属与电光青紫氛围',
    tier: '中级',
    css: {
      '--game-board-surface': '#27344e',
      '--game-board-texture': 'linear-gradient(135deg, rgba(78,230,255,.08), transparent 35%), radial-gradient(circle at 78% 78%, rgba(173,83,255,.14), transparent 36%), repeating-linear-gradient(90deg, transparent 0 27px, rgba(120,173,255,.025) 28px)',
      '--game-board-frame': '#0e1728',
      '--game-board-highlight': 'rgba(74,225,255,.58)',
      '--game-board-line': '#7b91ba',
      '--game-board-label': '#b5caf4',
      '--game-piece-surface': 'radial-gradient(circle at 36% 28%, #eef9ff, #91a9cb 46%, #30415e 88%)',
      '--game-piece-rim': '#71d8ef',
      '--game-black-stone': 'radial-gradient(circle at 35% 30%, #445b7a, #050916 70%)',
      '--game-white-stone': 'radial-gradient(circle at 35% 30%, #ecfbff, #86b6cc 72%)',
      '--game-white-stone-border': 'rgba(96,231,255,.36)',
      '--game-felt-surface': 'radial-gradient(ellipse at 46% 38%, #263d67 0%, #172747 56%, #0b1329 100%)',
      '--game-felt-border': '#11192c',
      '--game-felt-highlight': '#46dff2',
      '--game-seat-surface': 'rgba(12,21,44,.92)',
      '--game-card-face': 'linear-gradient(145deg, #f3fbff, #b9c8df)',
      '--game-card-border': '#69cde2',
      '--game-card-back': 'repeating-linear-gradient(135deg, #512f76 0 5px, #182f5e 5px 10px)',
      '--game-card-back-accent': '#76e9ff',
    },
  },
  {
    id: 'celestial-gold',
    name: '星穹鎏金',
    description: '曜石星芒与高级鎏金纹饰',
    tier: '高级',
    css: {
      '--game-board-surface': '#443251',
      '--game-board-texture': 'radial-gradient(circle at 18% 24%, rgba(255,224,151,.18) 0 1px, transparent 2px), radial-gradient(circle at 72% 31%, rgba(255,244,201,.14) 0 1px, transparent 2px), radial-gradient(circle at 55% 80%, rgba(167,129,255,.2), transparent 34%), linear-gradient(135deg, rgba(255,218,132,.06), transparent 45%)',
      '--game-board-frame': '#24162d',
      '--game-board-highlight': 'rgba(255,221,135,.82)',
      '--game-board-line': '#cbb274',
      '--game-board-label': '#ffe4a3',
      '--game-piece-surface': 'radial-gradient(circle at 36% 28%, #fff8d8, #dabb75 44%, #6e4a37 88%)',
      '--game-piece-rim': '#ffdc85',
      '--game-black-stone': 'radial-gradient(circle at 35% 30%, #5f4d6d, #110c18 70%)',
      '--game-white-stone': 'radial-gradient(circle at 35% 30%, #fff9da, #d7bd84 72%)',
      '--game-white-stone-border': 'rgba(255,219,132,.42)',
      '--game-felt-surface': 'radial-gradient(ellipse at 48% 38%, #4c315c 0%, #2e1e41 57%, #140f24 100%)',
      '--game-felt-border': '#1b1125',
      '--game-felt-highlight': '#e3bd64',
      '--game-seat-surface': 'rgba(30,18,43,.92)',
      '--game-card-face': 'linear-gradient(145deg, #fff9e3, #dbc590)',
      '--game-card-border': '#e6c36d',
      '--game-card-back': 'repeating-linear-gradient(45deg, #68427f 0 5px, #351f4f 5px 10px)',
      '--game-card-back-accent': '#ffe096',
    },
  },
]

function isGameSkinId(value: string | null): value is GameSkinId {
  return GAME_SKINS.some((skin) => skin.id === value)
}

export function gameSkinKind(gameKey: ArcadeGameKey): GameSkinKind | null {
  const skinKind = gameRegistration(gameKey)?.presentation.skinKind
  if (skinKind) return skinKind
  return null
}

export function storedGameSkin(): GameSkinId {
  const saved = localStorage.getItem(GAME_SKIN_STORAGE_KEY)
  return isGameSkinId(saved) ? saved : 'classic-wood'
}

export function rememberGameSkin(skin: GameSkinId): void {
  localStorage.setItem(GAME_SKIN_STORAGE_KEY, skin)
}

export function gameSkinCssVariables(skinId: GameSkinId): GameSkinCssVariables {
  return GAME_SKINS.find((skin) => skin.id === skinId)?.css ?? GAME_SKINS[0]!.css
}
