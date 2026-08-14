import { defineAsyncComponent } from 'vue'
import gomokuArtwork from '../../assets/game-hall/icons/gomoku.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'
import RuleSettings from './RuleSettings.vue'
import { gomokuRules } from './rules'

export const gomokuGame = defineBuiltinGame({
  key: 'gomoku',
  catalog: {
    order: 30,
    name: '五子棋',
    players: { min: 2, max: 2 },
    description: '一子定势，五子连珠',
    tone: 'ink',
    category: '棋类竞技',
    artwork: gomokuArtwork,
  },
  capabilities: {
    undo: true,
    draw: true,
    guests: true,
    spectators: true,
    firstPlayer: true,
    replay: false,
    ai: false,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./GomokuBoard.vue')),
    roomLayout: 'standard',
    skinKind: 'board',
  },
  rules: { ...gomokuRules, settingsComponent: RuleSettings },
  records: {
    stats: createCompetitiveStatsPresentation({
      roleLabels: { black: '黑方', white: '白方' },
      showDrawSummary: true,
    }),
  },
})

export default gomokuGame
