import type { BuiltinGameLeaderboardPresentation } from '../../game-platform/types'
import type { BuiltinGameStatsPresentation } from '../../game-platform/types'
import StatsSummary from './StatsSummary.vue'

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

const roleLabels: Record<string, string> = {
  merlin: '梅林',
  percival: '派西维尔',
  loyal_servant: '亚瑟的忠臣',
  dissenting_courtier: '心怀异念之臣',
  shadow_merlin: '暗影梅林',
  assassin: '刺客',
  morgana: '莫甘娜',
  mordred: '莫德雷德',
  oberon: '奥伯伦',
  minion: '莫德雷德的爪牙',
}

export const avalonStats: BuiltinGameStatsPresentation = {
  defaultMode: 'standard',
  defaultVariant: (mode) => mode === 'court_undercurrent' ? 'classic' : undefined,
  titleSuffix: (mode, variant) => ` · ${avalonModeLabel(mode, variant)}`,
  description: '每款游戏独立记录胜负，对局详情绑定当前账号。',
  filters: avalonLeaderboard.filters,
  summaryItems: (summary) => [
    { value: summary.games, label: '总场次' },
    { value: summary.wins, label: '胜场' },
    { value: `${summary.winRate}%`, label: '胜率' },
  ],
  summaryComponent: StatsSummary,
  historyOutcome: (match) => match.outcome === 'win' ? '胜' : '负',
  historyTitle: (match) =>
    `${roleLabels[match.role] ?? match.role} · ${match.alignment === 'good' ? '好人' : '坏人'}`,
  historyMeta: (match, date) =>
    `${date} · ${avalonModeLabel(match.gameMode ?? undefined, undefined)} · ${match.playerCount} 人 · 房间 ${match.roomCode}`,
  detailModeLabel: (match) => avalonModeLabel(
    match.gameMode ?? match.details.mode,
    match.details.shadowMerlinEnabled ? 'shadow_merlin' : 'classic',
  ),
  detailWinnerLabel: (match) => match.winner === 'good' ? '好人获胜' : '坏人获胜',
  detailNote: (match) => match.ranked
    ? '本局计入排行榜'
    : '本局含 AI，不计排行榜',
}
