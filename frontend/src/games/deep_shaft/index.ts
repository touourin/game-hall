import { defineAsyncComponent } from 'vue'
import deepShaftArtworkDark from '../../assets/game-hall/icons/deep-shaft-dark.webp'
import deepShaftArtworkLight from '../../assets/game-hall/icons/deep-shaft-light.webp'
import { soloGameCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { deepShaftLeaderboard, deepShaftStats } from './records'
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
    artwork: { dark: deepShaftArtworkDark, light: deepShaftArtworkLight },
  },
  capabilities: soloGameCapabilities(),
  presentation: {
    component: defineAsyncComponent(() => import('./DeepShaftGame.vue')),
    roomLayout: 'wide',
    skinKind: null,
    roomShell: {
      headerEyebrowSuffix: () => ' · 百层平台生存',
      headerTitle: () => '百层深井',
    },
    solo: deepShaftSoloPresentation,
  },
  rules: {
    defaults: { allowSpectators: true },
    labels: () => ['100 层挑战', '左右移动', '服务端轨迹重放'],
  },
  records: {
    leaderboard: deepShaftLeaderboard,
    stats: deepShaftStats,
  },
})

export default deepShaftGame
