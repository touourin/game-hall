import { defineAsyncComponent, h, type Component } from 'vue'
import { GENERATED_THIRD_PARTY_GAME_MODULES } from './generated/thirdPartyGameModules'

export interface ThirdPartyGameManifest {
  apiVersion: 1
  enabled: boolean
  id: `plugin-${string}`
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
  defaultOptions?: Record<string, unknown>
  ruleLabels?: string[]
}

export interface ThirdPartyGameDefinition {
  manifest: ThirdPartyGameManifest
  component: Component
}

type PluginViewModule = { default: Component }
interface GeneratedPluginModule {
  directory: string
  manifest: unknown
  loadView: () => Promise<PluginViewModule>
}

export function validateThirdPartyGameManifest(
  candidate: unknown,
  directory: string,
): ThirdPartyGameManifest | null {
  if (!candidate || typeof candidate !== 'object') return null
  const manifest = candidate as Record<string, unknown>
  const players = manifest.players as Record<string, unknown> | undefined
  const id = manifest.id
  if (
    manifest.apiVersion !== 1
    || typeof manifest.enabled !== 'boolean'
    || typeof id !== 'string'
    || !/^plugin-[a-z0-9][a-z0-9-]{0,24}$/.test(id)
    || id !== directory
    || typeof manifest.name !== 'string'
    || !manifest.name.trim()
    || manifest.name.length > 24
    || typeof manifest.description !== 'string'
    || !manifest.description.trim()
    || manifest.description.length > 80
    || typeof manifest.category !== 'string'
    || !manifest.category.trim()
    || manifest.category.length > 16
    || typeof manifest.tone !== 'string'
    || !/^[a-z0-9][a-z0-9-]{0,23}$/.test(manifest.tone)
    || (manifest.roomLayout !== undefined && (
      !['standard', 'wide', 'immersive'].includes(String(manifest.roomLayout))
    ))
    || !players
    || !Number.isInteger(players.min)
    || !Number.isInteger(players.max)
    || Number(players.min) < 1
    || Number(players.max) < Number(players.min)
    || Number(players.max) > 20
    || (players.label !== undefined && (
      typeof players.label !== 'string'
      || !players.label.trim()
      || players.label.length > 16
    ))
    || (manifest.defaultOptions !== undefined && (
      !manifest.defaultOptions
      || typeof manifest.defaultOptions !== 'object'
      || Array.isArray(manifest.defaultOptions)
    ))
    || (manifest.ruleLabels !== undefined && (
      !Array.isArray(manifest.ruleLabels)
      || manifest.ruleLabels.length > 6
      || manifest.ruleLabels.some((label) => (
        typeof label !== 'string' || !label.trim() || label.length > 24
      ))
    ))
  ) return null
  return manifest as unknown as ThirdPartyGameManifest
}

function buildRegistry(): readonly ThirdPartyGameDefinition[] {
  const definitions: ThirdPartyGameDefinition[] = []
  const generatedModules = GENERATED_THIRD_PARTY_GAME_MODULES as readonly GeneratedPluginModule[]
  for (const generated of generatedModules) {
    const { directory } = generated
    const manifest = validateThirdPartyGameManifest(generated.manifest, directory)
    if (!manifest?.enabled) continue
    const component = defineAsyncComponent({
      loader: async () => (await generated.loadView()).default,
      errorComponent: {
        setup: () => () => h(
          'section',
          { class: 'surface plugin-game-load-error', role: 'alert' },
          '第三方游戏界面加载失败，请联系插件作者。',
        ),
      },
    })
    definitions.push({ manifest, component })
  }
  return definitions.sort((left, right) => left.manifest.id.localeCompare(right.manifest.id))
}

export const THIRD_PARTY_GAME_PLUGINS = buildRegistry()

export function thirdPartyGameDefinition(key: unknown): ThirdPartyGameDefinition | null {
  if (typeof key !== 'string') return null
  return THIRD_PARTY_GAME_PLUGINS.find((plugin) => plugin.manifest.id === key) ?? null
}

export function thirdPartyGameComponent(key: unknown): Component | null {
  return thirdPartyGameDefinition(key)?.component ?? null
}

export function thirdPartyGameRoomLayout(
  key: unknown,
): ThirdPartyGameManifest['roomLayout'] {
  return thirdPartyGameDefinition(key)?.manifest.roomLayout ?? 'standard'
}

export function thirdPartyGameDefaultOptions(key: unknown): Record<string, unknown> {
  return { ...(thirdPartyGameDefinition(key)?.manifest.defaultOptions ?? {}) }
}

export function thirdPartyGameRuleLabels(key: unknown): string[] {
  return [...(thirdPartyGameDefinition(key)?.manifest.ruleLabels ?? [])]
}
