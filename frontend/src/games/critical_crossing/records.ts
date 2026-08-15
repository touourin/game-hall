import { formatMatchDuration } from '../../game-platform/recordFormatting'
import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

const filters = [
  { label: '5 秒 · 校准', mode: '5s' },
  { label: '8 秒 · 过载', mode: '8s' },
  { label: '10 秒 · 临界', mode: '10s' },
] as const

export function crossingDifficultyLabel(mode: unknown): string {
  if (mode === '10s') return '10 秒临界'
  if (mode === '8s') return '8 秒过载'
  return '5 秒校准'
}

export const criticalCrossingLeaderboard: BuiltinGameLeaderboardPresentation = {
  defaultMode: '5s',
  titleSuffix: mode => crossingDifficultyLabel(mode),
  description: '三档目标时间独立排名，按成功穿越次数与完成率排序。',
  filters,
  entryDetail: entry => `${entry.games} 次挑战 · ${entry.wins} 次穿越`,
  entryScore: entry => `${entry.wins} 次`,
  note: '每次挑战均由服务器按相同种子重放完整方向输入。',
}

export const criticalCrossingStats: BuiltinGameStatsPresentation = {
  defaultMode: '5s',
  titleSuffix: mode => crossingDifficultyLabel(mode),
  description: '分别记录 5、8、10 秒挑战的穿越与碰撞结果。',
  filters,
  summaryItems: summary => [
    { value: summary.games, label: '挑战次数' },
    { value: summary.wins, label: '成功穿越' },
    { value: `${summary.winRate}%`, label: '穿越率' },
  ],
  historyOutcome: match => match.outcome === 'win' ? '越' : '断',
  historyTitle: match => match.outcome === 'win'
    ? `${crossingDifficultyLabel(match.gameMode)}完成`
    : match.reason,
  historyMeta: (match, date) => `${date} · ${crossingDifficultyLabel(match.gameMode)}`,
  detailSection: (match) => {
    const state = match.details.state
    const crossed = match.winner === 'crossed'
    const collision = state?.collision_kind === 'boundary'
      ? '边界封锁'
      : '脉冲屏障'
    return {
      title: '临界穿越成绩',
      metrics: [
        {
          status: crossed ? 'success' : 'failed',
          label: crossed ? '完整穿越' : collision,
          value: formatMatchDuration(state?.elapsed_ms),
          note: `目标 ${formatMatchDuration(state?.duration_ms)} · ${state?.pulse_count ?? 0} 轮脉冲`,
        },
        {
          status: 'success',
          label: '服务端轨迹校验',
          value: `${state?.input_count ?? 0} 帧输入`,
          note: '同种子重建脉冲位置、缺口与边界压力',
        },
      ],
    }
  },
  detailWinnerLabel: match => match.winner === 'crossed'
    ? '临界穿越完成'
    : '穿越中断',
  detailNote: match => match.ranked
    ? `本次结果计入${crossingDifficultyLabel(match.gameMode)}排行榜`
    : '本次挑战不计排行榜',
}
