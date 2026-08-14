import { Zap } from '@lucide/vue'
import type { BuiltinGameSoloPresentation } from '../../game-platform/types'

export const reactionSoloPresentation: BuiltinGameSoloPresentation = {
  icon: Zap,
  accent: '#7299a8',
  content: () => ({
    category: '反应速度',
    kicker: '视觉信号与瞬时反应',
    title: '挑战你的毫秒反应',
    description: '保持专注，等待信号真正亮起后再行动；抢跑同样会被准确记录。',
    button: '进入反应挑战',
    features: ['随机信号间隔', '抢跑即时判定', '三轮平均计榜'],
    metrics: [
      { label: '测试赛制', value: '3 轮' },
      { label: '记录精度', value: '毫秒级' },
      { label: '排名依据', value: '平均反应' },
    ],
    stages: ['保持待命', '捕捉信号', '记录反应'],
    recordNote: '完成三轮信号测试后，服务端将以平均反应时间记录成绩。',
  }),
}
