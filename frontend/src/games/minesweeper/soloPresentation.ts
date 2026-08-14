import { Bomb } from '@lucide/vue'
import type {
  BuiltinGameSoloMetric,
  BuiltinGameSoloPresentation,
} from '../../game-platform/types'

const difficultyMetrics: Record<string, readonly BuiltinGameSoloMetric[]> = {
  beginner: [
    { label: '雷区规格', value: '9 × 9' },
    { label: '地雷数量', value: '10' },
    { label: '安全方格', value: '71' },
  ],
  intermediate: [
    { label: '雷区规格', value: '16 × 16' },
    { label: '地雷数量', value: '40' },
    { label: '安全方格', value: '216' },
  ],
  expert: [
    { label: '雷区规格', value: '16 × 30' },
    { label: '地雷数量', value: '99' },
    { label: '安全方格', value: '381' },
  ],
}

export const minesweeperSoloPresentation: BuiltinGameSoloPresentation = {
  icon: Bomb,
  accent: '#6e9d89',
  hasRuleSettings: true,
  content: (options) => ({
    category: '逻辑排雷',
    kicker: '逻辑排雷与风险控制',
    title: '清除所有安全方格',
    description: '从数字线索推演雷区结构；首次点击必定安全，插旗与清除均为经典规则。',
    button: '进入扫雷挑战',
    features: ['首次点击安全', '电脑与触屏适配', '三种难度独立计榜'],
    metrics: difficultyMetrics[String(options.difficulty ?? 'beginner')]
      ?? difficultyMetrics.beginner!,
    stages: ['观察线索', '标记雷区', '清空方格'],
    recordNote: '仅完整清除全部安全方格的成绩会进入对应难度排行榜。',
  }),
}
