import { defineAsyncComponent } from 'vue'
import hanoiArtwork from '../../assets/game-hall/icons/hanoi.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'
import { hanoiLeaderboard, hanoiStats } from './records'
import { hanoiRoomShell } from './roomPresentation'

export const hanoiGame = defineBuiltinGame({
  key: 'hanoi',
  catalog: {
    order: 150,
    name: '汉诺塔',
    players: { min: 1, max: 1 },
    description: '移动圆盘，用最少步数通关',
    tone: 'tower',
    category: '个人挑战',
    artwork: hanoiArtwork,
  },
  capabilities: {
    undo: false,
    draw: false,
    guests: false,
    spectators: true,
    firstPlayer: false,
    replay: false,
    ai: false,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./HanoiGame.vue')),
    roomLayout: 'standard',
    skinKind: null,
    roomShell: hanoiRoomShell,
  },
  rules: {
    settingsComponent: RuleSettings,
    defaults: {
      discCount: 5,
      allowSpectators: true,
    },
    labels: (options) => {
      const discCount = Number(options.discCount)
      return [`${discCount} 层圆盘`, `理论最少 ${2 ** discCount - 1} 步`]
    },
  },
  records: {
    leaderboard: hanoiLeaderboard,
    stats: hanoiStats,
    matchDetailComponent: defineAsyncComponent(() => import('./MatchDetail.vue')),
  },
})

export default hanoiGame
