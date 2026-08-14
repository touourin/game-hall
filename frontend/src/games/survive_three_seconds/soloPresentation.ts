import { Timer } from '@lucide/vue'
import type { BuiltinGameSoloPresentation } from '../../game-platform/types'

export const surviveThreeSecondsSoloPresentation: BuiltinGameSoloPresentation = {
  icon: Timer,
  accent: '#d46b7b',
  content: () => ({
    category: '极限闪避',
    kicker: '方向控制与瞬时路线判断',
    title: '只要坚持三秒',
    description: '三段慢速弹幕会依次横向、纵向和交叉来袭。看清青色缺口及时换位，不要长期躲在边缘。',
    button: '进入三秒挑战',
    features: ['三段可读波次', '边缘清场压力', '服务端重放轨迹'],
    metrics: [
      { label: '生存目标', value: '3.00 秒' },
      { label: '轨迹采样', value: '60 Hz' },
      { label: '移动方式', value: '四方向' },
    ],
    stages: ['观察预警', '穿过缺口', '远离边缘'],
    recordNote: '完成后服务器会重放全部 180 帧输入，验证碰撞与存活结果。',
  }),
}
