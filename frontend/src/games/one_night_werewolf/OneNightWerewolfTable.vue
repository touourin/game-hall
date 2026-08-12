<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  Check,
  Eye,
  Moon,
  Shuffle,
  Sunrise,
  Vote,
} from '@lucide/vue'
import PressRevealCard from '../../components/PressRevealCard.vue'
import type { ArcadeSnapshot } from '../../types/arcade'
import { useArcadeStore } from '../../stores/arcade'
import type { OneNightWerewolfView } from './types'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const roleSeen = ref(false)
const selectedPlayerIds = ref<string[]>([])
const selectedCenterIndices = ref<number[]>([])
const voteTargetId = ref('')

const game = computed(() => props.snapshot.game as unknown as OneNightWerewolfView)
const selfRole = computed(() => game.value.self.initialRole)
const nightRole = computed(() => game.value.legal.nightRole ?? null)
const selectablePlayers = computed(() => props.snapshot.players.filter(
  player => game.value.legal.targetPlayerIds?.includes(player.id),
))
const voteTargets = computed(() => props.snapshot.players.filter(
  player => game.value.legal.voteTargetPlayerIds?.includes(player.id),
))
const requiredPlayerTargets = computed(() => nightRole.value === 'troublemaker' ? 2 : 1)
const centerSelectionCount = computed(() => game.value.legal.centerSelectionCount ?? 0)
const nightActionReady = computed(() => {
  if (!nightRole.value) return false
  if (['minion', 'mason', 'insomniac'].includes(nightRole.value)) return true
  if (nightRole.value === 'werewolf' && centerSelectionCount.value === 0) return true
  if (nightRole.value === 'seer') {
    return selectedPlayerIds.value.length === 1
      || selectedCenterIndices.value.length === 2
  }
  if (centerSelectionCount.value > 0) return selectedCenterIndices.value.length === centerSelectionCount.value
  return selectedPlayerIds.value.length === requiredPlayerTargets.value
})

watch(
  () => [props.snapshot.phase, props.snapshot.revision],
  () => {
    selectedPlayerIds.value = []
    selectedCenterIndices.value = []
    voteTargetId.value = ''
    if (props.snapshot.phase !== 'role_reveal') roleSeen.value = false
  },
)

function playerLabel(playerId: string | null | undefined): string {
  const player = props.snapshot.players.find(item => item.id === playerId)
  return player ? `${player.seat + 1}号 ${player.name}` : '未知玩家'
}

function togglePlayer(playerId: string) {
  selectedCenterIndices.value = []
  if (nightRole.value !== 'troublemaker') {
    selectedPlayerIds.value = [playerId]
    return
  }
  if (selectedPlayerIds.value.includes(playerId)) {
    selectedPlayerIds.value = selectedPlayerIds.value.filter(id => id !== playerId)
    return
  }
  if (selectedPlayerIds.value.length < 2) selectedPlayerIds.value.push(playerId)
}

function toggleCenter(index: number) {
  selectedPlayerIds.value = []
  if (selectedCenterIndices.value.includes(index)) {
    selectedCenterIndices.value = selectedCenterIndices.value.filter(item => item !== index)
    return
  }
  if (selectedCenterIndices.value.length < centerSelectionCount.value) {
    selectedCenterIndices.value.push(index)
  }
}

function submitNightAction() {
  if (!nightActionReady.value) return
  const role = nightRole.value
  if (role === 'seer' && centerSelectionCount.value === 2 && selectedCenterIndices.value.length === 2) {
    void arcade.action('night_action', { centerIndices: selectedCenterIndices.value })
    return
  }
  if (centerSelectionCount.value === 1) {
    void arcade.action('night_action', { centerIndex: selectedCenterIndices.value[0] })
    return
  }
  if (role === 'troublemaker') {
    void arcade.action('night_action', { targetPlayerIds: selectedPlayerIds.value })
    return
  }
  if (['robber', 'seer'].includes(role ?? '')) {
    void arcade.action('night_action', { targetPlayerId: selectedPlayerIds.value[0] })
    return
  }
  void arcade.action('night_action')
}

function skipOptionalAction() {
  void arcade.action('night_action', { skip: true })
}

function submitVote() {
  if (!voteTargetId.value) return
  void arcade.action('vote', { targetPlayerId: voteTargetId.value })
}
</script>

