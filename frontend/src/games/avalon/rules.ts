import type { BuiltinGameRules } from '../../game-platform/types'

export const avalonRules = {
  defaults: {
    mode: 'standard',
    shadowMerlinEnabled: false,
    ladyEnabled: true,
    listed: true,
    allowGuests: true,
    allowSpectators: true,
    earlyAssassinationEnabled: false,
  },
  applyChange: (options, key, value) => {
    const next = { ...options, [key]: value }
    if (key === 'mode' && value === 'court_undercurrent') {
      next.ladyEnabled = false
      next.earlyAssassinationEnabled = false
    }
    if (key === 'mode' && value === 'standard') {
      next.shadowMerlinEnabled = false
    }
    return next
  },
  labels: (options) => {
    const labels = [
      options.mode === 'court_undercurrent' ? '王庭暗流' : '标准阿瓦隆',
      options.listed ? '公开房间' : '私密房间',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ]
    if (options.mode !== 'court_undercurrent') {
      labels.push(options.ladyEnabled ? '启用湖中仙女' : '不启用湖中仙女')
      if (options.earlyAssassinationEnabled) labels.push('允许提前刺杀')
    }
    if (
      options.mode === 'court_undercurrent'
      && options.shadowMerlinEnabled
    ) labels.push('暗影梅林扩展')
    return labels
  },
} satisfies BuiltinGameRules
