import type {
  MatchDetail,
  MatchHistoryItem,
  StatsSummary,
} from '../stats'
import type {
  BuiltinGameRecords,
  BuiltinGameStatsPresentation,
} from './types'

export function formatRecordDuration(milliseconds: number | null | undefined): string {
  if (!isValidMetric(milliseconds)) return '—'
  const seconds = Math.floor(milliseconds / 1000)
  const tenths = Math.floor(milliseconds % 1000 / 100)
  return `${seconds}.${tenths} 秒`
}

export function formatMatchDuration(milliseconds: number | null | undefined): string {
  if (!isValidMetric(milliseconds)) return '—'
  const totalSeconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return minutes
    ? `${minutes} 分 ${seconds} 秒`
    : `${seconds}.${Math.floor(milliseconds % 1000 / 100)} 秒`
}

function isValidMetric(value: number | null | undefined): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0
}

export function formatRecordNumber(
  value: number | null | undefined,
  unit = '',
  maximumFractionDigits = 0,
): string {
  if (!isValidMetric(value)) return '—'
  const fractionDigits = Number.isFinite(maximumFractionDigits)
    ? Math.min(20, Math.max(0, Math.trunc(maximumFractionDigits)))
    : 0
  const formatted = value.toLocaleString('zh-CN', {
    maximumFractionDigits: fractionDigits,
  })
  return unit ? `${formatted} ${unit}` : formatted
}

export function difficultyRecordLabel(value: string | undefined): string {
  if (value === 'expert') return '高级'
  if (value === 'intermediate') return '中级'
  return '初级'
}

export function tetrisRecordModeLabel(value: string | undefined): string {
  if (value?.startsWith('timed_')) {
    const durationSeconds = Number(value.slice(6))
    if ([60, 180, 300].includes(durationSeconds)) {
      return `${durationSeconds / 60} 分钟限时`
    }
    return '未知限时模式'
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

export function createScoredGameRecords(
  scoreKind: 'time_trial' | 'high_score' | 'ranking',
  gameName: string,
): BuiltinGameRecords {
  if (scoreKind === 'ranking') {
    const points = (value: number | null | undefined) => (
      typeof value === 'number' && Number.isFinite(value)
        ? `${value > 0 ? '+' : ''}${value.toLocaleString('zh-CN')} 分`
        : '—'
    )
    return {
      scoreKind,
      leaderboard: {
        description: '按累计名次积分排序；同分依次比较冠军次数、夺冠率、场次和注册时间。',
        entryDetail: (entry) => `${entry.games} 局 · ${entry.wins} 次冠军`,
        entryScore: (entry) => points(entry.totalPoints),
        note: '积分可为负数；只累计已结束且符合战绩条件的对局。',
      },
      stats: {
        description: `记录${gameName}每局名次与积分变化。`,
        summaryItems: (summary) => [
          { value: summary.games, label: '总场次' },
          { value: points(summary.totalPoints), label: '累计积分' },
          { value: summary.wins, label: '冠军次数' },
        ],
        historyOutcome: () => '分',
        historyTitle: (match) => `${gameName} · ${match.role} · ${points(match.scoreValue)}`,
        historyMeta: (match, date) => `${date} · ${match.playerCount} 人 · 房间 ${match.roomCode}`,
        detailPlayerRoleLabel: (role) => role,
        detailSection: (match) => ({
          title: '名次积分',
          metrics: match.details.players.map((player) => ({
            status: (player.scoreValue ?? 0) >= 0 ? 'success' : 'failed',
            label: `${player.name} · ${player.role ?? '玩家'}`,
            value: points(player.scoreValue),
          })),
        }),
        detailWinnerLabel: () => `${gameName}名次已结算`,
        detailNote: (match) => match.ranked ? '本局名次积分计入排行榜' : '本局不计排行榜',
      },
    }
  }
  if (scoreKind === 'time_trial') {
    return {
      scoreKind,
      leaderboard: {
        description: '按个人历史最佳完成时间排序，用时越短排名越前。',
        entryDetail: (entry) => (
          `${entry.games} 次挑战 · 平均 ${formatMatchDuration(entry.averageMs)}`
        ),
        entryScore: (entry) => formatMatchDuration(entry.bestMs),
        note: '只有完整完成并通过服务端校验的挑战才会记录时间。',
      },
      stats: {
        description: `记录每次${gameName}挑战的完成时间。`,
        summaryItems: (summary) => [
          { value: summary.games, label: '挑战次数' },
          { value: formatMatchDuration(summary.bestMs), label: '历史最佳' },
          { value: formatMatchDuration(summary.averageMs), label: '平均用时' },
        ],
        historyOutcome: () => '时',
        historyTitle: (match) => `${gameName} · ${formatMatchDuration(match.scoreMs)}`,
        historyMeta: (_match, date) => `${date} · 计时挑战`,
        detailWinnerLabel: () => `${gameName}挑战完成`,
        detailNote: (match) => match.ranked
          ? '本次时间计入排行榜'
          : '本次时间不计排行榜',
      },
    }
  }
  return {
    scoreKind,
    leaderboard: {
      description: '按个人历史最高分排序，分数越高排名越前。',
      entryDetail: (entry) => (
        `${entry.games} 次挑战 · 平均 ${formatRecordNumber(entry.averageScore, '分')}`
      ),
      entryScore: (entry) => formatRecordNumber(entry.bestScore, '分'),
      note: '只有完整结束并通过服务端校验的挑战才会记录分数。',
    },
    stats: {
      description: `记录每次${gameName}挑战的服务端结算分数。`,
      summaryItems: (summary) => [
        { value: summary.games, label: '挑战次数' },
        { value: formatRecordNumber(summary.bestScore), label: '历史最高' },
        { value: formatRecordNumber(summary.averageScore), label: '平均分数' },
      ],
      historyOutcome: () => '分',
      historyTitle: (match) => (
        `${gameName} · ${formatRecordNumber(match.scoreValue, '分')}`
      ),
      historyMeta: (_match, date) => `${date} · 高分挑战`,
      detailWinnerLabel: () => `${gameName}挑战结束`,
      detailNote: (match) => match.ranked
        ? '本次分数计入排行榜'
        : '本次分数不计排行榜',
    },
  }
}
