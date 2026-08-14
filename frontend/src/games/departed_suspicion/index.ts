import { defineAsyncComponent } from 'vue'
import artwork from '../../assets/game-hall/icons/departed-suspicion.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'
import { departedSuspicionRoomShell } from './roomPresentation'

export const departedSuspicionGame = defineBuiltinGame({
  key: 'departed_suspicion',
  catalog: {
    order: 10,
    name: '无间疑云',
    players: { min: 4, max: 8 },
    description: '查底细、抢装备，在枪口转向前找出敌方领袖',
    tone: 'suspicion',
    category: '身份推理',
    artwork,
  },
  capabilities: {
    undo: false,
    draw: false,
    guests: true,
    spectators: true,
    firstPlayer: true,
    replay: false,
    ai: false,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./DepartedSuspicionTable.vue')),
    roomLayout: 'wide',
    skinKind: null,
    roomShell: departedSuspicionRoomShell,
  },
  rules: {
    settingsComponent: RuleSettings,
    defaults: {
      equipmentSet: 'bombers',
      firstPlayer: 'random',
      allowGuests: true,
      allowSpectators: true,
    },
    labels: (options) => [
      '4–8 人基础身份局',
      options.equipmentSet === 'base'
        ? '基础16张装备'
        : '基础＋炸弹客/叛徒21张装备',
      options.firstPlayer === 'host' ? '房主先手' : '随机先手',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ],
  },
})

export default departedSuspicionGame
