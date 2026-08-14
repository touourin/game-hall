import { Grid3X3 } from '@lucide/vue'
import type { BuiltinGameSoloPresentation } from '../../game-platform/types'

export const schulteSoloPresentation: BuiltinGameSoloPresentation = {
  icon: Grid3X3,
  accent: '#8584a6',
  content: () => ({
    category: '专注力挑战',
    kicker: '视觉搜索与持续专注',
    title: '按顺序找到 1–25',
    description: '让视线覆盖整张方格，在不漏号、不跳号的前提下压缩每一次搜索时间。',
    button: '进入舒尔特方格',
    features: ['顺序完整验证', '服务端精确计时', '专注速度计榜'],
    metrics: [
      { label: '标准版式', value: '5 × 5' },
      { label: '搜索目标', value: '1 → 25' },
      { label: '完成判定', value: '依次点击' },
    ],
    stages: ['稳定视线', '依次搜索', '完成计时'],
    recordNote: '完整点击 1–25 后，服务端将自动保存本次用时。',
  }),
}
