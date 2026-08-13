import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

export const chessStats = createCompetitiveStatsPresentation({
  roleLabels: { black: '黑方', white: '白方' },
})
