import { defineAsyncComponent } from 'vue'
import goArtwork from '../../assets/game-hall/icons/go.webp'
import { boardDuelCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'
import RuleSettings from './RuleSettings.vue'
import { goRules } from './rules'

export const goGame = defineBuiltinGame({
  key: 'go',
  catalog: {
    order: 60,
    name: '围棋',
    players: { min: 2, max: 2 },
    description: '方寸之间，围地争先',
    tone: 'jade',
    category: '棋类竞技',
    artwork: goArtwork,
  },
  capabilities: boardDuelCapabilities({ ai: true }),
  presentation: {
    component: defineAsyncComponent(() => import('./GoBoard.vue')),
    roomLayout: 'standard',
    skinKind: 'board',
    launcher: {
      kicker: '方寸落子，争地围空',
      title: '开启手谈棋局',
      description: '设定棋盘、贴目与先手，在安静的落子中争夺整片疆域。',
      accent: '#79c9ae',
      glow: '#327c68',
    },
  },
  rules: { ...goRules, settingsComponent: RuleSettings },
  records: {
    stats: createCompetitiveStatsPresentation({
      roleLabels: { black: '黑方', white: '白方' },
      showDrawSummary: true,
    }),
  },
})

export default goGame
