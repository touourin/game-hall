<script setup lang="ts">
import { computed } from 'vue'
import type { ArcadeSnapshot } from '../../types/arcade'
import AvalonTable from './AvalonTable.vue'
import {
  defaultRoleSkinLoadout,
  lockRoleSkinLoadout,
  roleSkinRoleCode,
  storedRoleSkinLoadout,
  storedRoleSkinLoadoutLock,
  type RoleSkinId,
} from './roleSkins'
import { isAvalonArcadeSnapshot } from './types'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const emit = defineEmits<{ openChat: [] }>()

const avalonSnapshot = computed(() => (
  isAvalonArcadeSnapshot(props.snapshot) ? props.snapshot : null
))
const roleSkinAccountId = computed(() => (
  props.snapshot.viewer?.accountId
  ?? props.snapshot.self.accountId
  ?? props.snapshot.viewer?.id
  ?? props.snapshot.self.id
))
const viewerIsGuest = computed(() => (
  props.snapshot.viewer?.isGuest ?? props.snapshot.self.isGuest
))
const activeRoleSkin = computed<RoleSkinId>(() => {
  const snapshot = avalonSnapshot.value
  const role = roleSkinRoleCode(snapshot?.game.self.role?.code ?? '')
  if (!snapshot || !role) return 'classic-tabletop'
  const savedLoadout = viewerIsGuest.value
    ? defaultRoleSkinLoadout()
    : storedRoleSkinLoadout(roleSkinAccountId.value)
  const lockedLoadout = storedRoleSkinLoadoutLock(snapshot.roomCode)
    ?? lockRoleSkinLoadout(snapshot.roomCode, savedLoadout)
  return lockedLoadout[role]
})
</script>

<template>
  <AvalonTable
    v-if="avalonSnapshot"
    :snapshot="avalonSnapshot.game"
    :role-skin="activeRoleSkin"
    @open-chat="emit('openChat')"
  />
</template>
