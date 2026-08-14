import { Blocks } from '@lucide/vue'
import type { BuiltinGameSoloPresentation } from '../../game-platform/types'

export const tetrisSoloPresentation: BuiltinGameSoloPresentation = {
  icon: Blocks,
  accent: '#719aa3',
  hasRuleSettings: true,
  content: (options) => {
    const timed = options.challengeMode !== 'endless'
    const duration = Number(options.durationSeconds ?? 180)
    return {
      category: '空间排列',
      kicker: '空间规划与即时决策',
      title: '排列方块，持续消行',
      description: timed
        ? `在 ${duration / 60} 分钟内预判方块，用旋转、暂存和快速落底冲击高分。`
        : '预判接下来的方块，用旋转、暂存和快速落底保持棋盘整洁，冲击更高分数。',
      button: '进入落块挑战',
      features: ['7-bag 公平随机', '键盘与拇指控制', timed ? '到点自动结算' : '堆顶自动结算'],
      metrics: [
        { label: '挑战模式', value: timed ? `${duration / 60} 分钟` : '无限' },
        { label: '标准棋盘', value: '10 × 20' },
        { label: '方块种类', value: '7 种' },
      ],
      stages: ['规划落点', '排列消行', '挑战高分'],
      recordNote: timed
        ? '倒计时结束或方块提前堆顶后，本轮成绩会保存到对应时长排行榜。'
        : '方块堆到顶部后，本轮得分、消行数与等级会保存到无限挑战排行榜。',
    }
  },
}
