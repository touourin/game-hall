import { useArcadeStore } from './stores/arcade'

export type { ArcadeSnapshot } from './types/arcade'

export function usePluginGameActions() {
  const arcade = useArcadeStore()
  return {
    action: arcade.actionWithResult,
    rapidAction: arcade.rapidAction,
    restart: arcade.restartGame,
  }
}
