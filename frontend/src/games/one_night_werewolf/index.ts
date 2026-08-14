import { defineAsyncComponent } from 'vue'
import artwork from '../../assets/game-hall/icons/one-night-werewolf.webp'
import { socialTableCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { oneNightWerewolfStats } from './records'
import { oneNightWerewolfRoomShell } from './roomPresentation'

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
  capabilities: socialTableCapabilities({
    spectators: false,
    firstPlayer: false,
  }),
  presentation: {
    component: defineAsyncComponent(() => import('./OneNightWerewolfTable.vue')),
    roomLayout: 'wide',
    skinKind: null,
    launcher: {
      kicker: '月落之前，每个人都可能换了身份',
      title: '召集月夜村庄',
      description: '一晚完成所有行动，天亮后通过发言和一次秘密投票找出狼人。',
      accent: '#95a9ee',
      glow: '#4d5f9e',
    },
    roomShell: oneNightWerewolfRoomShell,
  },
  rules: {
    settingsGroups: [
      {
        key: 'rolePreset', title: '角色组合', control: 'cards', columns: 3,
        description: '所有组合都包含玩家人数加三张牌；多皮者留待后续扩展',
        options: [
          ['beginner', '初见月夜', '核心换牌角色，适合第一次教学'],
          ['standard', '标准疑云', '加入爪牙与皮匠，阵营判断更丰富'],
          ['chaos', '混沌之夜', '高人数加入守夜人，信息交叉更多'],
        ],
      },
      {
        key: 'listed', title: '房间发现', control: 'cards',
        description: '进行中固定关闭观战，避免第一人称视角泄露私密身份',
        options: [
          [true, '公开房间', '等待阶段可以在大厅中被发现'],
          [false, '私密房间', '只有拿到房间码或邀请链接的玩家可加入'],
        ],
      },
    ],
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
  records: { stats: oneNightWerewolfStats },
})

export default oneNightWerewolfGame
