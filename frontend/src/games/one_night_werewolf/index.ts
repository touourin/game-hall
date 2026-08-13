import { defineAsyncComponent } from 'vue'
import artwork from '../../assets/game-hall/icons/one-night-werewolf.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'

export const oneNightWerewolfGame = defineBuiltinGame({
  key: 'one_night_werewolf',
  catalog: {
    order: 20,
    name: '一夜狼人',
    players: { min: 3, max: 10 },
    description: '一晚换位，天亮后只投一次',
    tone: 'moon',
    category: '社交推理',
    artwork,
  },
  capabilities: {
    undo: false,
    draw: false,
    guests: true,
    spectators: false,
    firstPlayer: false,
    replay: false,
    ai: false,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./OneNightWerewolfTable.vue')),
    roomLayout: 'wide',
    skinKind: null,
  },
  rules: {
    settingsComponent: RuleSettings,
    defaults: {
      rolePreset: 'standard',
      listed: true,
      allowGuests: true,
      allowSpectators: false,
    },
    labels: (options) => {
      const preset = options.rolePreset === 'beginner'
        ? '初见月夜'
        : options.rolePreset === 'chaos'
          ? '混沌之夜'
          : '标准疑云'
      return [
        '3–10 人',
        preset,
        '不限时讨论',
        options.listed ? '公开房间' : '私密房间',
        options.allowGuests ? '允许游客' : '仅登录玩家',
      ]
    },
  },
})

export default oneNightWerewolfGame
