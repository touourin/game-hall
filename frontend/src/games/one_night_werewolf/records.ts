import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

const roleLabels = {
  one_night_minion: '爪牙',
  werewolf: '狼人',
  mason: '守夜人',
  seer: '预言家',
  robber: '强盗',
  troublemaker: '捣蛋鬼',
  drunk: '酒鬼',
  insomniac: '失眠者',
  villager: '村民',
  tanner: '皮匠',
  hunter: '猎人',
}

export const oneNightWerewolfStats = createCompetitiveStatsPresentation({
  roleLabels,
  winnerLabel: (match, roleLabel) => {
    if (match.winner === 'village') return '村庄阵营获胜'
    if (match.winner === 'werewolf') return '狼人阵营获胜'
    if (match.winner === 'tanner') return '皮匠获胜'
    if (match.winner === 'none') return '本局无人获胜'
    return `${roleLabel(match.winner)}获胜`
  },
})
