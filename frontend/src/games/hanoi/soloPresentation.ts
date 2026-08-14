import { Layers3 } from '@lucide/vue'
import type { BuiltinGameSoloPresentation } from '../../game-platform/types'

export const hanoiSoloPresentation: BuiltinGameSoloPresentation = {
  icon: Layers3,
  accent: '#a48a65',
  hasRuleSettings: true,
  content: (options) => {
    const discCount = Number(options.discCount ?? 5)
    return {
      category: '空间推演',
      kicker: '递归推演与最短路径',
      title: '把整座圆盘移到最右侧',
      description: '每次只能移动最上方一块圆盘，大圆盘不能压在小圆盘上。',
      button: '进入汉诺塔挑战',
      features: ['3–8 层自由选择', '步数实时记录', '理论最优对照'],
      metrics: [
        { label: '当前层数', value: `${discCount} 层` },
        { label: '理论最少', value: `${2 ** discCount - 1} 步` },
        { label: '移动规则', value: '单盘移动' },
      ],
      stages: ['规划路径', '逐层迁移', '完成整塔'],
      recordNote: '完成整塔迁移后，本次层数、步数与用时会保存到个人战绩。',
    }
  },
}
