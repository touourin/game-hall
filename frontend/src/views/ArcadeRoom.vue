<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  ArrowLeft,
  Crown,
  Handshake,
  RotateCcw,
  Settings2,
  Trash2,
  Undo2,
  UserMinus,
  UsersRound,
  X,
} from '@lucide/vue'
import ArcadeChatPanel from '../components/ArcadeChatPanel.vue'
import InviteLinkPanel from '../components/InviteLinkPanel.vue'
import HostTransferNotice from '../components/HostTransferNotice.vue'
import GameRuleSettings from '../components/GameRuleSettings.vue'
import { useArcadeStore } from '../stores/arcade'
import type { ArcadePlayer, ArcadeSnapshot } from '../types/arcade'
import { gameRuleLabels, withDefaultGameRules } from '../gameRules'
import DoudizhuTable from '../games/doudizhu/DoudizhuTable.vue'
import GoBoard from '../games/go/GoBoard.vue'
import GomokuBoard from '../games/gomoku/GomokuBoard.vue'
import XiangqiBoard from '../games/xiangqi/XiangqiBoard.vue'
import JunqiBoard from '../games/junqi/JunqiBoard.vue'
import ReactionTest from '../games/reaction/ReactionTest.vue'
import SchulteGrid from '../games/schulte/SchulteGrid.vue'
import MinesweeperBoard from '../games/minesweeper/MinesweeperBoard.vue'
import HanoiGame from '../games/hanoi/HanoiGame.vue'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const confirmation = ref<
  { kind: 'kick'; player: ArcadePlayer } | { kind: 'dissolve' } | null
>(null)
const ruleEditor = ref<Record<string, unknown> | null>(null)
const missingPlayers = computed(
  () => props.snapshot.requiredPlayers - props.snapshot.players.length,
)
const inviteUrl = computed(() => {
  const url = new URL(window.location.href)
  url.search = ''
  url.searchParams.set('game', props.snapshot.gameKey)
  url.searchParams.set('room', props.snapshot.roomCode)
  return url.toString()
})
const selfRematchReady = computed(() =>
  props.snapshot.rematchReadyPlayerIds.includes(props.snapshot.self.id),
)
const isSolo = computed(() => ['reaction', 'schulte', 'minesweeper', 'hanoi'].includes(props.snapshot.gameKey))

async function confirmRoomAction() {
  if (!confirmation.value) return
  const succeeded = confirmation.value.kind === 'kick'
    ? await arcade.kickPlayer(confirmation.value.player.id)
    : await arcade.dissolveRoom()
  if (succeeded) confirmation.value = null
}

function openRuleEditor() {
  ruleEditor.value = withDefaultGameRules(
    props.snapshot.gameKey,
    props.snapshot.options,
  )
}

async function saveRules() {
  if (!ruleEditor.value) return
  if (await arcade.updateRules(ruleEditor.value)) ruleEditor.value = null
}

</script>

