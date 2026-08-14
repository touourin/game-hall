import type { BuiltinGameRoomShellPresentation } from '../../game-platform/types'

export const pokerRoomShell: BuiltinGameRoomShellPresentation = {
  activeExitDescription: '暂时返回会保留座位和筹码；退出并淘汰将放弃本桌，而且无法再返回。',
  abandonLabel: '退出并淘汰',
  finishedLabel: '本桌结束',
  rematchLabel: '准备重新开桌',
}
