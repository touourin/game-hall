import { Footprints } from '@lucide/vue'
import type {
  BuiltinGameSoloMetric,
  BuiltinGameSoloPresentation,
} from '../../game-platform/types'

const difficultyMetrics: Record<string, readonly BuiltinGameSoloMetric[]> = {
  '5s': [
    { label: '目标时间', value: '5.00 秒' },
    { label: '云桥路段', value: '5 段' },
    { label: '轨迹采样', value: '60 Hz' },
  ],
  '8s': [
    { label: '目标时间', value: '8.00 秒' },
    { label: '云桥路段', value: '8 段' },
    { label: '轨迹采样', value: '60 Hz' },
  ],
  '10s': [
    { label: '目标时间', value: '10.00 秒' },
    { label: '云桥路段', value: '10 段' },
    { label: '轨迹采样', value: '60 Hz' },
  ],
}

export const criticalCrossingSoloPresentation: BuiltinGameSoloPresentation = {
  icon: Footprints,
  accent: '#ef7b4d',
  hasRuleSettings: true,
  content: options => ({
    category: '桥梁跑酷',
    kicker: '自动前进、分叉判断与动作配合',
    title: '在两路与三路云桥间疾行',
    description: '人物会自动向前奔跑；用 A/D 变道、W 跳过地面障碍、S 下蹲避开上方障碍。',
    button: '进入算途疾行',
    features: ['两路 / 三路随机分叉', '跑跳蹲人物动画', '服务端重放键盘轨迹'],
    metrics: difficultyMetrics[String(options.difficulty ?? '5s')]
      ?? difficultyMetrics['5s']!,
    stages: ['观察桥面', '变道与闪避', '冲过终点'],
    recordNote: '服务器会重放全部变道与动作输入，三种难度分别记录成绩。',
  }),
}
