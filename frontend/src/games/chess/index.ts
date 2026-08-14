import { defineAsyncComponent } from 'vue'
import chessArtwork from '../../assets/game-hall/icons/chess.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

export const chessGame = defineBuiltinGame({
  key: 'chess',
  catalog: {
    order: 50,
    name: '国际象棋',
    players: { min: 2, max: 2 },
    description: '跨越黑白格，围猎对方王',
    tone: 'chess',
    category: '棋类竞技',
    artwork: chessArtwork,
  },
  capabilities: {
    undo: true,
    draw: true,
    guests: true,
    spectators: true,
    firstPlayer: true,
    replay: true,
    ai: false,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./ChessBoard.vue')),
    roomLayout: 'standard',
    skinKind: 'board',
  },
  rules: {
    defaults: {
      firstPlayer: 'random',
      allowGuests: true,
      allowSpectators: true,
      allowUndo: true,
      allowDraw: true,
    },
    labels: (options) => [
      options.firstPlayer === 'host' ? '房主先手' : '随机先手',
      options.allowUndo ? '允许悔棋' : '禁止悔棋',
      options.allowDraw ? '允许和棋' : '禁止和棋',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ],
  },
  records: {
    stats: createCompetitiveStatsPresentation({
      roleLabels: { black: '黑方', white: '白方' },
    }),
  },
})

export default chessGame
