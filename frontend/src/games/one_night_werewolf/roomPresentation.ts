import type { BuiltinGameRoomShellPresentation } from '../../game-platform/types'

const phaseLabels: Record<string, string> = {
  lobby: '等待集结',
  role_reveal: '确认身份',
  night: '秘密夜晚',
  discussion: '晨间讨论',
  voting: '秘密投票',
  finished: '真相揭晓',
}

export const oneNightWerewolfRoomShell: BuiltinGameRoomShellPresentation = {
  headerEyebrowSuffix: (snapshot) =>
    ` · ${phaseLabels[snapshot.phase] ?? snapshot.phase}`,
}
