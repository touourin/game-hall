<script setup lang="ts">
import { QrCode, X } from '@lucide/vue'
import QrcodeVue from 'qrcode.vue'

withDefaults(
  defineProps<{
    url: string
    roomCode: string
    title?: string
    description?: string
  }>(),
  {
    title: '扫描加入房间',
    description: '请先连接与服务器相同的 Wi‑Fi',
  },
)

defineEmits<{
  close: []
}>()
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="modal-card qr-modal" role="dialog" aria-modal="true" :aria-label="title">
      <button class="modal-close" type="button" aria-label="关闭二维码" @click="$emit('close')">
        <X :size="20" />
      </button>
      <span class="modal-icon"><QrCode :size="25" /></span>
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
      <div class="qr-frame">
        <QrcodeVue :value="url" :size="196" level="M" />
      </div>
      <strong class="modal-room-code">{{ roomCode }}</strong>
      <small>{{ url }}</small>
    </section>
  </div>
</template>

<style scoped>
.qr-frame {
  width: 220px;
  margin: 0 auto 15px;
  border-radius: 18px;
  padding: 12px;
  background: white;
  line-height: 0;
}

.modal-room-code {
  display: block;
  color: var(--gold);
  font-family: ui-monospace, monospace;
  font-size: 28px;
  letter-spacing: .16em;
}

.qr-modal > small {
  display: block;
  max-width: 100%;
  margin-top: 8px;
  overflow: hidden;
  color: #78958b;
  font-size: 8px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
