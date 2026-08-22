<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChevronRight, UsersRound } from '@lucide/vue'
import BaseModal from '../../components/ui/BaseModal.vue'
import type { ArcadeSnapshot } from '../../types/arcade'
import { isAvalonArcadeSnapshot } from './types'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const showPlayerNumbers = ref(false)

const avalonSnapshot = computed(() => (
  isAvalonArcadeSnapshot(props.snapshot) ? props.snapshot : null
))
const isSpectating = computed(() => props.snapshot.viewer?.mode === 'spectator')
const selfPlayerNumber = computed(() => {
  const player = props.snapshot.players.find(
    (candidate) => candidate.id === props.snapshot.self.id,
  )
  return player ? player.seat + 1 : null
})

function aiDifficultyLabel(difficulty?: string | null): string {
  if (!difficulty) return '普通'
  return props.snapshot.ai?.difficulties.find(
    (option) => option.key === difficulty,
  )?.label ?? difficulty
}
</script>

<template>
  <button
    v-if="avalonSnapshot"
    class="self-number-trigger"
    type="button"
    data-ui-interaction="choice"
    :aria-label="`${isSpectating ? '观战视角' : '我的号码'}是 ${selfPlayerNumber} 号，查看玩家号码表`"
    @click="showPlayerNumbers = true"
  >
    <span class="self-number-value">{{ selfPlayerNumber }}号</span>
    <span class="self-number-copy">
      <small>{{ isSpectating ? '观战视角' : '我的号码' }}</small>
      <span>查看号码表</span>
    </span>
    <ChevronRight :size="14" aria-hidden="true" />
  </button>

  <BaseModal
    v-if="showPlayerNumbers && avalonSnapshot"
    aria-label="玩家号码表"
    panel-class="player-number-modal"
    close-label="关闭玩家号码表"
    mobile-sheet
    inline
    @close="showPlayerNumbers = false"
  >
    <span class="modal-icon"><UsersRound :size="25" /></span>
    <h2>玩家号码表</h2>
    <p>本局号码保持不变</p>
    <div class="player-number-list">
      <div
        v-for="player in snapshot.players"
        :key="player.id"
        :class="{ self: player.id === snapshot.self.id }"
      >
        <span>{{ player.seat + 1 }}</span>
        <strong>{{ player.name }}</strong>
        <small v-if="player.isBot">
          AI · {{ aiDifficultyLabel(player.botDifficulty) }}
        </small>
        <small v-if="player.id === snapshot.self.id">
          {{ isSpectating ? '观战视角' : '你' }}
        </small>
      </div>
    </div>
  </BaseModal>
</template>
