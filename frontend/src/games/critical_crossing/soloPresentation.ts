import { ScanLine } from '@lucide/vue'
import type {
  BuiltinGameSoloMetric,
  BuiltinGameSoloPresentation,
} from '../../game-platform/types'

const difficultyMetrics: Record<string, readonly BuiltinGameSoloMetric[]> = {
  '5s': [
    { label: '目标时间', value: '5.00 秒' },
    { label: '脉冲序列', value: '5 轮' },
    { label: '轨迹采样', value: '60 Hz' },
  ],
  '8s': [
    { label: '目标时间', value: '8.00 秒' },
    { label: '脉冲序列', value: '8 轮' },
    { label: '轨迹采样', value: '60 Hz' },
  ],
  '10s': [
    { label: '目标时间', value: '10.00 秒' },
    { label: '脉冲序列', value: '10 轮' },
    { label: '轨迹采样', value: '60 Hz' },
  ],
}

export const criticalCrossingSoloPresentation: BuiltinGameSoloPresentation = {
  icon: ScanLine,
  accent: '#6a9eaa',
  hasRuleSettings: true,
  content: options => ({
    category: '路径穿越',
    kicker: '缺口识别与连续路线判断',
    title: '沿着安全缺口穿过临界场',
    description: '观察边缘预警，在横向、纵向和交叉脉冲抵达前完成换位；不要长期停留在封锁边界。',
    button: '进入临界穿越',
    features: ['三档目标时间', '可读脉冲缺口', '服务端重放轨迹'],
    metrics: difficultyMetrics[String(options.difficulty ?? '5s')]
      ?? difficultyMetrics['5s']!,
    stages: ['读取预警', '移动到缺口', '持续穿越'],
    recordNote: '服务器会重放全部方向输入，三种难度分别记录成绩。',
  }),
}