<template>
  <div class="one-night-table">
    <section v-if="snapshot.phase === 'role_reveal'" class="one-night-phase">
      <header class="one-night-heading">
        <span><Eye :size="22" /></span>
        <div><small>SECRET ROLE</small><h2>确认你的开局身份</h2><p>身份可能在夜间被交换。先记住你开局拿到的牌。</p></div>
      </header>

      <div class="surface one-night-role-deck" aria-label="本局角色牌">
        <strong>本局角色牌</strong>
        <span v-for="(role, index) in game.roleDeck" :key="`${role.code}-${index}`">{{ role.label }}</span>
      </div>

      <PressRevealCard
        v-if="selfRole"
        :title="selfRole.label"
        :subtitle="selfRole.alignment === 'werewolf' ? '狼人阵营' : selfRole.alignment === 'tanner' ? '独立阵营' : '村庄阵营'"
        @seen="roleSeen = true"
      >
        <p class="one-night-secret">{{ selfRole.description }}</p>
      </PressRevealCard>

      <button
        v-if="game.legal.canConfirmRole"
        type="button"
        class="primary-button wide-button"
        :disabled="!roleSeen"
        @click="arcade.action('confirm_role')"
      ><Check :size="19" />我已记住身份</button>
      <div v-else class="one-night-wait"><span />已确认，等待其他玩家</div>
      <p class="one-night-progress">已确认 {{ game.roleConfirmedCount }} / {{ snapshot.players.length }}</p>
    </section>

    <section v-else-if="snapshot.phase === 'night'" class="one-night-phase night-phase">
      <header class="one-night-heading">
        <span><Moon :size="22" /></span>
        <div><small>NIGHT SEQUENCE</small><h2>{{ game.night.isMyTurn ? '轮到你在夜里行动' : '月夜仍在继续' }}</h2><p>{{ game.night.isMyTurn ? game.night.prompt : '请保持安静，等待属于你的身份被唤醒。' }}</p></div>
      </header>

      <div v-if="game.night.isMyTurn" class="surface night-action-card">
        <div v-if="selectablePlayers.length" class="one-night-targets">
          <button
            v-for="player in selectablePlayers"
            :key="player.id"
            type="button"
            :class="{ selected: selectedPlayerIds.includes(player.id) }"
            @click="togglePlayer(player.id)"
          ><b>{{ player.seat + 1 }}</b><span>{{ player.name }}</span></button>
        </div>
        <div v-if="centerSelectionCount" class="one-night-centers">
          <button
            v-for="index in [0, 1, 2]"
            :key="index"
            type="button"
            :class="{ selected: selectedCenterIndices.includes(index) }"
            @click="toggleCenter(index)"
          ><Moon :size="18" /><span>中央 {{ index + 1 }}</span></button>
        </div>
        <div class="night-actions">
          <button
            v-if="['robber', 'troublemaker'].includes(nightRole ?? '')"
            type="button"
            class="secondary-button"
            @click="skipOptionalAction"
          >不使用能力</button>
          <button type="button" class="primary-button" :disabled="!nightActionReady" @click="submitNightAction">
            <Shuffle v-if="['robber', 'troublemaker', 'drunk'].includes(nightRole ?? '')" :size="18" />
            <Check v-else :size="18" />
            确认夜间行动
          </button>
        </div>
      </div>
      <div v-else class="surface moon-waiting"><Moon :size="44" /><strong>闭眼等待</strong><span>其他身份正在依次行动，你的私密信息不会公开。</span></div>
    </section>

    <section v-else-if="snapshot.phase === 'discussion'" class="one-night-phase">
      <header class="one-night-heading dawn">
        <span><Sunrise :size="22" /></span>
        <div><small>DAYBREAK DISCUSSION</small><h2>天亮了，找出谁变成了狼人</h2><p>结合开局身份、夜间结果和大家的发言推理。最终身份可能已经改变。</p></div>
      </header>

      <div class="surface discussion-status"><Sunrise :size="25" /><span><strong>自由讨论，不限时间</strong><small>确认大家都已完成发言后，由房主开始秘密投票。</small></span></div>
      <PressRevealCard v-if="selfRole" title="我的私密信息" subtitle="按住回顾开局身份与夜间结果" hint="讨论时按住查看">
        <p class="one-night-secret"><strong>开局：{{ selfRole.label }}</strong><br>{{ selfRole.description }}</p>
        <div v-if="game.self.nightResults.length" class="one-night-results">
          <span v-for="result in game.self.nightResults" :key="`${result.kind}-${result.text}`">{{ result.text }}</span>
        </div>
        <p v-else class="one-night-secret">本局没有额外夜间信息。</p>
      </PressRevealCard>
      <button v-if="game.legal.canStartVote" type="button" class="primary-button wide-button" @click="arcade.action('start_vote')"><Vote :size="18" />开始投票</button>
      <p v-else class="one-night-progress">等待房主开始投票</p>
    </section>

    <section v-else-if="snapshot.phase === 'voting'" class="one-night-phase">
      <header class="one-night-heading vote-heading">
        <span><Vote :size="22" /></span>
        <div><small>FINAL BALLOT</small><h2>秘密投出唯一一票</h2><p>所有人提交后同时结算。得票最高且至少两票的玩家会被处决。</p></div>
      </header>
      <div v-if="!game.hasVoted" class="surface final-vote-card">
        <label for="one-night-vote">你认为谁是狼人？</label>
        <select id="one-night-vote" v-model="voteTargetId">
          <option value="">请选择玩家</option>
          <option v-for="player in voteTargets" :key="player.id" :value="player.id">{{ player.seat + 1 }}号 {{ player.name }}</option>
        </select>
        <button type="button" class="primary-button" :disabled="!voteTargetId" @click="submitVote">锁定投票</button>
      </div>
      <div v-else class="surface moon-waiting"><Check :size="38" /><strong>投票已锁定</strong><span>等待其他玩家提交，不会提前公开票型。</span></div>
      <p class="one-night-progress">已投票 {{ game.votesSubmitted }} / {{ snapshot.players.length }}</p>
    </section>

    <section v-else-if="snapshot.phase === 'finished' && game.resolution" class="one-night-phase resolution-phase">
      <header class="one-night-heading">
        <span><Sunrise :size="22" /></span>
        <div><small>ROLE REVEAL</small><h2>月夜真相</h2><p>开局身份、换牌后的最终身份与投票全部公开。</p></div>
      </header>
      <div class="resolution-grid">
        <article
          v-for="item in game.resolution.players"
          :key="item.playerId"
          class="surface resolution-player"
          :class="{ eliminated: item.eliminated, winner: item.won }"
        >
          <header><strong>{{ playerLabel(item.playerId) }}</strong><span v-if="item.won">获胜</span></header>
          <dl><div><dt>开局</dt><dd>{{ item.initialRole.label }}</dd></div><div><dt>最终</dt><dd>{{ item.finalRole.label }}</dd></div></dl>
          <p>{{ item.voteCount }} 票 · 投给 {{ playerLabel(item.votedForId) }}{{ item.eliminated ? ' · 被处决' : '' }}</p>
        </article>
      </div>
      <div class="surface revealed-centers"><strong>最终中央三牌</strong><span v-for="(role, index) in game.resolution.centerRoles" :key="index">{{ index + 1 }} · {{ role.label }}</span></div>
    </section>
  </div>
