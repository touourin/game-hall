import type { BuiltinGameRoomShellPresentation } from '../../game-platform/types'

export const departedSuspicionRoomShell: BuiltinGameRoomShellPresentation = {
  headerEyebrowSuffix: (snapshot) =>
    ` · ${snapshot.options.equipmentSet === 'base' ? '基础装备局' : '炸弹客/叛徒装备局'}`,
}
