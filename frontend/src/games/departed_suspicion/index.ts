import { defineAsyncComponent } from 'vue'
import artwork from '../../assets/game-hall/icons/departed-suspicion.webp'
import { socialTableCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'

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
  capabilities: socialTableCapabilities(),
  presentation: {
    component: defineAsyncComponent(() => import('./DepartedSuspicionTable.vue')),
    roomLayout: 'wide',
    skinKind: null,
    launcher: {
      kicker: '身份藏在底牌里，枪口决定谁能留下',
      title: '建立秘密调查组',
      description: '召集两方特工入席，在装备、试探与临场判断中找出对方领袖。',
      accent: '#c98d87',
      glow: '#7d4745',
    },
    roomShell: {
      headerEyebrowSuffix: (snapshot) =>
        ` · ${snapshot.options.equipmentSet === 'base' ? '基础装备局' : '炸弹客/叛徒装备局'}`,
    },
  },
  rules: {
    settingsGroups: [{
      key: 'equipmentSet', title: '装备牌库', control: 'cards',
      description: '卧底扩展依赖完整掩护系统，因此不混入普通身份局',
      options: [
        ['bombers', '炸弹客/叛徒装备', '基础16张加该扩展5张，共21张'],
        ['base', '基础装备', '只使用经典16张，适合第一次教学'],
      ],
    }],
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
