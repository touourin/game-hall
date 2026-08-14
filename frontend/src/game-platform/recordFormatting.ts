import type {
  MatchDetail,
  MatchHistoryItem,
  StatsSummary,
} from '../stats'
import type { BuiltinGameStatsPresentation } from './types'

export function formatRecordDuration(milliseconds: number | null | undefined): string {
  if (milliseconds === null || milliseconds === undefined) return '—'
  const seconds = Math.floor(milliseconds / 1000)
  const tenths = Math.floor(milliseconds % 1000 / 100)
  return `${seconds}.${tenths} 秒`
}

export function formatMatchDuration(milliseconds: number | null | undefined): string {
  if (milliseconds === null || milliseconds === undefined) return '—'
  const totalSeconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return minutes
    ? `${minutes} 分 ${seconds} 秒`
    : `${seconds}.${Math.floor(milliseconds % 1000 / 100)} 秒`
}

export function difficultyRecordLabel(value: string | undefined): string {
  if (value === 'expert') return '高级'
  if (value === 'intermediate') return '中级'
  if (value === 'beginner') return '初级'
  return ''
}

export function tetrisRecordModeLabel(value: string | undefined): string {
  if (value?.startsWith('timed_')) {
    return `${Number(value.slice(6)) / 60} 分钟限时`
  }
  return '无限挑战'
}

export interface CompetitiveStatsOptions {
  roleLabels?: Readonly<Record<string, string>>
  winnerLabel?: (match: MatchDetail, roleLabel: (role: string) => string) => string
  detailModeLabel?: (match: MatchDetail) => string
  showDrawSummary?: boolean
}

export function createCompetitiveStatsPresentation(
  options: CompetitiveStatsOptions = {},
): BuiltinGameStatsPresentation {
  const roleLabel = (role: string) => options.roleLabels?.[role] ?? role

  return {
    description: '每款游戏独立记录胜负，对局详情绑定当前账号。',
    summaryItems: (summary: StatsSummary) => [
      { value: summary.games, label: '总场次' },
      { value: summary.wins, label: '胜场' },
      { value: `${summary.winRate}%`, label: '胜率' },
    ],
    showDrawSummary: options.showDrawSummary,
    historyOutcome: standardOutcomeLabel,
    historyTitle: (match: MatchHistoryItem) =>
      `${match.gameName} · ${roleLabel(match.role)}`,
    historyMeta: (match: MatchHistoryItem, formattedDate: string) =>
      `${formattedDate} · ${match.playerCount} 人 · 房间 ${match.roomCode}`,
    detailPlayerRoleLabel: options.roleLabels ? roleLabel : undefined,
    detailModeLabel: options.detailModeLabel,
    detailWinnerLabel: (match: MatchDetail) => {
      if (match.winner === 'draw') return '双方和棋'
      return options.winnerLabel?.(match, roleLabel)
        ?? `${roleLabel(match.winner)}获胜`
    },
    detailNote: (match: MatchDetail) =>
      match.ranked ? '本局计入排行榜' : '本局含 AI，不计排行榜',
  }
}

export function standardOutcomeLabel(match: MatchHistoryItem): string {
  if (match.outcome === 'draw') return '和'
  if (match.outcome === 'completed') return '测'
  return match.outcome === 'win' ? '胜' : '负'
}
