import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

export const gomokuStats = createCompetitiveStatsPresentation({
  roleLabels: { black: '黑方', white: '白方' },
  showDrawSummary: true,
})
