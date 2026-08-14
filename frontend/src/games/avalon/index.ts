import { defineAsyncComponent } from 'vue'
import avalonArtwork from '../../assets/game-hall/icons/avalon.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'
import { avalonLeaderboard, avalonStats } from './records'
import { avalonRoomShell } from './roomPresentation'
import { avalonRules } from './rules'

export const avalonGame = defineBuiltinGame({
  key: 'avalon',
  catalog: {
    order: 0,
    name: '阿瓦隆',
    players: { min: 5, max: 10 },
    description: '谎言上桌，忠诚接受考验',
    tone: 'gold',
    category: '社交推理',
    artwork: avalonArtwork,
  },
  capabilities: {
    undo: false,
    draw: false,
    guests: true,
    spectators: true,
    firstPlayer: false,
    replay: true,
    ai: true,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./AvalonRoomView.vue')),
    roomLayout: 'wide',
    skinKind: null,
    roomShell: avalonRoomShell,
  },
  rules: { ...avalonRules, settingsComponent: RuleSettings },
  records: {
    leaderboard: avalonLeaderboard,
    stats: avalonStats,
    matchDetailComponent: defineAsyncComponent(() => import('./MatchDetail.vue')),
  },
})

export default avalonGame
