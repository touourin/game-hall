<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, Copy, Link2, Share2 } from '@lucide/vue'
import { copyText } from '../clipboard'

const props = withDefaults(
  defineProps<{
    url: string
    shareTitle?: string
    shareText?: string
  }>(),
  {
    shareTitle: '游戏邀请',
    shareText: '点击链接加入游戏房间',
  },
)

const copyStatus = ref<'idle' | 'copied' | 'failed'>('idle')
const canShare = computed(() => typeof navigator.share === 'function')

function selectLink(event: Event) {
  const input = event.currentTarget
  if (input instanceof HTMLInputElement) input.select()
}

async function copyInviteLink() {
  copyStatus.value = (await copyText(props.url)) ? 'copied' : 'failed'
  window.setTimeout(() => {
    copyStatus.value = 'idle'
  }, 1800)
}

async function shareInviteLink() {
  try {
    await navigator.share({
      title: props.shareTitle,
      text: props.shareText,
      url: props.url,
    })
  } catch {
    // Closing the system share sheet does not require an error message.
  }
}
</script>

<template>
  <div class="invite-link-panel">
    <label class="invite-link-field">
      <Link2 :size="16" />
      <input
        :value="url"
        readonly
        aria-label="邀请链接"
        @click="selectLink"
        @focus="selectLink"
      />
    </label>
    <div class="invite-link-actions">
      <button type="button" @click="copyInviteLink">
        <Check v-if="copyStatus === 'copied'" :size="17" />
        <Copy v-else :size="17" />
        {{ copyStatus === 'copied' ? '已复制' : copyStatus === 'failed' ? '复制失败' : '复制邀请链接' }}
      </button>
      <button v-if="canShare" type="button" @click="shareInviteLink">
        <Share2 :size="17" />
        分享
      </button>
    </div>
    <p v-if="copyStatus === 'failed'">自动复制失败，请长按或点击上方链接手动复制。</p>
  </div>
</template>

<style scoped>
.invite-link-panel {
  display: grid;
  gap: 9px;
  width: 100%;
}

.invite-link-field {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 9px 11px;
  color: #9eb9af;
  background: rgba(3, 19, 20, 0.46);
}

.invite-link-field svg {
  flex: 0 0 auto;
  color: var(--gold);
}

.invite-link-field input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  padding: 0;
  color: inherit;
  background: transparent;
  font: inherit;
  font-size: 10px;
}

.invite-link-actions {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.invite-link-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 42px;
  border: 1px solid rgba(225, 188, 104, 0.22);
  border-radius: 12px;
  padding: 0 14px;
  color: #ead9a9;
  background: rgba(113, 84, 34, 0.18);
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}

.invite-link-panel p {
  margin: 0;
  color: var(--muted);
  font-size: 10px;
  text-align: center;
}

@media (max-width: 430px) {
  .invite-link-actions {
    display: grid;
    grid-template-columns: 1fr auto;
  }

  .invite-link-actions button {
    padding: 0 12px;
  }
}
</style>
