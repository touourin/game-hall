import { defineAsyncComponent } from 'vue'
import gomokuArtwork from '../../assets/game-hall/icons/gomoku.webp'
import { boardDuelCapabilities } from '../../game-platform/capabilities'
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
  capabilities: boardDuelCapabilities(),
  presentation: {
    component: defineAsyncComponent(() => import('./GomokuBoard.vue')),
    roomLayout: 'standard',
    skinKind: 'board',
    launcher: {
      kicker: '纵横十五路，一线定胜负',
      title: '落座连珠棋局',
      description: '选择公平开局与胜负规则，邀请对手在棋盘中央展开攻守。',
      accent: '#c5d2d7',
      glow: '#71858d',
    },
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
