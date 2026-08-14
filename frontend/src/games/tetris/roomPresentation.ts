import type { BuiltinGameRoomShellPresentation } from '../../game-platform/types'

export const tetrisRoomShell: BuiltinGameRoomShellPresentation = {
  headerEyebrowSuffix: (snapshot) => snapshot.options.challengeMode === 'endless'
    ? ' · 无限高分挑战'
    : ` · ${Number(snapshot.options.durationSeconds ?? 180) / 60} 分钟限时`,
  headerTitle: () => '落块挑战',
  statsMode: (snapshot) => snapshot.options.challengeMode === 'endless'
    ? 'standard'
    : `timed_${Number(snapshot.options.durationSeconds ?? 180)}`,
}
