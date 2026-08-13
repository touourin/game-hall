import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

export const goStats = createCompetitiveStatsPresentation({
  roleLabels: { black: '黑方', white: '白方' },
  showDrawSummary: true,
})
