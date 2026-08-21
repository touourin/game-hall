import { defineAsyncComponent } from 'vue'
import doudizhuArtworkDark from '../../assets/game-hall/icons/doudizhu-dark.webp'
import doudizhuArtworkLight from '../../assets/game-hall/icons/doudizhu-light.webp'
import { socialTableCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

export const doudizhuGame = defineBuiltinGame({
  key: 'doudizhu',
  catalog: {
    order: 80,
    name: '斗地主',
    players: { min: 3, max: 3 },
    description: '逐张发牌，可随时明牌，三人斗到底',
    tone: 'blue',
    category: '扑克对战',
    artwork: { dark: doudizhuArtworkDark, light: doudizhuArtworkLight },
  },
  capabilities: socialTableCapabilities({ ai: true }),
  presentation: {
    component: defineAsyncComponent(() => import('./DoudizhuTable.vue')),
    roomLayout: 'wide',
    skinKind: 'cards',
    launcher: {
      kicker: '三人入局，叫抢定势',
      title: '召集一桌牌局',
      description: '创建三人牌局，确认玩法后邀请另外两位玩家加入。',
      accent: '#83bde5',
      glow: '#3d6f99',
    },
  },
  rules: {
    settingsGroups: [{
      key: 'variant', title: '斗地主玩法', control: 'cards', columns: 3,
      description: '三种玩法共用叫地主、抢地主与倍数结算',
      options: [
        ['classic', '经典', '标准54张牌'],
        ['laizi', '癞子', '随机点数充当万能牌'],
        ['no_shuffle', '不洗牌', '再来一局保留收牌顺序'],
      ],
    }],
    defaults: {
      firstPlayer: 'random',
      allowGuests: true,
      allowSpectators: true,
      variant: 'classic',
    },
    labels: (options) => [
      options.variant === 'laizi'
        ? '癞子玩法'
        : options.variant === 'no_shuffle'
          ? '不洗牌玩法'
          : '经典玩法',
      options.firstPlayer === 'host' ? '房主首叫' : '随机首叫',
      '叫地主／抢地主',
      '随时明牌',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ],
    firstPlayerCopy: () => ({
      title: '首叫玩家',
      description: '再来一局时仍会自动轮换',
      randomDescription: '随机指定首叫玩家',
      hostDescription: '房主在首局首先叫地主',
    }),
  },
  records: {
    stats: createCompetitiveStatsPresentation({
      roleLabels: { landlord: '地主', farmer: '农民' },
    }),
  },
})

export default doudizhuGame
