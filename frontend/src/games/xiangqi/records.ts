import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

export const xiangqiStats = createCompetitiveStatsPresentation({
  roleLabels: { red: '红方', black: '黑方' },
  showDrawSummary: true,
})
