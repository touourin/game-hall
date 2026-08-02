<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  src?: string | null
  name: string
  fallback?: string | number
}>()

const failed = ref(false)

watch(
  () => props.src,
  () => { failed.value = false },
)
</script>

<template>
  <span class="avatar-image" role="img" :aria-label="`${name}的头像`">
    <img
      v-if="src && !failed"
      :src="src"
      alt=""
      draggable="false"
      @error="failed = true"
    />
    <span v-else aria-hidden="true">{{ fallback ?? name.slice(0, 1) }}</span>
  </span>
</template>

<style scoped>
.avatar-image {
  display: inline-grid;
  flex: 0 0 auto;
  place-items: center;
  overflow: hidden;
}

.avatar-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-image > span {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
}
</style>
