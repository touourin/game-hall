import { defineAsyncComponent } from 'vue'
import type { BuiltinGameRoomShellPresentation } from '../../game-platform/types'
import { isAvalonArcadeSnapshot } from './types'

const phaseLabels: Record<string, string> = {
  lobby: '等待玩家集结',
  role_reveal: '确认身份',
  team_building: '组建任务队伍',
  team_voting: '表决任务队伍',
  mission_voting: '执行秘密任务',
  round_result: '任务结算',
  lady_select: '湖中仙女',
  lady_reveal: '仙女启示',
  assassination: '最后刺杀',
  dagger_grant: '黑誓授刃',
  final_council: '最后议事',
  exile_council_ballot: '祓影议庭锁票',
  exile_council_assassination_decision: '祓影议庭',
  exile_council_assassination_target: '暗刃刺杀',
  game_over: '本局终章',
}

export const avalonRoomShell: BuiltinGameRoomShellPresentation = {
  headerDetailsComponent: defineAsyncComponent(
    () => import('./AvalonRoomHeaderDetails.vue'),
  ),
  headerActionsComponent: defineAsyncComponent(
    () => import('./AvalonRoomHeaderActions.vue'),
  ),
  lobbyComponent: defineAsyncComponent(
    () => import('./AvalonRoomLobby.vue'),
  ),
  headerEyebrowSuffix: (snapshot) => {
    if (!isAvalonArcadeSnapshot(snapshot)) return ''
    const mode = snapshot.game.settings.mode === 'court_undercurrent'
      ? '王庭暗流'
      : '标准模式'
    return ` · ${mode} · ${phaseLabels[snapshot.game.phase] ?? snapshot.game.phase}`
  },
  waitingMessage: (snapshot) => {
    if (!isAvalonArcadeSnapshot(snapshot)) return null
    if (!snapshot.game.settings.shadowMerlinEnabled || snapshot.players.length >= 6) {
      return null
    }
    return `暗影梅林扩展至少需要 6 名玩家，还需 ${6 - snapshot.players.length} 名`
  },
  handlesResult: true,
}
