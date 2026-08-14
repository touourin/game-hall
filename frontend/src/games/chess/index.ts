import { defineAsyncComponent } from 'vue'
import chessArtworkDark from '../../assets/game-hall/icons/chess-dark.webp'
import chessArtworkLight from '../../assets/game-hall/icons/chess-light.webp'
import { boardDuelCapabilities } from '../../game-platform/capabilities'
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
    artwork: { dark: chessArtworkDark, light: chessArtworkLight },
  },
  capabilities: boardDuelCapabilities({ replay: true }),
  presentation: {
    component: defineAsyncComponent(() => import('./ChessBoard.vue')),
    roomLayout: 'standard',
    skinKind: 'board',
    launcher: {
      kicker: '六十四格之间，每一步都在收紧王的退路',
      title: '开启黑白棋局',
      description: '邀请对手落座，在完整升变、王车易位与和棋判定中展开较量。',
      accent: '#b8b7ae',
      glow: '#6d6b62',
    },
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
