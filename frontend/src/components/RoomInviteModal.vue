<script setup lang="ts">
import { QrCode } from '@lucide/vue'
import QrcodeVue from 'qrcode.vue'
import BaseModal from './ui/BaseModal.vue'

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
  <BaseModal
    :title="title"
    :description="description"
    panel-class="qr-modal"
    close-label="关闭二维码"
    @close="$emit('close')"
  >
    <template #icon><QrCode :size="25" /></template>
    <div class="qr-frame">
      <QrcodeVue :value="url" :size="196" level="M" />
    </div>
    <strong class="modal-room-code">{{ roomCode }}</strong>
    <small class="qr-url">{{ url }}</small>
  </BaseModal>
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
  color: var(--accent);
  font-family: ui-monospace, monospace;
  font-size: 28px;
  letter-spacing: .16em;
}

.qr-url {
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
