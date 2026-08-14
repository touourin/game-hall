import type { BuiltinGameRoomShellPresentation } from '../../game-platform/types'

export const minesweeperRoomShell: BuiltinGameRoomShellPresentation = {
  headerEyebrowSuffix: (snapshot) => ` · ${snapshot.game.difficultyLabel}`,
  headerTitle: () => '扫雷挑战',
  statsMode: (snapshot) => String(snapshot.options.difficulty ?? 'beginner'),
}