</template>

<style scoped>
.one-night-table,.one-night-phase { display: grid; gap: 16px; }
.one-night-phase { width: min(100%, 880px); margin: 0 auto; }
.one-night-heading { display: grid; grid-template-columns: auto minmax(0,1fr); align-items: center; gap: 13px; }
.one-night-heading > span { width: 44px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb,#9dafea 40%,var(--line)); border-radius: 14px; color: #b9c7ff; background: color-mix(in srgb,#7186d6 12%,var(--surface-inset)); }
.one-night-heading small { color: #9dafea; font-size: 9px; font-weight: 900; letter-spacing: .16em; }.one-night-heading h2 { margin: 2px 0 3px; font-family: "Songti SC",serif; font-size: clamp(22px,4vw,30px); }.one-night-heading p { margin: 0; color: var(--muted); line-height: 1.55; }
.one-night-secret { max-width: 320px; margin: 0; color: var(--text-soft); font-size: 12px; line-height: 1.65; text-align: center; }.one-night-wait,.moon-waiting { display: flex; align-items: center; justify-content: center; gap: 9px; color: var(--muted); }.one-night-wait > span { width: 8px; aspect-ratio:1; border-radius:50%; background:#9dafea; box-shadow:0 0 14px #9dafea; }.one-night-progress { margin:0; color:var(--muted); text-align:center; }
.one-night-role-deck { padding:13px; display:flex; align-items:center; justify-content:center; flex-wrap:wrap; gap:7px; }.one-night-role-deck strong { margin-right:4px; font-size:12px; }.one-night-role-deck span { border:1px solid rgba(157,175,234,.18); border-radius:999px; padding:5px 8px; color:#b9c7ff; background:rgba(119,139,215,.09); font-size:10px; font-weight:800; }
.night-phase { min-height: 430px; }.night-action-card { padding: clamp(16px,4vw,24px); display:grid; gap:16px; }.one-night-targets,.one-night-centers { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:9px; }.one-night-targets button,.one-night-centers button { min-height:76px; display:grid; place-items:center; gap:5px; border:1px solid var(--line); border-radius:13px; color:var(--text); background:var(--surface-inset); cursor:pointer; }.one-night-targets b { width:28px; aspect-ratio:1; display:grid; place-items:center; border-radius:50%; color:#b9c7ff; background:rgba(119,139,215,.15); }.one-night-targets button.selected,.one-night-centers button.selected { border-color:#9dafea; background:rgba(119,139,215,.13); box-shadow:inset 0 0 0 1px rgba(157,175,234,.18); }.night-actions { display:flex; justify-content:flex-end; gap:9px; }.moon-waiting { min-height:230px; padding:30px; flex-direction:column; text-align:center; }.moon-waiting svg { color:#9dafea; }.moon-waiting strong { font-family:"Songti SC",serif; font-size:24px; }.moon-waiting span { max-width:380px; color:var(--muted); line-height:1.55; }
.discussion-status { display:flex; align-items:center; justify-content:center; gap:12px; padding:16px; color:#b9c7ff; }.discussion-status span { display:grid; gap:3px; }.discussion-status small { color:var(--muted); line-height:1.5; }.discussion-status strong { font-size:16px; }.one-night-results { display:grid; gap:6px; max-width:320px; }.one-night-results span { border:1px solid rgba(157,175,234,.2); border-radius:10px; padding:8px; background:rgba(11,16,39,.55); font-size:11px; line-height:1.5; }
.final-vote-card { padding:22px; display:grid; gap:12px; }.final-vote-card label { font-weight:850; }.final-vote-card select { min-height:48px; border:1px solid var(--line); border-radius:11px; padding:0 12px; color:var(--text); background:var(--surface-inset); }
.resolution-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:10px; }.resolution-player { padding:15px; display:grid; gap:12px; }.resolution-player.eliminated { border-color:color-mix(in srgb,var(--red) 45%,var(--line)); }.resolution-player.winner { box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--green) 35%,transparent); }.resolution-player header { display:flex; align-items:center; justify-content:space-between; gap:8px; }.resolution-player header span { border-radius:999px; padding:4px 7px; color:var(--green); background:color-mix(in srgb,var(--green) 10%,transparent); font-size:10px; }.resolution-player dl { margin:0; display:grid; grid-template-columns:1fr 1fr; gap:8px; }.resolution-player dl div { border-radius:9px; padding:8px; background:var(--surface-inset); }.resolution-player dt { color:var(--muted); font-size:10px; }.resolution-player dd { margin:3px 0 0; font-weight:850; }.resolution-player p { margin:0; color:var(--muted); font-size:11px; }.revealed-centers { padding:15px; display:flex; align-items:center; flex-wrap:wrap; gap:8px; }.revealed-centers strong { margin-right:auto; }.revealed-centers span { border-radius:999px; padding:6px 9px; color:#b9c7ff; background:rgba(119,139,215,.12); }
@media(max-width:560px){.night-actions{align-items:stretch;flex-direction:column}.one-night-targets{grid-template-columns:repeat(2,minmax(0,1fr))}.resolution-grid{grid-template-columns:1fr}.revealed-centers{align-items:stretch;flex-direction:column}.revealed-centers strong{margin:0}.revealed-centers span{text-align:center}}
</style>
