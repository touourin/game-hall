<template>
  <article class="avalon-court-guide" aria-label="王庭暗流完整说明">
    <header>
      <small>COURT UNDERCURRENT · 王庭暗流</small>
      <h3>胜势已成，暗流未息</h3>
      <p>
        三次任务的胜利本该让亚瑟的王庭迎来曙光，但忠诚之下仍潜伏着动摇。
        一名知道刺客身份的臣子站在光明一侧；若黑誓之刃准确找到他，他的誓言将被扭转，最后的胜负也会在王庭议事中重新开启。
      </p>
    </header>

    <section class="avalon-court-role">
      <div>
        <small>特殊角色</small>
        <strong>异志之臣</strong>
      </div>
      <p>开局属于好人阵营，知道刺客是谁，并且只能提交任务成功牌。</p>
      <ul>
        <li><b>授刃前</b> 可以隐藏身份，也可以通过发言引导刺客找到自己。</li>
        <li><b>授刃命中</b> 会被黑誓之刃强制转化为邪恶阵营。</li>
        <li><b>最后议事</b> 由转化后的异志之臣亲自判断并刺杀梅林。</li>
      </ul>
    </section>

    <section class="avalon-court-flow">
      <h4>新模式终局规则</h4>
      <ol>
        <li>
          <span>1</span><p><b>好人三次任务成功</b>后不会立刻结算，进入黑誓授刃。</p>
        </li>
        <li>
          <span>2</span><p><b>刺客从私密候选中寻找异志之臣</b>；选错则好人立即获胜。</p>
        </li>
        <li>
          <span>3</span><p><b>授刃命中后异志之臣必定转化</b>；除奥伯伦外，邪恶玩家随后互认。</p>
        </li>
        <li>
          <span>4</span><p><b>最后议事由异志之臣确认刺杀目标</b>；刺中梅林邪恶获胜，否则好人获胜。</p>
        </li>
      </ol>
    </section>

    <footer>模式差异：固定关闭湖中仙女与提前刺杀，其余组队、表决和任务规则不变。</footer>
  </article>
</template>

<style scoped>
.avalon-court-guide { display: grid; gap: 12px; color: var(--text); text-align: left; }
.avalon-court-guide > header { border: 1px solid color-mix(in srgb, var(--gold) 24%, var(--line)); border-radius: 15px; padding: 15px; background: radial-gradient(circle at 92% 0%, color-mix(in srgb, var(--gold) 12%, transparent), transparent 40%), rgba(var(--surface-deep-rgb), .72); }
.avalon-court-guide > header small, .avalon-court-role small { color: var(--gold); font-size: 9px; font-weight: 850; letter-spacing: .12em; }
.avalon-court-guide h3 { margin: 7px 0 8px; font-family: "Songti SC", "STSong", serif; font-size: 20px; letter-spacing: .04em; }
.avalon-court-guide p { margin: 0; color: var(--text-soft); font-size: 11px; line-height: 1.7; }
.avalon-court-role { border: 1px solid color-mix(in srgb, #ae5960 30%, var(--line)); border-radius: 15px; padding: 14px; background: color-mix(in srgb, #792e35 10%, var(--surface)); }
.avalon-court-role > div { display: grid; gap: 3px; margin-bottom: 8px; }
.avalon-court-role strong { color: #e5a0a2; font-family: "Songti SC", "STSong", serif; font-size: 18px; }
.avalon-court-role ul { display: grid; gap: 7px; margin: 11px 0 0; padding-left: 18px; color: var(--text-soft); font-size: 10px; line-height: 1.55; }
.avalon-court-role b, .avalon-court-flow b { color: var(--text); }
.avalon-court-flow { border: 1px solid var(--line); border-radius: 15px; padding: 14px; background: rgba(var(--surface-deep-rgb), .58); }
.avalon-court-flow h4 { margin: 0 0 11px; color: var(--gold); font-size: 12px; }
.avalon-court-flow ol { display: grid; gap: 9px; margin: 0; padding: 0; list-style: none; }
.avalon-court-flow li { display: grid; grid-template-columns: 25px minmax(0, 1fr); align-items: start; gap: 9px; }
.avalon-court-flow li > span { display: grid; place-items: center; width: 25px; height: 25px; border: 1px solid color-mix(in srgb, var(--gold) 35%, var(--line)); border-radius: 8px; color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, transparent); font-size: 10px; font-weight: 900; }
.avalon-court-guide footer { border-radius: 11px; padding: 10px 12px; color: var(--muted); background: color-mix(in srgb, var(--gold) 6%, transparent); font-size: 10px; line-height: 1.55; }
@media (max-width: 480px) {
  .avalon-court-guide > header, .avalon-court-role, .avalon-court-flow { padding: 12px; }
  .avalon-court-guide h3 { font-size: 18px; }
}
</style>
