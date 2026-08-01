<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  Crown,
  Handshake,
  QrCode,
  RotateCcw,
  Settings2,
  Undo2,
  UsersRound,
  X,
} from '@lucide/vue'
import ArcadeChatPanel from '../components/ArcadeChatPanel.vue'
import InviteLinkPanel from '../components/InviteLinkPanel.vue'
import GameRuleSettings from '../components/GameRuleSettings.vue'
import HostTransferNotice from '../components/HostTransferNotice.vue'
import RoomExitButton from '../components/RoomExitButton.vue'
import RoomDissolveButton from '../components/RoomDissolveButton.vue'
import RoomPageHeader from '../components/RoomPageHeader.vue'
import RoomInviteModal from '../components/RoomInviteModal.vue'
import RoomKickButton from '../components/RoomKickButton.vue'
import { useArcadeStore } from '../stores/arcade'
import type { ArcadeSnapshot } from '../types/arcade'
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
import PokerTable from '../games/poker/PokerTable.vue'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const ruleEditor = ref<Record<string, unknown> | null>(null)
const showQr = ref(false)
const missingPlayers = computed(
  () => Math.max(0, (props.snapshot.minimumPlayers ?? props.snapshot.requiredPlayers) - props.snapshot.players.length),
)
const availableSeats = computed(
  () => Math.max(0, props.snapshot.requiredPlayers - props.snapshot.players.length),
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
const roomHeaderEyebrow = computed(() => {
  const suffix = props.snapshot.gameKey === 'junqi'
    ? ` · ${props.snapshot.options.mode === 'flip' ? '翻棋军旗' : '暗军旗'}`
    : props.snapshot.gameKey === 'reaction'
      ? ' · 单人测试'
      : props.snapshot.gameKey === 'schulte'
        ? ' · 单人专注'
        : props.snapshot.gameKey === 'minesweeper'
          ? ` · ${props.snapshot.game.difficultyLabel}`
          : props.snapshot.gameKey === 'hanoi'
            ? ' · 单人益智'
            : ''
  return `${props.snapshot.gameName}${suffix}`
})
const roomHeaderTitle = computed(() => {
  const soloTitles: Partial<Record<ArcadeSnapshot['gameKey'], string>> = {
    reaction: '反应挑战',
    schulte: '舒尔特挑战',
    minesweeper: '扫雷挑战',
    hanoi: '汉诺塔挑战',
  }
  return soloTitles[props.snapshot.gameKey] ?? `房间 ${props.snapshot.roomCode}`
})
watch(
  () => [props.snapshot.phase, props.snapshot.gameKey] as const,
  ([phase]) => {
    if (phase !== 'lobby' || isSolo.value) showQr.value = false
  },
)
const exitDescription = computed(() => {
  if (props.snapshot.phase === 'lobby') {
    return '你会离开房间并让出座位；如果你是房主，房主将自动移交。'
  }
  if (props.snapshot.phase === 'finished') {
    return '你会退出当前房间并返回游戏大厅。'
  }
  return '你的座位和本局进度都会保留，可以从大厅随时返回。'
})

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
    :class="{ 'arcade-room--wide': ['poker', 'doudizhu', 'junqi', 'minesweeper'].includes(snapshot.gameKey) }"
  >
    <RoomPageHeader
      :eyebrow="roomHeaderEyebrow"
      :title="roomHeaderTitle"
    >
      <template #actions>
        <button
          v-if="snapshot.phase === 'lobby' && !isSolo"
          type="button"
          class="header-action"
          aria-label="显示加入二维码"
          @click="showQr = true"
        >
          <QrCode :size="21" />
        </button>
        <RoomDissolveButton
          v-if="snapshot.actions.canDissolve"
          :busy="arcade.busy"
          @confirm="arcade.dissolveRoom"
        />
        <RoomExitButton
          :busy="arcade.busy"
          :description="exitDescription"
          @confirm="arcade.leaveRoom"
        />
      </template>
    </RoomPageHeader>

    <HostTransferNotice :transfer-at="snapshot.hostTransferAt" />

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
        <RoomKickButton
          v-if="snapshot.actions.canKickPlayers && player.id !== snapshot.self.id"
          :player-name="player.name"
          :busy="arcade.busy"
          @confirm="arcade.kickPlayer(player.id)"
        />
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
      <p v-else-if="availableSeats > 0">已可开始，还可加入 {{ availableSeats }} 名玩家</p>
      <p v-else>人员已到齐，房主可以开始</p>
      <button v-if="!isSolo" type="button" class="room-code-share" aria-label="显示加入二维码" @click="showQr = true">
        {{ snapshot.roomCode }}
      </button>
      <InviteLinkPanel
        v-if="!isSolo"
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
      <PokerTable v-else-if="snapshot.gameKey === 'poker'" :snapshot="snapshot" />
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

    <RoomInviteModal
      v-if="showQr && snapshot.phase === 'lobby' && !isSolo"
      :url="inviteUrl"
      :room-code="snapshot.roomCode"
      :title="`扫描加入${snapshot.gameName}房间`"
      @close="showQr = false"
    />

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
.arcade-player-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap: 10px; margin-bottom: 24px; padding: 14px; }
.arcade-player-strip article { display: flex; gap: 10px; align-items: center; padding: 10px; border: 1px solid transparent; border-radius: 12px; }
.arcade-player-strip article > div { min-width: 0; flex: 1; }
.arcade-player-strip article.self { border-color: color-mix(in srgb, var(--gold) 40%, transparent); background: color-mix(in srgb, var(--gold) 7%, transparent); }
.arcade-player-strip article > span { width: 34px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 10px; color: var(--gold); background: color-mix(in srgb, var(--gold) 13%, transparent); font-weight: 900; }
.arcade-player-strip strong, .arcade-player-strip small { display: block; }
.arcade-player-strip small { margin-top: 2px; color: var(--muted); }
.arcade-player-strip small svg { vertical-align: -2px; color: var(--gold); }
.room-rule-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: -12px 0 24px; padding: 11px 13px; }
.room-rule-bar > div { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; min-width: 0; }
.room-rule-bar svg { flex: 0 0 auto; color: var(--gold); }
.room-rule-bar span { border: 1px solid var(--line); border-radius: 999px; padding: 4px 8px; color: var(--muted); background: rgba(0, 0, 0, .1); font-size: 10px; }
.room-rule-bar > button { flex: 0 0 auto; min-height: 36px; border: 1px solid color-mix(in srgb, var(--gold) 38%, var(--line)); border-radius: 10px; padding: 0 11px; color: var(--gold); background: color-mix(in srgb, var(--gold) 7%, transparent); font-weight: 850; }
.arcade-waiting { min-height: 390px; display: grid; place-items: center; align-content: center; gap: 12px; text-align: center; }
.arcade-waiting > svg { color: var(--gold); }
.arcade-waiting h2, .arcade-waiting p { margin: 0; }
.arcade-waiting p { color: var(--muted); }
.room-code-share { margin: 14px 0 0; border: 0; padding: 0; color: var(--text); background: transparent; font-size: 28px; font-weight: 800; letter-spacing: .18em; }
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
.rule-editor-modal { width: min(94vw, 620px); max-height: min(88vh, 820px); overflow-y: auto; }
.rule-editor-modal > p { margin: -4px 0 20px; color: var(--muted); }
.rule-editor-modal > .wide-button { margin-top: 22px; }
@media (max-width: 600px) {
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
