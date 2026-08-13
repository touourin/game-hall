import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

export const pokerStats = createCompetitiveStatsPresentation({
  winnerLabel: () => '筹码结算完成',
})
