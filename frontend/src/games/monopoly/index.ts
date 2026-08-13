import { defineAsyncComponent } from 'vue'
import monopolyArtwork from '../../assets/game-hall/icons/monopoly.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'

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
  },
  rules: {
    settingsComponent: RuleSettings,
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
