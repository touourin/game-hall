<script setup lang="ts">
import type { RoleSkinId } from '../../gameRoleSkins'
import type { RoomSnapshot } from '../../types/avalon'
import AvalonTable from './AvalonTable.vue'

withDefaults(defineProps<{
  snapshot: RoomSnapshot
  roleSkin?: RoleSkinId
}>(), {
  roleSkin: 'classic-tabletop',
})

const emit = defineEmits<{ openChat: [] }>()
</script>

<template>
  <AvalonTable
    :snapshot="snapshot"
    :role-skin="roleSkin"
    @open-chat="emit('openChat')"
  />
</template>
