import { defineAsyncComponent } from 'vue'
import xiangqiArtwork from '../../assets/game-hall/icons/xiangqi.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
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
  capabilities: {
    undo: true,
    draw: true,
    guests: true,
    spectators: true,
    firstPlayer: true,
    replay: true,
    ai: true,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./XiangqiBoard.vue')),
    roomLayout: 'standard',
    skinKind: 'board',
  },
  rules: { ...xiangqiRules, settingsComponent: RuleSettings },
})

export default xiangqiGame
