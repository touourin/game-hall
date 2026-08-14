import { defineAsyncComponent } from 'vue'
import xiangqiArtworkDark from '../../assets/game-hall/icons/xiangqi-dark.webp'
import xiangqiArtworkLight from '../../assets/game-hall/icons/xiangqi-light.webp'
import { boardDuelCapabilities } from '../../game-platform/capabilities'
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
    artwork: { dark: xiangqiArtworkDark, light: xiangqiArtworkLight },
  },
  capabilities: boardDuelCapabilities({ replay: true, ai: true }),
  presentation: {
    component: defineAsyncComponent(() => import('./XiangqiBoard.vue')),
    roomLayout: 'standard',
    skinKind: 'board',
    launcher: {
      kicker: '隔河列阵，攻守有序',
      title: '布下楚汉战局',
      description: '创建一场完整可复盘的中国象棋对局，让每一步进退都有回应。',
      accent: '#df887d',
      glow: '#9d433d',
    },
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
