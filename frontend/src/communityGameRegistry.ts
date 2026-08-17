import { defineAsyncComponent, h, type Component } from 'vue'
import type {
  BuiltinGameArtwork,
  GameAvailability,
  GameRegistration,
} from './game-platform/types'
import { createScoredGameRecords } from './game-platform/recordFormatting'
import { GENERATED_COMMUNITY_GAME_MODULES } from './generated/communityGameModules'
import type { PluginArcadeGameKey } from './types/arcade'

export interface CommunityGameManifest {
  $schema?: string
  apiVersion: 1
  version: string
  author: string
  license: string
  id: PluginArcadeGameKey
  name: string
  description: string
  category: string
  tone: string
  roomLayout?: 'standard' | 'wide' | 'immersive'
  players: {
    min: number
    max: number
    label?: string
  }
  capabilities: {
    guests: boolean
    spectators: boolean
    spectatorFrames: boolean
    firstPlayer: boolean
    undoActions: readonly string[]
    drawRequests: boolean
    replay: boolean
    ai: boolean
  }
  records: {
    scoreKind: 'outcome' | 'time_trial' | 'high_score'
  }
  defaultOptions?: Record<string, unknown>
  ruleLabels?: readonly string[]
}

type PluginViewModule = { default: Component }
export interface GeneratedPluginModule {
  directory: string
  status: GameAvailability
  order: number
  artwork?: BuiltinGameArtwork
  manifest: CommunityGameManifest
  loadView: () => Promise<PluginViewModule>
}

function defaultRules(manifest: CommunityGameManifest): Record<string, unknown> {
  const defaults: Record<string, unknown> = {
    allowSpectators: manifest.capabilities.spectators,
  }
  if (manifest.players.max > 1 && manifest.capabilities.guests) {
    defaults.allowGuests = true
  }
  if (manifest.players.max > 1 && manifest.capabilities.firstPlayer) {
    defaults.firstPlayer = 'random'
  }
  if (manifest.capabilities.undoActions.length) defaults.allowUndo = true
  if (manifest.capabilities.drawRequests) defaults.allowDraw = true
  return { ...defaults, ...(manifest.defaultOptions ?? {}) }
}

function ruleLabels(
  manifest: CommunityGameManifest,
  options: Readonly<Record<string, unknown>>,
): string[] {
  const labels = [...(manifest.ruleLabels ?? [])]
  if (manifest.players.max > 1 && manifest.capabilities.guests) {
    labels.push(options.allowGuests ? '允许游客' : '仅登录玩家')
  }
  return labels
}

export function buildCommunityGameRegistration(
  generated: GeneratedPluginModule,
): GameRegistration<PluginArcadeGameKey> {
  const { artwork, directory, manifest, order, status } = generated
  const component = defineAsyncComponent({
    loader: async () => (await generated.loadView()).default,
    errorComponent: {
      setup: () => () => h(
        'section',
        { class: 'surface plugin-game-load-error', role: 'alert' },
        '社区游戏界面加载失败，请联系插件作者。',
      ),
    },
  })
  const records = manifest.records.scoreKind === 'outcome'
    ? { scoreKind: 'outcome' as const }
    : createScoredGameRecords(manifest.records.scoreKind, manifest.name)
  return Object.freeze({
    key: manifest.id,
    source: 'community',
    availability: status,
    plugin: Object.freeze({
      version: manifest.version,
      author: manifest.author,
      license: manifest.license,
      directory,
    }),
    catalog: Object.freeze({
      order,
      name: manifest.name,
      players: Object.freeze({ ...manifest.players }),
      description: manifest.description,
      tone: manifest.tone,
      category: manifest.category,
      artwork: artwork ? Object.freeze({ ...artwork }) : undefined,
    }),
    capabilities: Object.freeze({
      undo: manifest.capabilities.undoActions.length > 0,
      draw: manifest.capabilities.drawRequests,
      guests: manifest.capabilities.guests,
      spectators: manifest.capabilities.spectators,
      spectatorFrames: manifest.capabilities.spectatorFrames,
      firstPlayer: manifest.capabilities.firstPlayer,
      replay: manifest.capabilities.replay,
      ai: manifest.capabilities.ai,
    }),
    presentation: Object.freeze({
      component,
      roomLayout: manifest.roomLayout ?? 'standard',
      skinKind: null,
    }),
    rules: Object.freeze({
      defaults: Object.freeze(defaultRules(manifest)),
      labels: (options: Readonly<Record<string, unknown>>) => (
        ruleLabels(manifest, options)
      ),
    }),
    records: Object.freeze(records),
  })
}

export const COMMUNITY_GAME_REGISTRATIONS = Object.freeze(
  (GENERATED_COMMUNITY_GAME_MODULES as readonly GeneratedPluginModule[])
    .map(buildCommunityGameRegistration),
)
