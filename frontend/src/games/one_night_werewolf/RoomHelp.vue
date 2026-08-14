<script setup lang="ts">
import { computed, ref } from 'vue'
import { CircleHelp } from '@lucide/vue'
import BaseModal from '../../components/ui/BaseModal.vue'
import type { ArcadeSnapshot } from '../../types/arcade'
import OneNightWerewolfRules from './OneNightWerewolfRules.vue'
import type { OneNightWerewolfView } from './types'

const props = withDefaults(defineProps<{
  snapshot: ArcadeSnapshot
  placement?: 'header' | 'rule'
}>(), {
  placement: 'header',
})
const showRules = ref(false)
const game = computed(() => (
  props.snapshot.gameKey === 'one_night_werewolf'
    ? props.snapshot.game as unknown as OneNightWerewolfView
    : null
))
const activeRoleCodes = computed(() => (
  [...new Set(game.value?.roleDeck.map((role) => role.code) ?? [])]
))
</script>

<template>
  <button
    v-if="game"
    :class="{ 'header-action': placement === 'header' }"
    type="button"
    aria-label="查看一夜狼人规则与角色"
    @click="showRules = true"
  >
    <CircleHelp :size="21" />
    <span v-if="placement === 'rule'">规则与角色</span>
  </button>
  <BaseModal
    v-if="showRules && game"
    aria-label="一夜狼人规则与角色说明"
    panel-class="one-night-rules-modal"
    close-label="关闭规则与角色说明"
    mobile-sheet
    inline
    @close="showRules = false"
  >
    <span class="modal-icon"><CircleHelp :size="25" /></span>
    <h2>一夜狼人 · 规则与角色</h2>
    <p>玩法流程、角色技能、行动限制与胜负条件统一整理在这里。</p>
    <OneNightWerewolfRules
      :roles="game.roleGuide"
      :active-role-codes="activeRoleCodes"
    />
  </BaseModal>
</template>

<style scoped>
:global(.modal-card.one-night-rules-modal) {
  width: min(94vw, 780px);
  max-height: min(88vh, 880px);
  overflow-y: auto;
}
</style>
