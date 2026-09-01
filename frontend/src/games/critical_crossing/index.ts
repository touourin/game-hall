import { defineAsyncComponent } from 'vue'
import criticalCrossingArtworkDark from '../../assets/game-hall/icons/critical-crossing-dark.webp'
import criticalCrossingArtworkLight from '../../assets/game-hall/icons/critical-crossing-light.webp'
import { soloGameCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import {
  criticalCrossingLeaderboard,
  criticalCrossingStats,
} from './records'
import { criticalCrossingSoloPresentation } from './soloPresentation'

export const criticalCrossingGame = defineBuiltinGame({
  key: 'critical_crossing',
  catalog: {
    order: 130,
    name: '算途疾行',
    players: { min: 1, max: 1 },
    description: '在云桥上自动疾行，变道、跳跃与下蹲穿过随机分叉',
    tone: 'crossing',
    category: '个人挑战',
    artwork: {
      dark: criticalCrossingArtworkDark,
      light: criticalCrossingArtworkLight,
    },
  },
  capabilities: soloGameCapabilities({ spectatorFrames: true }),
  presentation: {
    component: defineAsyncComponent(() => import('./CriticalCrossingGame.vue')),
    roomLayout: 'wide',
    skinKind: null,
    roomShell: {
      headerEyebrowSuffix: snapshot => ` · ${snapshot.game.difficultyLabel}模式`,
      headerTitle: () => '算途疾行',
      statsMode: snapshot => String(snapshot.options.difficulty ?? '5s'),
    },
    solo: criticalCrossingSoloPresentation,
  },
  rules: {
    settingsGroups: [{
      key: 'difficulty',
      title: '疾行时长',
      control: 'cards',
      columns: 3,
      description: '人物会自动前进；赛道混合两路、三路分叉以及地面和上方障碍',
      options: [
        ['5s', '校准', '5 秒 · 5 段 · 入门节奏'],
        ['8s', '疾行', '8 秒 · 8 段 · 连续分叉'],
        ['10s', '极限', '10 秒 · 10 段 · 完整云桥'],
      ],
    }],
    defaults: {
      difficulty: '5s',
      allowSpectators: true,
    },
    labels: options => {
      if (options.difficulty === '10s') return ['极限', '10 秒目标', '10 段云桥']
      if (options.difficulty === '8s') return ['疾行', '8 秒目标', '8 段云桥']
      return ['校准', '5 秒目标', '5 段云桥']
    },
  },
  records: {
    modeFromRules: options => String(options.difficulty ?? '5s'),
    leaderboard: criticalCrossingLeaderboard,
    stats: criticalCrossingStats,
  },
})

export default criticalCrossingGame
