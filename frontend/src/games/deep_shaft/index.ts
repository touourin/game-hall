import { defineAsyncComponent } from 'vue'
import deepShaftArtwork from '../../assets/game-hall/icons/deep-shaft.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { deepShaftLeaderboard, deepShaftStats } from './records'
import { deepShaftRoomShell } from './roomPresentation'
import { deepShaftSoloPresentation } from './soloPresentation'

export const deepShaftGame = defineBuiltinGame({
  key: 'deep_shaft',
  catalog: {
    order: 110,
    name: '百层深井',
    players: { min: 1, max: 1 },
    description: '控制左右落点，在危险平台间深入一百层',
    tone: 'shaft',
    category: '个人挑战',
    artwork: deepShaftArtwork,
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
    component: defineAsyncComponent(() => import('./DeepShaftGame.vue')),
    roomLayout: 'standard',
    skinKind: null,
    roomShell: deepShaftRoomShell,
    solo: deepShaftSoloPresentation,
  },
  rules: {
    defaults: { allowSpectators: false },
    labels: () => ['100 层挑战', '左右移动', '服务端轨迹重放'],
  },
  records: {
    leaderboard: deepShaftLeaderboard,
    stats: deepShaftStats,
    matchDetailComponent: defineAsyncComponent(() => import('./MatchDetail.vue')),
  },
})

export default deepShaftGame
