import { defineAsyncComponent } from 'vue'
import pokerArtwork from '../../assets/game-hall/icons/poker.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'
import { pokerStats } from './records'

export const pokerGame = defineBuiltinGame({
  key: 'poker',
  catalog: {
    order: 70,
    name: '德州扑克',
    players: { min: 2, max: 8 },
    description: '读懂对手，把筹码推向终局',
    tone: 'poker',
    category: '扑克对战',
    artwork: pokerArtwork,
  },
  capabilities: {
    undo: false,
    draw: false,
    guests: true,
    spectators: true,
    firstPlayer: false,
    replay: false,
    ai: false,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./PokerTable.vue')),
    roomLayout: 'wide',
    skinKind: 'cards',
  },
  rules: {
    settingsComponent: RuleSettings,
    defaults: {
      allowGuests: true,
      allowSpectators: true,
      startingChips: 1000,
      smallBlind: 10,
    },
    labels: (options) => {
      const smallBlind = Number(options.smallBlind)
      return [
        '2–8 人',
        `起始 ${Number(options.startingChips)} 筹码`,
        `盲注 ${smallBlind}/${smallBlind * 2}`,
        options.allowGuests ? '允许游客' : '仅登录玩家',
      ]
    },
  },
  records: { stats: pokerStats },
})

export default pokerGame
