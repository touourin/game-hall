import { defineAsyncComponent } from 'vue'
import schulteArtwork from '../../assets/game-hall/icons/schulte.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { schulteLeaderboard } from './records'

export const schulteGame = defineBuiltinGame({
  key: 'schulte',
  catalog: {
    order: 120,
    name: '舒尔特方格',
    players: { min: 1, max: 1 },
    description: '从 1 找到 25，练速度与专注',
    tone: 'focus',
    category: '个人挑战',
    artwork: schulteArtwork,
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
    component: defineAsyncComponent(() => import('./SchulteGrid.vue')),
    roomLayout: 'standard',
    skinKind: null,
  },
  rules: {
    defaults: { allowSpectators: false },
    labels: () => ['5×5 标准挑战', '服务端计时'],
  },
  records: { leaderboard: schulteLeaderboard },
})

export default schulteGame
