import { defineAsyncComponent } from 'vue'
import tetrisArtwork from '../../assets/game-hall/icons/tetris.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'
import { tetrisLeaderboard } from './records'

export const tetrisGame = defineBuiltinGame({
  key: 'tetris',
  catalog: {
    order: 160,
    name: '落块挑战',
    players: { min: 1, max: 1 },
    description: '排列方块、连续消行，冲击更高分数',
    tone: 'blocks',
    category: '个人挑战',
    artwork: tetrisArtwork,
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
    component: defineAsyncComponent(() => import('./TetrisGame.vue')),
    roomLayout: 'standard',
    skinKind: null,
  },
  rules: {
    settingsComponent: RuleSettings,
    defaults: {
      challengeMode: 'timed',
      durationSeconds: 180,
      allowSpectators: false,
    },
    labels: (options) => [
      options.challengeMode === 'timed'
        ? `${Number(options.durationSeconds) / 60} 分钟限时`
        : '无限挑战',
      '10×20 标准棋盘',
      '7-bag 随机序列',
    ],
  },
  records: { leaderboard: tetrisLeaderboard },
})

export default tetrisGame
