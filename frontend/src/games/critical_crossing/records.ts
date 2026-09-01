import { formatMatchDuration } from '../../game-platform/recordFormatting'
import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

const filters = [
  { label: '5 秒 · 校准', mode: '5s' },
  { label: '8 秒 · 疾行', mode: '8s' },
  { label: '10 秒 · 极限', mode: '10s' },
] as const

export function crossingDifficultyLabel(mode: unknown): string {
  if (mode === '10s') return '10 秒极限'
  if (mode === '8s') return '8 秒疾行'
  return '5 秒校准'
}

export const criticalCrossingLeaderboard: BuiltinGameLeaderboardPresentation = {
  defaultMode: '5s',
  titleSuffix: mode => ` · ${crossingDifficultyLabel(mode)}`,
  description: '三档云桥长度独立排名，按成功疾行次数与完成率排序。',
  filters,
  entryDetail: entry => `${entry.games} 次挑战 · ${entry.wins} 次完赛`,
  entryScore: entry => `${entry.wins} 次`,
  note: '每次挑战均由服务器按相同种子重放变道、跳跃与下蹲输入。',
}

export const criticalCrossingStats: BuiltinGameStatsPresentation = {
  defaultMode: '5s',
  titleSuffix: mode => ` · ${crossingDifficultyLabel(mode)}`,
  description: '分别记录 5、8、10 秒挑战的疾行距离与碰撞结果。',
  filters,
  summaryItems: summary => [
    { value: summary.games, label: '挑战次数' },
    { value: summary.wins, label: '成功完赛' },
    { value: `${summary.winRate}%`, label: '完赛率' },
  ],
  historyOutcome: match => match.outcome === 'win' ? '达' : '撞',
  historyTitle: match => match.outcome === 'win'
    ? `${crossingDifficultyLabel(match.gameMode)}完成`
    : match.reason,
  historyMeta: (match, date) => `${date} · ${crossingDifficultyLabel(match.gameMode)}`,
  detailSection: (match) => {
    const state = match.details.state
    const crossed = match.winner === 'crossed'
    const collision = ({
      gap: '断桥缺口',
      barrier: '封路护栏',
      ground: '地面障碍',
      overhead: '上方障碍',
    } as Record<string, string>)[String(state?.collision_kind)] ?? '赛道障碍'
    return {
      title: '算途疾行成绩',
      metrics: [
        {
          status: crossed ? 'success' : 'failed',
          label: crossed ? '完整完赛' : collision,
          value: `${state?.distance_meters ?? 0} 米`,
          note: `用时 ${formatMatchDuration(state?.elapsed_ms)} · 通过 ${state?.passed_sections ?? 0}/${state?.section_count ?? state?.pulse_count ?? 0} 段`,
        },
        {
          status: 'success',
          label: '服务端轨迹校验',
          value: `${state?.input_count ?? 0} 帧输入`,
          note: '同种子重建两路/三路分叉、障碍和人物动作',
        },
      ],
    }
  },
  detailWinnerLabel: match => match.winner === 'crossed'
    ? '算途疾行完成'
    : '疾行中断',
  detailNote: match => match.ranked
    ? `本次结果计入${crossingDifficultyLabel(match.gameMode)}排行榜`
    : '本次挑战不计排行榜',
}
