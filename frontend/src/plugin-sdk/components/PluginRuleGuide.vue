<script setup lang="ts">
import ModeGuide from '../../components/ModeGuide.vue'
import type { PluginRuleGuideProps } from '../types'

defineProps<PluginRuleGuideProps>()
</script>

<template>
  <ModeGuide class="plugin-rule-guide" :content="content" />
</template>
