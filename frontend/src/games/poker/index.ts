import { defineAsyncComponent } from 'vue'
import pokerArtwork from '../../assets/game-hall/icons/poker.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

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
    roomShell: {
      activeExitDescription: '暂时返回会保留座位和筹码；退出并淘汰将放弃本桌，而且无法再返回。',
      abandonLabel: '退出并淘汰',
      finishedLabel: '本桌结束',
      rematchLabel: '准备重新开桌',
    },
  },
  rules: {
    settingsGroups: [
      {
        key: 'startingChips', title: '起始筹码', control: 'segmented', columns: 3,
        description: '开桌时发放，后续手牌持续继承，不涉及真实货币',
        options: [[500, '500'], [1000, '1000'], [2000, '2000']],
      },
      {
        key: 'smallBlind', title: '大小盲注', control: 'segmented', columns: 3,
        description: '大盲始终是小盲的两倍',
        options: [[5, '5/10'], [10, '10/20'], [20, '20/40']],
      },
    ],
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
  records: {
    stats: createCompetitiveStatsPresentation({
      winnerLabel: () => '筹码结算完成',
    }),
  },
})

export default pokerGame
