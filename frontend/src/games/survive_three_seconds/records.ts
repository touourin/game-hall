import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

export const surviveThreeSecondsLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按成功坚持三秒的次数排序，同次数时比较存活率。',
  entryDetail: (entry) => `${entry.games} 次挑战 · ${entry.wins} 次生还`,
  entryScore: (entry) => `${entry.wins} 次`,
  note: '每次挑战都由服务器重放 180 帧方向输入后判定结果。',
}

export const surviveThreeSecondsStats: BuiltinGameStatsPresentation = {
  description: '记录每次三秒弹幕挑战的存活与碰撞结果。',
  summaryItems: (summary) => [
    { value: summary.games, label: '挑战次数' },
    { value: summary.wins, label: '成功生还' },
    { value: `${summary.winRate}%`, label: '三秒存活率' },
  ],
  historyOutcome: (match) => match.outcome === 'win' ? '生' : '中',
  historyTitle: (match) => match.outcome === 'win' ? '坚持 3.00 秒' : match.reason,
  historyMeta: (_match, date) => `${date} · 180 帧轨迹已校验`,
  detailWinnerLabel: (match) => match.winner === 'survived'
    ? '坚持三秒成功'
    : '被弹幕击中',
  detailNote: (match) => match.ranked
    ? '本次轨迹验证结果计入坚持三秒排行榜'
    : '本次挑战不计排行榜',
}
