<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeft, Copy, Crown, RotateCcw, UsersRound } from '@lucide/vue'
import { useArcadeStore } from '../stores/arcade'
import type { ArcadeSnapshot } from '../types/arcade'
import DoudizhuTable from '../games/doudizhu/DoudizhuTable.vue'
import GoBoard from '../games/go/GoBoard.vue'
import GomokuBoard from '../games/gomoku/GomokuBoard.vue'
import XiangqiBoard from '../games/xiangqi/XiangqiBoard.vue'
import JunqiBoard from '../games/junqi/JunqiBoard.vue'
import ReactionTest from '../games/reaction/ReactionTest.vue'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
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

async function copyInvite() {
  try {
    await navigator.clipboard.writeText(inviteUrl.value)
  } catch {
    // Browsers without clipboard permission can still copy the visible room code.
  }
}
</script>

<template>
  <main class="arcade-room page-container">
    <header class="arcade-room-header">
      <div>
        <small>{{ snapshot.gameName }}<template v-if="snapshot.gameKey === 'junqi'"> · {{ snapshot.options.mode === 'flip' ? '翻棋军旗' : '暗军旗' }}</template><template v-else-if="snapshot.gameKey === 'reaction'"> · 单人测试</template></small>
        <h1>{{ snapshot.gameKey === 'reaction' ? '三轮反应挑战' : `房间 ${snapshot.roomCode}` }}</h1>
      </div>
      <button type="button" class="icon-button" aria-label="离开房间" @click="arcade.leaveRoom">
        <ArrowLeft :size="21" />
      </button>
    </header>

    <section v-if="snapshot.gameKey !== 'reaction'" class="surface arcade-player-strip" aria-label="房间玩家">
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
      </article>
    </section>

    <section v-if="snapshot.phase === 'lobby'" class="surface arcade-waiting">
      <UsersRound :size="48" />
      <h2>等待玩家到齐</h2>
      <p v-if="missingPlayers > 0">还需要 {{ missingPlayers }} 名玩家</p>
      <p v-else>人员已到齐，房主可以开始</p>
      <div class="room-code-share">
        <b>{{ snapshot.roomCode }}</b>
        <button type="button" @click="copyInvite"><Copy :size="17" />复制邀请链接</button>
      </div>
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
      <div v-if="snapshot.phase === 'finished' && snapshot.gameKey !== 'reaction'" class="surface result-banner">
        <small>本局结束</small>
        <h2>{{ snapshot.winReason }}</h2>
        <p>
          {{ snapshot.winnerPlayerIds.includes(snapshot.self.id) ? '你赢了' : '再接再厉' }}
          · 战绩已保存
        </p>
        <button
          v-if="snapshot.actions.canRestart"
          type="button"
          class="primary-button"
          @click="arcade.restartGame"
        >
          <RotateCcw :size="18" /> 再来一局
        </button>
      </div>

      <GomokuBoard v-if="snapshot.gameKey === 'gomoku'" :snapshot="snapshot" />
      <XiangqiBoard v-else-if="snapshot.gameKey === 'xiangqi'" :snapshot="snapshot" />
      <GoBoard v-else-if="snapshot.gameKey === 'go'" :snapshot="snapshot" />
      <DoudizhuTable v-else-if="snapshot.gameKey === 'doudizhu'" :snapshot="snapshot" />
      <JunqiBoard v-else-if="snapshot.gameKey === 'junqi'" :snapshot="snapshot" />
      <ReactionTest v-else-if="snapshot.gameKey === 'reaction'" :snapshot="snapshot" />
    </section>
  </main>
</template>

<style scoped>
.arcade-room { padding-bottom: 70px; }
.arcade-room-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.arcade-room-header small { color: var(--gold); letter-spacing: .14em; }
.arcade-room-header h1 { margin: 4px 0 0; font-size: clamp(24px, 4vw, 38px); }
.arcade-player-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap: 10px; margin-bottom: 24px; padding: 14px; }
.arcade-player-strip article { display: flex; gap: 10px; align-items: center; padding: 10px; border: 1px solid transparent; border-radius: 12px; }
.arcade-player-strip article.self { border-color: #d6ae5166; background: #d6ae5112; }
.arcade-player-strip article > span { width: 34px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 10px; color: var(--gold); background: #d6ae5120; font-weight: 900; }
.arcade-player-strip strong, .arcade-player-strip small { display: block; }
.arcade-player-strip small { margin-top: 2px; color: var(--muted); }
.arcade-player-strip small svg { vertical-align: -2px; color: var(--gold); }
.arcade-waiting { min-height: 390px; display: grid; place-items: center; align-content: center; gap: 12px; text-align: center; }
.arcade-waiting > svg { color: var(--gold); }
.arcade-waiting h2, .arcade-waiting p { margin: 0; }
.arcade-waiting p { color: var(--muted); }
.room-code-share { margin: 14px 0; display: flex; gap: 12px; align-items: center; }
.room-code-share b { font-size: 28px; letter-spacing: .18em; }
.room-code-share button { display: inline-flex; gap: 7px; align-items: center; padding: 9px 12px; border: 1px solid var(--line); border-radius: 10px; color: var(--text); background: transparent; }
.arcade-game-stage { display: grid; gap: 22px; }
.result-banner { padding: 18px; text-align: center; }
.result-banner small { color: var(--gold); }
.result-banner h2 { margin: 5px 0; }
.result-banner p { color: var(--muted); }
.result-banner .primary-button { margin: 12px auto 0; }
</style>
