import { defineAsyncComponent } from 'vue'
import schulteArtworkDark from '../../assets/game-hall/icons/schulte-dark.webp'
import schulteArtworkLight from '../../assets/game-hall/icons/schulte-light.webp'
import { soloGameCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { schulteLeaderboard, schulteStats } from './records'
import { schulteSoloPresentation } from './soloPresentation'

export const schulteGame = defineBuiltinGame({
  key: 'schulte',
  catalog: {
    order: 120,
    name: '舒尔特方格',
    players: { min: 1, max: 1 },
    description: '从 1 找到 25，练速度与专注',
    tone: 'focus',
    category: '个人挑战',
    artwork: { dark: schulteArtworkDark, light: schulteArtworkLight },
  },
  capabilities: soloGameCapabilities(),
  presentation: {
    component: defineAsyncComponent(() => import('./SchulteGrid.vue')),
    roomLayout: 'standard',
    skinKind: null,
    roomShell: {
      headerEyebrowSuffix: () => ' · 单人专注',
      headerTitle: () => '舒尔特挑战',
    },
    solo: schulteSoloPresentation,
  },
  rules: {
    defaults: { allowSpectators: true },
    labels: () => ['5×5 标准挑战', '服务端计时'],
  },
  records: {
    leaderboard: schulteLeaderboard,
    stats: schulteStats,
  },
})

export default schulteGame
