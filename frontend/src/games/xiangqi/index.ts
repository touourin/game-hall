import { defineAsyncComponent } from 'vue'
import xiangqiArtwork from '../../assets/game-hall/icons/xiangqi.webp'
import { boardGameCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'
import RuleSettings from './RuleSettings.vue'
import { xiangqiRules } from './rules'

export const xiangqiGame = defineBuiltinGame({
  key: 'xiangqi',
  catalog: {
    order: 40,
    name: '中国象棋',
    players: { min: 2, max: 2 },
    description: '隔河列阵，步步攻守',
    tone: 'red',
    category: '棋类竞技',
    artwork: xiangqiArtwork,
  },
  capabilities: boardGameCapabilities({ replay: true, ai: true }),
  presentation: {
    component: defineAsyncComponent(() => import('./XiangqiBoard.vue')),
    roomLayout: 'standard',
    skinKind: 'board',
  },
  rules: { ...xiangqiRules, settingsComponent: RuleSettings },
  records: {
    stats: createCompetitiveStatsPresentation({
      roleLabels: { red: '红方', black: '黑方' },
      showDrawSummary: true,
    }),
  },
})

export default xiangqiGame
