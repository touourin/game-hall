<script setup lang="ts">
import type { OneNightRole } from './types'

defineProps<{
  roles: OneNightRole[]
  activeRoleCodes?: string[]
}>()

const alignmentLabels: Record<OneNightRole['alignment'], string> = {
  village: '村庄阵营',
  werewolf: '狼人阵营',
  tanner: '独立阵营',
}

const wakeOrder = ['狼人', '爪牙', '守夜人', '预言家', '强盗', '捣蛋鬼', '酒鬼', '失眠者']
</script>

<template>
  <div class="one-night-rules">
    <section class="one-night-rule-summary">
      <h3>一局怎么玩</h3>
      <ol>
        <li><strong>发牌：</strong>总牌数始终比玩家多三张，多出的三张放在中央。</li>
        <li><strong>夜晚：</strong>按开局身份依次行动；换牌后不会再次执行新身份的技能。</li>
        <li><strong>讨论：</strong>天亮后不限时自由讨论，所有人准备好后由房主开始投票。</li>
        <li><strong>投票：</strong>每人秘密投给一名其他玩家；最高票至少两票才会处决，并列最高者一起处决。</li>
      </ol>
      <p><strong>最重要：</strong>开局身份决定夜间技能，夜晚结束后的最终身份决定阵营、猎人效果与胜负。</p>
    </section>

    <section class="one-night-wake-order">
      <h3>夜间行动顺序</h3>
      <div>
        <template v-for="(label, index) in wakeOrder" :key="label">
          <span>{{ label }}</span><b v-if="index < wakeOrder.length - 1">→</b>
        </template>
      </div>
      <small>村民、皮匠和猎人没有主动夜间技能。</small>
    </section>

    <section class="one-night-role-guide">
      <header><h3>角色技能</h3><small>本游戏当前支持的全部角色</small></header>
      <div>
        <article
          v-for="role in roles"
          :key="role.code"
          :class="[`alignment-${role.alignment}`, { active: activeRoleCodes?.includes(role.code) }]"
        >
          <header>
            <strong>{{ role.label }}</strong>
            <span>{{ alignmentLabels[role.alignment] }}</span>
            <em v-if="activeRoleCodes?.includes(role.code)">本局使用</em>
          </header>
          <p>{{ role.description }}</p>
        </article>
      </div>
    </section>

    <section class="one-night-win-rules">
      <h3>胜负判定</h3>
      <ul>
        <li><strong>村庄阵营：</strong>场上有狼人时，至少处决一名狼人；场上没有狼人时，应让所有人各得一票，从而无人被处决。</li>
        <li><strong>狼人阵营：</strong>场上有狼人且没有狼人被处决；只有爪牙在场时，诱导村庄处决其他玩家。</li>
        <li><strong>皮匠：</strong>最终身份为皮匠、自己被处决且狼人阵营没有获胜时获胜；若皮匠与狼人同时死亡，皮匠可与村庄共同获胜。</li>
        <li><strong>猎人：</strong>猎人被处决时，他投票选择的玩家也会死亡，并继续参与本局胜负判定。</li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.one-night-rules { display:grid; gap:18px; text-align:left; --one-night-accent:var(--gold); }.one-night-rules section { display:grid; gap:10px; }.one-night-rules h3 { margin:0; font-size:16px; }.one-night-rules ol,.one-night-rules ul { margin:0; padding-left:20px; color:var(--text-soft); line-height:1.65; }.one-night-rules li + li { margin-top:5px; }.one-night-rule-summary > p { margin:0; border:1px solid color-mix(in srgb,var(--one-night-accent) 24%,var(--line)); border-radius:10px; padding:11px 12px; color:var(--text-soft); background:color-mix(in srgb,var(--one-night-accent) 8%,var(--surface-inset)); line-height:1.55; }
.one-night-wake-order > div { display:flex; align-items:center; flex-wrap:wrap; gap:6px; }.one-night-wake-order span { border:1px solid var(--line); border-radius:999px; padding:5px 8px; color:var(--one-night-accent); background:var(--surface-inset); font-size:11px; font-weight:800; }.one-night-wake-order b { color:var(--muted); }.one-night-wake-order small { color:var(--muted); }
.one-night-role-guide > header { display:flex; align-items:baseline; justify-content:space-between; gap:10px; }.one-night-role-guide > header small { color:var(--muted); }.one-night-role-guide > div { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; }.one-night-role-guide article { display:grid; gap:7px; border:1px solid var(--line); border-left:3px solid var(--green); border-radius:10px; padding:11px 12px; background:var(--surface-inset); }.one-night-role-guide article.alignment-werewolf { border-left-color:var(--red); }.one-night-role-guide article.alignment-tanner { border-left-color:var(--gold); }.one-night-role-guide article.active { box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--one-night-accent) 18%,transparent); }.one-night-role-guide article > header { display:flex; align-items:center; gap:7px; }.one-night-role-guide article strong { font-size:14px; }.one-night-role-guide article span,.one-night-role-guide article em { color:var(--muted); font-size:9px; font-style:normal; }.one-night-role-guide article em { margin-left:auto; border-radius:999px; padding:3px 6px; color:var(--one-night-accent); background:color-mix(in srgb,var(--one-night-accent) 11%,var(--surface-inset)); }.one-night-role-guide article p { margin:0; color:var(--text-soft); font-size:11px; line-height:1.55; }
.one-night-win-rules { border-top:1px solid var(--line); padding-top:16px; }
@media(max-width:620px){.one-night-role-guide > div{grid-template-columns:1fr}.one-night-role-guide > header{align-items:flex-start;flex-direction:column;gap:3px}}
</style>
