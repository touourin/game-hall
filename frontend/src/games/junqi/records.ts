import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

const roleLabels = {
  'dark-red': '暗军旗·红方',
  'dark-blue': '暗军旗·蓝方',
  'flip-red': '翻棋军旗·红方',
  'flip-blue': '翻棋军旗·蓝方',
}

export const junqiStats = createCompetitiveStatsPresentation({
  roleLabels,
  detailModeLabel: (match) => match.details.options?.mode === 'flip'
    ? '翻棋军旗'
    : '暗军旗',
})
