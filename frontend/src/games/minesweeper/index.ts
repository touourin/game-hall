import { defineAsyncComponent } from 'vue'
import minesweeperArtwork from '../../assets/game-hall/icons/minesweeper.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'
import { minesweeperLeaderboard } from './records'

export const minesweeperGame = defineBuiltinGame({
  key: 'minesweeper',
  catalog: {
    order: 140,
    name: '扫雷',
    players: { min: 1, max: 1 },
    description: '排除危险，清空整片雷区',
    tone: 'mine',
    category: '个人挑战',
    artwork: minesweeperArtwork,
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
    component: defineAsyncComponent(() => import('./MinesweeperBoard.vue')),
    roomLayout: 'wide',
    skinKind: null,
  },
  rules: {
    settingsComponent: RuleSettings,
    defaults: {
      difficulty: 'beginner',
      allowSpectators: true,
    },
    labels: (options) => {
      if (options.difficulty === 'expert') return ['高级', '16×30', '99 雷']
      if (options.difficulty === 'intermediate') return ['中级', '16×16', '40 雷']
      return ['初级', '9×9', '10 雷']
    },
  },
  records: { leaderboard: minesweeperLeaderboard },
})

export default minesweeperGame
