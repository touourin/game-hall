<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { MessageCircle, Send, X } from '@lucide/vue'
import type { ArcadeChatMessage } from '../types/arcade'
import AvatarImage from './AvatarImage.vue'

const props = defineProps<{
  messages: ArcadeChatMessage[]
  maxLength: number
  selfId: string
  busy: boolean
  send: (content: string) => Promise<boolean>
}>()

const open = ref(false)
const draft = ref('')
const chatList = ref<HTMLElement | null>(null)
const lastSeenId = ref(props.messages.at(-1)?.id ?? null)
const unreadCount = computed(() => {
  if (open.value || !props.messages.length) return 0
  const lastSeenIndex = props.messages.findIndex(
    (message) => message.id === lastSeenId.value,
  )
  return props.messages
    .slice(lastSeenIndex + 1)
    .filter((message) => message.senderId !== props.selfId).length
})

function formatTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

async function scrollToLatest() {
  await nextTick()
  if (chatList.value) chatList.value.scrollTop = chatList.value.scrollHeight
}

async function openChat() {
  open.value = true
  lastSeenId.value = props.messages.at(-1)?.id ?? null
  await scrollToLatest()
}

function closeChat() {
  lastSeenId.value = props.messages.at(-1)?.id ?? null
  open.value = false
}

async function submit() {
  const content = draft.value.trim()
  if (!content || props.busy) return
  if (await props.send(content)) {
    draft.value = ''
    await scrollToLatest()
  }
}

watch(
  () => props.messages.at(-1)?.id,
  async (messageId) => {
    if (!open.value) return
    lastSeenId.value = messageId ?? null
    await scrollToLatest()
  },
)
</script>

<template>
  <button
    v-if="!open"
    type="button"
    class="arcade-chat-dock"
    aria-label="打开房间聊天"
    @click="openChat"
  >
    <MessageCircle :size="20" />
    <span>聊天</span>
    <b v-if="unreadCount">{{ unreadCount > 99 ? '99+' : unreadCount }}</b>
  </button>

  <section v-else class="arcade-chat-panel" aria-label="房间聊天">
    <header>
      <div><MessageCircle :size="18" /><strong>房间聊天</strong></div>
      <button type="button" aria-label="关闭聊天" @click="closeChat"><X :size="19" /></button>
    </header>
    <div ref="chatList" class="arcade-chat-list" aria-live="polite">
      <div v-if="!messages.length" class="arcade-chat-empty">发一条消息开始聊天</div>
      <article
        v-for="message in messages"
        :key="message.id"
        :class="{ mine: message.senderId === selfId }"
      >
        <AvatarImage
          class="arcade-chat-avatar"
          :src="message.senderAvatarUrl"
          :name="message.senderName"
        />
        <div class="arcade-chat-bubble">
          <small>{{ message.senderName }} · {{ formatTime(message.createdAt) }}</small>
          <p>{{ message.content }}</p>
        </div>
      </article>
    </div>
    <form @submit.prevent="submit">
      <input
        v-model="draft"
        :maxlength="maxLength"
        placeholder="输入消息…"
        aria-label="聊天消息"
      />
      <button type="submit" aria-label="发送消息" :disabled="!draft.trim() || busy">
        <Send :size="18" />
      </button>
    </form>
  </section>
</template>

<style scoped>
.arcade-chat-dock {
  position: fixed;
  z-index: 45;
  right: max(18px, env(safe-area-inset-right));
  bottom: max(18px, env(safe-area-inset-bottom));
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 46px;
  border: 1px solid color-mix(in srgb, var(--gold) 34%, var(--line));
  border-radius: 999px;
  padding: 0 15px;
  color: var(--text);
  background: color-mix(in srgb, var(--surface) 94%, black);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28);
  font-weight: 850;
}

.arcade-chat-dock b {
  min-width: 19px;
  height: 19px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  color: #18201b;
  background: var(--gold);
  font-size: 9px;
}

.arcade-chat-panel {
  position: fixed;
  z-index: 46;
  right: max(18px, env(safe-area-inset-right));
  bottom: max(18px, env(safe-area-inset-bottom));
  width: min(390px, calc(100vw - 36px));
  height: min(520px, calc(100vh - 80px));
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 18px;
  color: var(--text);
  background: color-mix(in srgb, var(--surface) 97%, black);
  box-shadow: 0 22px 70px rgba(0, 0, 0, 0.44);
}

.arcade-chat-panel > header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--line);
  padding: 13px 14px;
}

.arcade-chat-panel > header div {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.arcade-chat-panel button {
  display: grid;
  place-items: center;
  border: 0;
  color: inherit;
  background: transparent;
}

.arcade-chat-list {
  overflow-y: auto;
  padding: 14px;
}

.arcade-chat-list article {
  display: flex;
  align-items: flex-end;
  gap: 7px;
  width: fit-content;
  max-width: 86%;
  margin-bottom: 10px;
}

.arcade-chat-list article.mine {
  flex-direction: row-reverse;
  margin-left: auto;
  text-align: right;
}

.arcade-chat-avatar {
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  margin-bottom: 1px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.18);
}

.arcade-chat-bubble {
  min-width: 0;
}

.arcade-chat-list small {
  display: block;
  margin-bottom: 3px;
  color: var(--muted);
  font-size: 9px;
}

.arcade-chat-list p {
  margin: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.035);
  text-align: left;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.arcade-chat-list article.mine p {
  border-color: color-mix(in srgb, var(--gold) 30%, var(--line));
  background: color-mix(in srgb, var(--gold) 10%, transparent);
}

.arcade-chat-empty {
  display: grid;
  height: 100%;
  place-items: center;
  color: var(--muted);
}

.arcade-chat-panel form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 42px;
  gap: 8px;
  border-top: 1px solid var(--line);
  padding: 11px;
}

.arcade-chat-panel input {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 11px;
  padding: 10px 12px;
  color: var(--text);
  background: rgba(0, 0, 0, 0.16);
}

.arcade-chat-panel form button {
  border-radius: 11px;
  color: #1b211b;
  background: var(--gold);
}

.arcade-chat-panel form button:disabled {
  opacity: 0.45;
}

@media (max-width: 600px) {
  .arcade-chat-panel {
    right: 0;
    bottom: 0;
    left: 0;
    width: 100%;
    height: min(68vh, 560px);
    border-radius: 20px 20px 0 0;
  }
}
</style>
