import { defineAsyncComponent } from 'vue'
import reactionArtworkDark from '../../assets/game-hall/icons/reaction-dark.webp'
import reactionArtworkLight from '../../assets/game-hall/icons/reaction-light.webp'
import { soloGameCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { reactionLeaderboard, reactionStats } from './records'
import { reactionSoloPresentation } from './soloPresentation'

export const reactionGame = defineBuiltinGame({
  key: 'reaction',
  catalog: {
    order: 100,
    name: '反应挑战',
    players: { min: 1, max: 1 },
    description: '盯住信号，挑战毫秒反应',
    tone: 'pulse',
    category: '个人挑战',
    artwork: { dark: reactionArtworkDark, light: reactionArtworkLight },
  },
  capabilities: soloGameCapabilities(),
  presentation: {
    component: defineAsyncComponent(() => import('./ReactionTest.vue')),
    roomLayout: 'standard',
    skinKind: null,
    roomShell: {
      headerEyebrowSuffix: () => ' · 单人测试',
      headerTitle: () => '反应挑战',
    },
    solo: reactionSoloPresentation,
  },
  rules: {
    defaults: { allowSpectators: true },
    labels: () => ['三轮测试'],
  },
  records: {
    leaderboard: reactionLeaderboard,
    stats: reactionStats,
  },
})

export default reactionGame
