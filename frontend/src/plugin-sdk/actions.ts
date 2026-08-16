import { useArcadeStore } from '../stores/arcade'

export interface PluginGameActions {
  action: (
    actionName: string,
    payload?: Record<string, unknown>,
  ) => Promise<boolean>
  rapidAction: (
    actionName: string,
    payload?: Record<string, unknown>,
  ) => Promise<boolean>
  restart: () => Promise<boolean>
  publishSpectatorFrame: (
    sequence: number,
    state: Record<string, unknown>,
  ) => boolean
}

export function usePluginGameActions(): PluginGameActions {
  const arcade = useArcadeStore()
  return {
    action: (actionName, payload) => arcade.actionWithResult(actionName, payload),
    rapidAction: (actionName, payload) => arcade.rapidAction(actionName, payload),
    restart: () => arcade.restartGame(),
    publishSpectatorFrame: (sequence, state) => (
      arcade.publishSpectatorFrame(sequence, state)
    ),
  }
}
