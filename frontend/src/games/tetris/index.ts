import { defineAsyncComponent } from 'vue'
import tetrisArtworkDark from '../../assets/game-hall/icons/tetris-dark.webp'
import tetrisArtworkLight from '../../assets/game-hall/icons/tetris-light.webp'
import { soloGameCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { tetrisLeaderboard, tetrisStats } from './records'
import { tetrisSoloPresentation } from './soloPresentation'

export const tetrisGame = defineBuiltinGame({
  key: 'tetris',
  catalog: {
    order: 160,
    name: '落块挑战',
    players: { min: 1, max: 1 },
    description: '排列方块、连续消行，冲击更高分数',
    tone: 'blocks',
    category: '个人挑战',
    artwork: { dark: tetrisArtworkDark, light: tetrisArtworkLight },
  },
  capabilities: soloGameCapabilities(),
  presentation: {
    component: defineAsyncComponent(() => import('./TetrisGame.vue')),
    roomLayout: 'standard',
    skinKind: null,
    roomShell: {
      headerEyebrowSuffix: (snapshot) => snapshot.options.challengeMode === 'endless'
        ? ' · 无限高分挑战'
        : ` · ${Number(snapshot.options.durationSeconds ?? 180) / 60} 分钟限时`,
      headerTitle: () => '落块挑战',
      statsMode: (snapshot) => snapshot.options.challengeMode === 'endless'
        ? 'standard'
        : `timed_${Number(snapshot.options.durationSeconds ?? 180)}`,
    },
    solo: tetrisSoloPresentation,
  },
  rules: {
    settingsGroups: [
      {
        key: 'challengeMode', title: '挑战模式', control: 'cards',
        description: '限时模式到点自动结算；无限模式保留堆顶结束玩法',
        options: [
          ['timed', '限时挑战', '在固定时间内尽可能获得高分'],
          ['endless', '无限挑战', '持续游玩，直到方块堆到顶部'],
        ],
      },
      {
        key: 'durationSeconds', title: '挑战时长', control: 'segmented', columns: 3,
        description: '不同时间档位分别记录排行榜',
        visibleWhen: ['challengeMode', 'timed'],
        options: [[60, '1 分钟'], [180, '3 分钟'], [300, '5 分钟']],
      },
    ],
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
  records: {
    modeFromRules: (options) => options.challengeMode === 'endless'
      ? 'standard'
      : `timed_${Number(options.durationSeconds ?? 180)}`,
    leaderboard: tetrisLeaderboard,
    stats: tetrisStats,
  },
})

export default tetrisGame
