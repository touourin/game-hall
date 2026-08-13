import type { BuiltinGameRules } from '../../game-platform/types'

export const XIANGQI_HANDICAP_OPTIONS = [
  { value: 'none', label: '不让子' },
  { value: 'cannon', label: '让炮' },
  { value: 'horse', label: '让马' },
  { value: 'rook', label: '让车' },
  { value: 'nine', label: '让九子' },
] as const

export const xiangqiRules = {
  defaults: {
    firstPlayer: 'random',
    allowGuests: true,
    allowSpectators: true,
    allowUndo: true,
    allowDraw: true,
    captureHintsEnabled: true,
    handicap: 'none',
    handicapGiver: 'host',
  },
  hasHandicap: (options) => (
    typeof options.handicap === 'string' && options.handicap !== 'none'
  ),
  labels: (options) => {
    const handicap = typeof options.handicap === 'string'
      && options.handicap !== 'none'
    const labels = [
      handicap
        ? options.handicapGiver === 'host' ? '房主让子' : '对手让子'
        : options.firstPlayer === 'host' ? '房主先手' : '随机先手',
      options.allowUndo ? '允许悔棋' : '禁止悔棋',
      options.allowDraw ? '允许和棋' : '禁止和棋',
    ]
    const selectedHandicap = XIANGQI_HANDICAP_OPTIONS.find(
      ({ value }) => value !== 'none' && value === options.handicap,
    )
    if (selectedHandicap) labels.push(selectedHandicap.label)
    labels.push(options.captureHintsEnabled ? '吃子提醒' : '关闭吃子提醒')
    labels.push(options.allowGuests ? '允许游客' : '仅登录玩家')
    return labels
  },
} satisfies BuiltinGameRules