<template>
  <main
    class="arcade-room page-container"
    :class="{ 'arcade-room--wide': ['doudizhu', 'junqi', 'minesweeper'].includes(snapshot.gameKey) }"
  >
    <header class="arcade-room-header">
      <div>
        <small>{{ snapshot.gameName }}<template v-if="snapshot.gameKey === 'junqi'"> · {{ snapshot.options.mode === 'flip' ? '翻棋军旗' : '暗军旗' }}</template><template v-else-if="snapshot.gameKey === 'reaction'"> · 单人测试</template><template v-else-if="snapshot.gameKey === 'schulte'"> · 单人专注</template><template v-else-if="snapshot.gameKey === 'minesweeper'"> · {{ snapshot.game.difficultyLabel }}</template><template v-else-if="snapshot.gameKey === 'hanoi'"> · 单人益智</template></small>
        <h1>{{ snapshot.gameKey === 'reaction' ? '反应挑战' : snapshot.gameKey === 'schulte' ? '舒尔特挑战' : snapshot.gameKey === 'minesweeper' ? '扫雷挑战' : snapshot.gameKey === 'hanoi' ? '汉诺塔挑战' : `房间 ${snapshot.roomCode}` }}</h1>
      </div>
      <div class="arcade-room-actions">
        <button
          v-if="snapshot.actions.canDissolve"
          type="button"
          class="text-danger-button"
          @click="confirmation = { kind: 'dissolve' }"
        >
          <Trash2 :size="17" />解散房间
        </button>
        <button type="button" class="icon-button" aria-label="离开房间" @click="arcade.leaveRoom">
          <ArrowLeft :size="21" />
        </button>
      </div>
    </header>

    <section v-if="!isSolo" class="surface arcade-player-strip" aria-label="房间玩家">
      <article
        v-for="player in snapshot.players"
        :key="player.id"
        :class="{ self: player.id === snapshot.self.id }"
      >
        <span>{{ player.seat + 1 }}</span>
        <div>
          <strong>{{ player.name }}</strong>
          <small>
            <Crown v-if="player.isHost" :size="13" />
            {{ player.isHost ? '房主' : '玩家' }}
            {{ player.connected ? '· 在线' : '· 离线' }}
          </small>
        </div>
    <HostTransferNotice :transfer-at="snapshot.hostTransferAt" />

        <button
          v-if="snapshot.actions.canKickPlayers && player.id !== snapshot.self.id"
          type="button"
          class="kick-player-button"
          :aria-label="`移除${player.name}`"
          @click="confirmation = { kind: 'kick', player }"
        >
          <UserMinus :size="16" />
        </button>
      </article>
    </section>

    <section v-if="!isSolo" class="surface room-rule-bar" aria-label="房间规则">
      <div>
        <Settings2 :size="18" />
        <span v-for="label in gameRuleLabels(snapshot.gameKey, snapshot.options)" :key="label">{{ label }}</span>
      </div>
      <button v-if="snapshot.actions.canEditRules" type="button" @click="openRuleEditor">{{ snapshot.phase === 'finished' ? '修改下局规则' : '修改规则' }}</button>
    </section>

    <section v-if="snapshot.phase === 'lobby'" class="surface arcade-waiting">
      <UsersRound :size="48" />
      <h2>等待玩家到齐</h2>
      <p v-if="missingPlayers > 0">还需要 {{ missingPlayers }} 名玩家</p>
      <p v-else>人员已到齐，房主可以开始</p>
      <div class="room-code-share">
        <b>{{ snapshot.roomCode }}</b>
      </div>
      <InviteLinkPanel
        :url="inviteUrl"
        :share-title="`加入${snapshot.gameName}房间 ${snapshot.roomCode}`"
        :share-text="`点击链接加入我的${snapshot.gameName}房间 ${snapshot.roomCode}`"
      />
      <button
        v-if="snapshot.actions.canStart"
        type="button"
        class="primary-button"
        @click="arcade.startGame"
      >
        开始{{ snapshot.gameName }}
      </button>
    </section>

    <section v-else class="arcade-game-stage">
      <div v-if="snapshot.phase === 'finished' && !isSolo" class="surface result-banner">
        <small>本局结束</small>
        <h2>{{ snapshot.winReason }}</h2>
        <p>
          {{ snapshot.winnerPlayerIds.includes(snapshot.self.id) ? '你赢了' : '再接再厉' }}
          · 战绩已保存
        </p>
        <p class="rematch-progress">
          {{ snapshot.rematchReadyPlayerIds.length }} / {{ snapshot.players.length }} 人已准备
        </p>
        <button
          v-if="snapshot.actions.canRestart || selfRematchReady"
          type="button"
          class="primary-button"
          :disabled="selfRematchReady"
          @click="arcade.restartGame"
        >
          <RotateCcw :size="18" />
          {{ selfRematchReady ? '等待其他玩家' : '准备再来一局' }}
        </button>
      </div>

      <section
        v-if="snapshot.phase === 'playing' && (snapshot.actions.canRequestUndo || snapshot.actions.canRequestDraw || snapshot.request)"
        class="surface match-request-panel"
      >
        <template v-if="snapshot.request">
          <div>
            <strong>{{ snapshot.request.requesterName }}</strong>
            <span>申请{{ snapshot.request.kind === 'undo' ? '悔棋' : '和棋' }}</span>
          </div>
          <div v-if="snapshot.request.isMine" class="request-response-actions request-waiting-actions">
            <p>等待其他玩家确认</p>
            <button type="button" @click="arcade.resolveGameRequest(false)">撤回申请</button>
          </div>
          <div v-else class="request-response-actions">
            <button type="button" @click="arcade.resolveGameRequest(false)">拒绝</button>
            <button type="button" class="accept" @click="arcade.resolveGameRequest(true)">同意</button>
          </div>
        </template>
        <template v-else>
          <span>对局协商</span>
          <div>
            <button
              v-if="snapshot.actions.canRequestUndo"
              type="button"
              @click="arcade.requestGameAction('undo')"
            >
              <Undo2 :size="16" />申请悔棋
            </button>
            <button
              v-if="snapshot.actions.canRequestDraw"
              type="button"
              @click="arcade.requestGameAction('draw')"
            >
              <Handshake :size="16" />申请和棋
            </button>
          </div>
        </template>
      </section>

      <GomokuBoard v-if="snapshot.gameKey === 'gomoku'" :snapshot="snapshot" />
      <XiangqiBoard v-else-if="snapshot.gameKey === 'xiangqi'" :snapshot="snapshot" />
      <GoBoard v-else-if="snapshot.gameKey === 'go'" :snapshot="snapshot" />
      <DoudizhuTable v-else-if="snapshot.gameKey === 'doudizhu'" :snapshot="snapshot" />
      <JunqiBoard v-else-if="snapshot.gameKey === 'junqi'" :snapshot="snapshot" />
      <ReactionTest v-else-if="snapshot.gameKey === 'reaction'" :snapshot="snapshot" />
      <SchulteGrid v-else-if="snapshot.gameKey === 'schulte'" :snapshot="snapshot" />
      <MinesweeperBoard v-else-if="snapshot.gameKey === 'minesweeper'" :snapshot="snapshot" />
      <HanoiGame v-else-if="snapshot.gameKey === 'hanoi'" :snapshot="snapshot" />
    </section>

    <ArcadeChatPanel
      v-if="!isSolo"
      :messages="snapshot.chat.messages"
      :max-length="snapshot.chat.maxLength"
      :self-id="snapshot.self.id"
      :busy="arcade.busy"
      :send="arcade.sendChat"
    />

    <div v-if="confirmation" class="modal-backdrop" @click.self="confirmation = null">
      <section class="modal-card arcade-confirm-card" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭" @click="confirmation = null">
          <X :size="20" />
        </button>
        <Trash2 v-if="confirmation.kind === 'dissolve'" :size="28" />
        <UserMinus v-else :size="28" />
        <h2>{{ confirmation.kind === 'dissolve' ? '解散这个房间？' : `移除${confirmation.player.name}？` }}</h2>
        <p>{{ confirmation.kind === 'dissolve' ? '所有等待中的玩家都会返回大厅。' : '对方会立即离开当前房间。' }}</p>
        <div class="arcade-confirm-actions">
          <button type="button" @click="confirmation = null">取消</button>
          <button type="button" class="danger" @click="confirmRoomAction">确认</button>
        </div>
      </section>
    </div>

    <div v-if="ruleEditor" class="modal-backdrop" @click.self="ruleEditor = null">
      <section class="modal-card rule-editor-modal" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭规则设置" @click="ruleEditor = null">
          <X :size="20" />
        </button>
        <span class="modal-icon"><Settings2 :size="25" /></span>
        <h2>房间规则</h2>
        <p>{{ snapshot.phase === 'finished' ? '保存后所有玩家会返回等待阶段，新规则从下一局生效。' : '保存后会同步给房间中的所有玩家，开局后不可修改。' }}</p>
        <GameRuleSettings v-model="ruleEditor" :game-key="snapshot.gameKey" />
        <button type="button" class="primary-button wide-button" :disabled="arcade.busy" @click="saveRules">保存规则</button>
      </section>
    </div>
  </main>
