import { defineAsyncComponent } from 'vue'
import monopolyArtwork from '../../assets/game-hall/icons/monopoly.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'

export const monopolyGame = defineBuiltinGame({
  key: 'monopoly',
  catalog: {
    order: 170,
    name: '大富翁',
    players: { min: 2, max: 4 },
    description: '买下整座城，让财富沿街生长',
    tone: 'fortune',
    category: '派对桌游',
    artwork: monopolyArtwork,
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
    component: defineAsyncComponent(() => import('./MonopolyBoard.vue')),
    roomLayout: 'wide',
    skinKind: null,
    launcher: {
      kicker: '掷骰启程，让每条街道成为资产',
      title: '开启城市财富竞赛',
      description: '邀请伙伴环游城市，收购同色街区、升级地产，在回合终点成为首席大亨。',
      accent: '#dfb45f',
      glow: '#8a6126',
    },
  },
  rules: {
    settingsGroups: [
      {
        key: 'startingCash', title: '起始资金', control: 'segmented', columns: 3,
        description: '资金越少，前期买地取舍越明显',
        options: [[6000, '6000'], [8000, '8000'], [10000, '10000']],
      },
      {
        key: 'maxRounds', title: '比赛回合', control: 'segmented', columns: 3,
        description: '达到上限时按现金、地产与升级总值排名',
        options: [[12, '12 回合'], [20, '20 回合'], [30, '30 回合']],
      },
    ],
    defaults: {
      firstPlayer: 'random',
      allowGuests: true,
      allowSpectators: true,
      startingCash: 8000,
      maxRounds: 20,
    },
    labels: (options) => [
      '2–4 人',
      `起始资金 ${Number(options.startingCash)}`,
      `${Number(options.maxRounds)} 回合资产赛`,
      '同色地块可升级',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ],
  },
})

export default monopolyGame
