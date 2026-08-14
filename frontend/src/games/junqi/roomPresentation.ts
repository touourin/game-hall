import type { BuiltinGameRoomShellPresentation } from '../../game-platform/types'

export const junqiRoomShell: BuiltinGameRoomShellPresentation = {
  headerEyebrowSuffix: (snapshot) =>
    ` · ${snapshot.options.mode === 'flip' ? '翻棋军旗' : '暗军旗'}`,
}
