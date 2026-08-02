import type { ModeGuideContent } from '../../components/uiTypes'

export const AVALON_COURT_GUIDE: ModeGuideContent = {
  ariaLabel: '王庭暗流完整说明',
  eyebrow: 'COURT UNDERCURRENT · 王庭暗流',
  title: '胜势已成，暗流未息',
  story: '三次任务的胜利本该让亚瑟的王庭迎来曙光，但忠诚之下仍潜伏着动摇。一名知道刺客身份的臣子站在光明一侧；若黑誓之刃准确找到他，他的誓言将被扭转，最后的胜负也会在王庭议事中重新开启。',
  feature: {
    label: '特殊角色',
    title: '异志之臣',
    description: '开局属于好人阵营，知道刺客是谁，并且只能提交任务成功牌。',
    details: [
      { label: '授刃前', text: '可以隐藏身份，也可以通过发言引导刺客找到自己。' },
      { label: '授刃命中', text: '会被黑誓之刃强制转化为邪恶阵营。' },
      { label: '最后议事', text: '由转化后的异志之臣亲自判断并刺杀梅林。' },
    ],
  },
  flowTitle: '新模式终局规则',
  steps: [
    { title: '好人三次任务成功', text: '后不会立刻结算，进入黑誓授刃。' },
    { title: '刺客从私密候选中寻找异志之臣', text: '；选错则好人立即获胜。' },
    { title: '授刃命中后异志之臣必定转化', text: '；除奥伯伦外，邪恶玩家随后互认。' },
    { title: '最后议事由异志之臣确认刺杀目标', text: '；刺中梅林邪恶获胜，否则好人获胜。' },
  ],
  footer: '模式差异：固定关闭湖中仙女与提前刺杀，其余组队、表决和任务规则不变。',
}
