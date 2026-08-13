import type { BuiltinGameRules } from '../../game-platform/types'

export const junqiRules = {
  defaults: {
    firstPlayer: 'random',
    allowGuests: true,
    allowSpectators: true,
    mode: 'dark',
  },
  labels: (options) => [
    options.mode === 'flip' ? '翻棋军旗' : '暗军旗',
    options.firstPlayer === 'host' ? '房主先手' : '随机先手',
    options.allowGuests ? '允许游客' : '仅登录玩家',
  ],
} satisfies BuiltinGameRules
