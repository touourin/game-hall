import { defineAsyncComponent } from 'vue'
import goArtwork from '../../assets/game-hall/icons/go.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'
import { goStats } from './records'
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
  capabilities: {
    undo: true,
    draw: true,
    guests: true,
    spectators: true,
    firstPlayer: true,
    replay: false,
    ai: true,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./GoBoard.vue')),
    roomLayout: 'standard',
    skinKind: 'board',
  },
  rules: { ...goRules, settingsComponent: RuleSettings },
  records: { stats: goStats },
})

export default goGame
