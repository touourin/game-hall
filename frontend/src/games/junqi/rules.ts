import type { BuiltinGameRules } from '../../game-platform/types'

export const junqiRules = {
  settingsGroups: [{
    key: 'mode', title: '军旗玩法', control: 'cards',
    description: '选择完整暗棋或轻量翻棋',
    options: [
      ['dark', '暗军旗', '双方秘密布阵后行棋'],
      ['flip', '翻棋军旗', '随机扣棋，首翻确定阵营'],
    ],
  }],
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
