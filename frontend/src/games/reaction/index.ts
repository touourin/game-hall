import { defineAsyncComponent } from 'vue'
import reactionArtwork from '../../assets/game-hall/icons/reaction.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { reactionLeaderboard, reactionStats } from './records'
import { reactionRoomShell } from './roomPresentation'
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
    artwork: reactionArtwork,
  },
  capabilities: {
    undo: false,
    draw: false,
    guests: false,
    spectators: false,
    firstPlayer: false,
    replay: false,
    ai: false,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./ReactionTest.vue')),
    roomLayout: 'standard',
    skinKind: null,
    roomShell: reactionRoomShell,
    solo: reactionSoloPresentation,
  },
  rules: {
    defaults: { allowSpectators: false },
    labels: () => ['三轮测试'],
  },
  records: {
    leaderboard: reactionLeaderboard,
    stats: reactionStats,
    matchDetailComponent: defineAsyncComponent(() => import('./MatchDetail.vue')),
  },
})

export default reactionGame
