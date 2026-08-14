import { defineAsyncComponent } from 'vue'
import minesweeperArtwork from '../../assets/game-hall/icons/minesweeper.webp'
import { soloGameCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { minesweeperLeaderboard, minesweeperStats } from './records'
import { minesweeperSoloPresentation } from './soloPresentation'

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
  capabilities: soloGameCapabilities({ spectators: true }),
  presentation: {
    component: defineAsyncComponent(() => import('./MinesweeperBoard.vue')),
    roomLayout: 'wide',
    skinKind: null,
    roomShell: {
      headerEyebrowSuffix: (snapshot) => ` · ${snapshot.game.difficultyLabel}`,
      headerTitle: () => '扫雷挑战',
      statsMode: (snapshot) => String(snapshot.options.difficulty ?? 'beginner'),
    },
    solo: minesweeperSoloPresentation,
  },
  rules: {
    settingsGroups: [{
      key: 'difficulty', title: '挑战难度', control: 'cards', columns: 3,
      description: '三种经典规格分别记录成绩和排行榜',
      options: [
        ['beginner', '初级', '9×9 · 10 雷'],
        ['intermediate', '中级', '16×16 · 40 雷'],
        ['expert', '高级', '16×30 · 99 雷'],
      ],
    }],
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
  records: {
    modeFromRules: (options) => String(options.difficulty ?? 'beginner'),
    leaderboard: minesweeperLeaderboard,
    stats: minesweeperStats,
  },
})

export default minesweeperGame