</template>

<style scoped>
.arcade-room { padding-bottom: 70px; }
.arcade-room-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.arcade-room-header small { color: var(--gold); letter-spacing: .14em; }
.arcade-room-header h1 { margin: 4px 0 0; font-size: clamp(24px, 4vw, 38px); }
.arcade-room-actions { display: flex; align-items: center; gap: 8px; }
.text-danger-button { display: inline-flex; align-items: center; gap: 6px; min-height: 42px; border: 1px solid rgba(225, 114, 114, .3); border-radius: 11px; padding: 0 12px; color: #efaaa7; background: rgba(133, 47, 52, .16); font-weight: 800; }
.arcade-player-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap: 10px; margin-bottom: 24px; padding: 14px; }
.arcade-player-strip article { display: flex; gap: 10px; align-items: center; padding: 10px; border: 1px solid transparent; border-radius: 12px; }
.arcade-player-strip article > div { min-width: 0; flex: 1; }
.arcade-player-strip article.self { border-color: color-mix(in srgb, var(--gold) 40%, transparent); background: color-mix(in srgb, var(--gold) 7%, transparent); }
.arcade-player-strip article > span { width: 34px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 10px; color: var(--gold); background: color-mix(in srgb, var(--gold) 13%, transparent); font-weight: 900; }
.arcade-player-strip strong, .arcade-player-strip small { display: block; }
.arcade-player-strip small { margin-top: 2px; color: var(--muted); }
.arcade-player-strip small svg { vertical-align: -2px; color: var(--gold); }
.kick-player-button { display: grid; flex: 0 0 auto; place-items: center; width: 34px; aspect-ratio: 1; border: 1px solid rgba(225, 114, 114, .24); border-radius: 10px; color: #efaaa7; background: rgba(133, 47, 52, .12); }
.room-rule-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: -12px 0 24px; padding: 11px 13px; }
.room-rule-bar > div { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; min-width: 0; }
.room-rule-bar svg { flex: 0 0 auto; color: var(--gold); }
.room-rule-bar span { border: 1px solid var(--line); border-radius: 999px; padding: 4px 8px; color: var(--muted); background: rgba(0, 0, 0, .1); font-size: 10px; }
.room-rule-bar > button { flex: 0 0 auto; min-height: 36px; border: 1px solid color-mix(in srgb, var(--gold) 38%, var(--line)); border-radius: 10px; padding: 0 11px; color: var(--gold); background: color-mix(in srgb, var(--gold) 7%, transparent); font-weight: 850; }
.arcade-waiting { min-height: 390px; display: grid; place-items: center; align-content: center; gap: 12px; text-align: center; }
.arcade-waiting > svg { color: var(--gold); }
.arcade-waiting h2, .arcade-waiting p { margin: 0; }
.arcade-waiting p { color: var(--muted); }
.room-code-share { margin: 14px 0 0; display: flex; align-items: center; }
.room-code-share b { font-size: 28px; letter-spacing: .18em; }
.arcade-waiting :deep(.invite-link-panel) { width: min(100%, 620px); }
.arcade-game-stage { display: grid; gap: 22px; }
.result-banner { padding: 18px; text-align: center; }
.result-banner small { color: var(--gold); }
.result-banner h2 { margin: 5px 0; }
.result-banner p { color: var(--muted); }
.result-banner .rematch-progress { margin-bottom: 0; font-size: 11px; }
.result-banner .primary-button { margin: 12px auto 0; }
.match-request-panel { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 15px; }
.match-request-panel > span { color: var(--muted); font-weight: 800; }
.match-request-panel > div { display: flex; align-items: center; gap: 8px; }
.match-request-panel > div:first-child { display: grid; gap: 2px; }
.match-request-panel > div:first-child span { color: var(--muted); }
.match-request-panel p { margin: 0; color: var(--gold); }
.match-request-panel button { display: inline-flex; align-items: center; gap: 6px; min-height: 38px; border: 1px solid var(--line); border-radius: 10px; padding: 0 11px; color: var(--text); background: transparent; font-weight: 800; }
.request-waiting-actions { justify-content: flex-end; }
.request-response-actions button.accept { border-color: color-mix(in srgb, var(--gold) 38%, var(--line)); color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, transparent); }
.arcade-confirm-card { width: min(92vw, 430px); text-align: center; }
.arcade-confirm-card > svg { color: #efaaa7; }
.arcade-confirm-card h2 { margin: 12px 0 6px; }
.arcade-confirm-card p { color: var(--muted); }
.arcade-confirm-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: 18px; }
.arcade-confirm-actions button { min-height: 43px; border: 1px solid var(--line); border-radius: 11px; color: var(--text); background: transparent; font-weight: 850; }
.arcade-confirm-actions button.danger { border-color: rgba(225, 114, 114, .34); color: #f1b0b0; background: rgba(133, 47, 52, .18); }
.rule-editor-modal { width: min(94vw, 620px); max-height: min(88vh, 820px); overflow-y: auto; }
.rule-editor-modal > p { margin: -4px 0 20px; color: var(--muted); }
.rule-editor-modal > .wide-button { margin-top: 22px; }
@media (max-width: 600px) {
  .text-danger-button { width: 42px; padding: 0; justify-content: center; font-size: 0; }
  .match-request-panel { align-items: stretch; flex-direction: column; }
  .match-request-panel > div { display: grid; grid-template-columns: 1fr 1fr; }
  .match-request-panel button { justify-content: center; }
  .room-rule-bar { align-items: stretch; flex-direction: column; }
  .room-rule-bar > button { width: 100%; }
}
@media (min-width: 860px) {
  .arcade-room.arcade-room--wide { width: min(100%, 1080px); }
}
</style>
