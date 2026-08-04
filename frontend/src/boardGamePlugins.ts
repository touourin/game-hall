export type BoardGamePluginTone = 'amber' | 'coral' | 'forest' | 'ocean' | 'violet'

/**
 * A board-game plugin owns its rules, room route, and game UI. Registering it
 * here makes it appear automatically in the board-game collection.
 */
export interface BoardGamePlugin {
  key: string
  name: string
  players: string
  description: string
  category: string
  tone: BoardGamePluginTone
  mark: string
  entryPath: string
}

// Board-game plugins are intentionally separate from the existing arcade games.
export const BOARD_GAME_PLUGINS: readonly BoardGamePlugin[] = []
