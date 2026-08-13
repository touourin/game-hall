import type { BuiltinGameRules } from '../../game-platform/types'

export const gomokuRules = {
  defaults: {
    firstPlayer: 'random',
    allowGuests: true,
    allowSpectators: true,
    allowUndo: true,
    allowDraw: true,
    winRule: 'exact_five',
    openingRule: 'swap2',
  },
  applyChange: (options, key, value) => {
    const next = { ...options, [key]: value }
    if (key === 'winRule' && value === 'renju') {
      next.openingRule = 'standard'
    }
    return next
  },
  labels: (options) => [
    '15 路棋盘',
    options.firstPlayer === 'host'
      ? options.openingRule === 'swap2' ? '房主摆子' : '房主先手'
      : options.openingRule === 'swap2' ? '随机摆子者' : '随机先手',
    options.allowUndo ? '允许悔棋' : '禁止悔棋',
    options.allowDraw ? '允许和棋' : '禁止和棋',
    options.openingRule === 'swap2' ? 'Swap2 开局' : '标准开局',
    options.winRule === 'renju'
      ? '有禁手连珠'
      : options.winRule === 'exact_five'
        ? '正好五子'
        : '自由五子',
    options.allowGuests ? '允许游客' : '仅登录玩家',
  ],
} satisfies BuiltinGameRules
