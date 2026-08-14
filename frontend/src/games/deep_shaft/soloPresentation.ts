import { MoveHorizontal } from '@lucide/vue'
import type { BuiltinGameSoloPresentation } from '../../game-platform/types'

export const deepShaftSoloPresentation: BuiltinGameSoloPresentation = {
  icon: MoveHorizontal,
  accent: '#9b866d',
  content: () => ({
    category: '平台生存',
    kicker: '落点判断与连续下降',
    title: '深入百层，别被深井吞没',
    description: '角色会自动下落，你只需控制左右。踩准不断上移的平台，避开尖刺并维持生命。',
    button: '进入百层深井',
    features: ['五类特殊平台', '键盘与双拇指控制', '服务端重放轨迹'],
    metrics: [
      { label: '通关目标', value: '100 层' },
      { label: '生命上限', value: '10' },
      { label: '操作方式', value: '仅左右' },
    ],
    stages: ['判断落点', '应对平台', '深入百层'],
    recordNote: '本轮左右输入会由服务器重放，最深层数将进入独立排行榜。',
  }),
}
