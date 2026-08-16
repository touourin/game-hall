import { computed } from 'vue'
import {
  GAME_THEME_MATERIALS,
  type GameThemeMaterials,
} from '../game-platform/presentation/gameThemeMaterials'
import { currentTheme } from '../theme'
import type { PluginThemeMaterials, PluginThemeName } from './types'

function freezeMaterials(materials: GameThemeMaterials): PluginThemeMaterials {
  return Object.freeze({
    scene: Object.freeze({ ...materials.scene }),
    stage: Object.freeze({ ...materials.stage }),
    metal: Object.freeze({ ...materials.metal }),
    copy: Object.freeze({ ...materials.copy }),
    semantic: Object.freeze({ ...materials.semantic }),
  })
}

const PUBLIC_THEME_MATERIALS: Readonly<Record<PluginThemeName, PluginThemeMaterials>> = Object.freeze({
  emerald: freezeMaterials(GAME_THEME_MATERIALS.emerald),
  midnight: freezeMaterials(GAME_THEME_MATERIALS.midnight),
  royal: freezeMaterials(GAME_THEME_MATERIALS.royal),
  amber: freezeMaterials(GAME_THEME_MATERIALS.amber),
})

export function pluginThemeMaterials(theme: PluginThemeName): PluginThemeMaterials {
  return PUBLIC_THEME_MATERIALS[theme]
}

export function usePluginTheme() {
  const theme = computed<PluginThemeName>(() => currentTheme.value)
  const materials = computed(() => pluginThemeMaterials(theme.value))

  return { theme, materials }
}
