import { defineAsyncComponent } from 'vue'
import doudizhuArtwork from '../../assets/game-hall/icons/doudizhu.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'

export const doudizhuGame = defineBuiltinGame({
  key: 'doudizhu',
  catalog: {
    order: 80,
    name: '斗地主',
    players: { min: 3, max: 3 },
    description: '抢下地主，三人斗到底',
    tone: 'blue',
    category: '扑克对战',
    artwork: doudizhuArtwork,
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
    component: defineAsyncComponent(() => import('./DoudizhuTable.vue')),
    roomLayout: 'wide',
    skinKind: 'cards',
  },
  rules: {
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
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ],
  },
})

export default doudizhuGame
