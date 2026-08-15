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
    name: '临界穿越',
    players: { min: 1, max: 1 },
    description: '识别脉冲缺口，穿越不断收紧的临界场',
    tone: 'crossing',
    category: '个人挑战',
    artwork: {
      dark: criticalCrossingArtworkDark,
      light: criticalCrossingArtworkLight,
    },
  },
  capabilities: soloGameCapabilities(),
  presentation: {
    component: defineAsyncComponent(() => import('./CriticalCrossingGame.vue')),
    roomLayout: 'standard',
    skinKind: null,
    roomShell: {
      headerEyebrowSuffix: snapshot => ` · ${snapshot.game.difficultyLabel}模式`,
      headerTitle: () => '临界穿越',
      statsMode: snapshot => String(snapshot.options.difficulty ?? '5s'),
    },
    solo: criticalCrossingSoloPresentation,
  },
  rules: {
    settingsGroups: [{
      key: 'difficulty',
      title: '穿越时长',
      control: 'cards',
      columns: 3,
      description: '更长的挑战会加入更多交叉脉冲，并独立记录成绩',
      options: [
        ['5s', '校准', '5 秒 · 5 轮'],
        ['8s', '过载', '8 秒 · 8 轮'],
        ['10s', '临界', '10 秒 · 10 轮'],
      ],
    }],
    defaults: {
      difficulty: '5s',
      allowSpectators: false,
    },
    labels: options => {
      if (options.difficulty === '10s') return ['临界', '10 秒目标', '10 轮脉冲']
      if (options.difficulty === '8s') return ['过载', '8 秒目标', '8 轮脉冲']
      return ['校准', '5 秒目标', '5 轮脉冲']
    },
  },
  records: {
    modeFromRules: options => String(options.difficulty ?? '5s'),
    leaderboard: criticalCrossingLeaderboard,
    stats: criticalCrossingStats,
  },
})

export default criticalCrossingGame
