import type { BuiltinGameRules } from '../../game-platform/types'

export const GO_HANDICAP_OPTIONS = [0, 2, 3, 6, 9] as const

export const goRules = {
  defaults: {
    firstPlayer: 'random',
    allowGuests: true,
    allowSpectators: true,
    allowUndo: true,
    allowDraw: true,
    boardSize: 19,
    komi: 7.5,
    handicap: 0,
    handicapGiver: 'host',
  },
  applyChange: (options, key, value) => {
    const next = { ...options, [key]: value }
    if (key === 'boardSize' && value !== 19) next.handicap = 0
    if (key === 'handicap' && value !== 0) {
      next.boardSize = 19
      next.komi = 0
    }
    return next
  },
  hasHandicap: (options) => Number(options.handicap) > 0,
  labels: (options) => {
    const handicap = Number(options.handicap) > 0
    const labels = [
      `${options.boardSize} 路棋盘`,
      handicap
        ? options.handicapGiver === 'host' ? '房主让子' : '对手让子'
        : options.firstPlayer === 'host' ? '房主先手' : '随机先手',
      options.allowUndo ? '允许悔棋' : '禁止悔棋',
      options.allowDraw ? '允许和棋' : '禁止和棋',
    ]
    if (handicap) labels.push(`让 ${options.handicap} 子`)
    labels.push(`贴目 ${options.komi}`)
    labels.push(options.allowGuests ? '允许游客' : '仅登录玩家')
    return labels
  },
} satisfies BuiltinGameRules
