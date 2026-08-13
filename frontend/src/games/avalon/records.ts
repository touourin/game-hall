import type { BuiltinGameLeaderboardPresentation } from '../../game-platform/types'

export function avalonModeLabel(
  mode: string | undefined,
  variant: string | undefined,
): string {
  if (mode !== 'court_undercurrent') return '标准模式'
  return variant === 'shadow_merlin'
    ? '王庭暗流 · 暗影梅林'
    : '王庭暗流 · 无暗影梅林'
}

export const avalonLeaderboard: BuiltinGameLeaderboardPresentation = {
  defaultMode: 'standard',
  defaultVariant: (mode) => mode === 'court_undercurrent' ? 'classic' : undefined,
  titleSuffix: (mode, variant) => ` · ${avalonModeLabel(mode, variant)}`,
  description: '按胜场排序，同胜场时依次比较胜率和有效场次。',
  filters: [
    { label: '标准模式', mode: 'standard' },
    { label: '暗流 · 无暗影', mode: 'court_undercurrent', variant: 'classic' },
    { label: '暗流 · 暗影梅林', mode: 'court_undercurrent', variant: 'shadow_merlin' },
  ],
  entryDetail: (entry) =>
    `${entry.wins} 胜${entry.draws ? ` · ${entry.draws} 和` : ''} / ${entry.games} 场`,
  entryScore: (entry) => `${entry.winRate}%`,
  note: '含 AI 的测试局不会计入排行榜。',
}
