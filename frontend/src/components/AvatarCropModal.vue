<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Check, Crop, ImageIcon, Move, X, ZoomIn } from '@lucide/vue'
import {
  initialSquareCrop,
  moveSquareCrop,
  resizeSquareCrop,
  type SquareCrop,
} from '../avatarCrop'
import UiIconButton from './ui/UiIconButton.vue'

const props = defineProps<{
  file: File
}>()

const emit = defineEmits<{
  close: []
  confirm: [file: File]
}>()

const OUTPUT_EDGE = 512
const MIN_CROP_RATIO = 0.35

const image = ref<HTMLImageElement | null>(null)
const stage = ref<HTMLElement | null>(null)
const preview = ref<HTMLCanvasElement | null>(null)
const cropSelection = ref<HTMLElement | null>(null)
const imageUrl = URL.createObjectURL(props.file)
const imageSize = reactive({ width: 0, height: 0 })
const stageSize = reactive({ width: 0, height: 0 })
const crop = ref<SquareCrop>({ x: 0, y: 0, size: 1 })
const imageError = ref(false)
const processing = ref(false)
let resizeObserver: ResizeObserver | null = null
let dragStart: {
  pointerX: number
  pointerY: number
  crop: SquareCrop
} | null = null

const ready = computed(() => imageSize.width > 0 && imageSize.height > 0)
const maximumCropSize = computed(() => Math.min(imageSize.width, imageSize.height))
const cropPercent = computed(() => {
  if (!maximumCropSize.value) return 100
  return Math.round((crop.value.size / maximumCropSize.value) * 100)
})
const displayScale = computed(() => {
  if (!ready.value || !stageSize.width || !stageSize.height) return 1
  return Math.min(
    stageSize.width / imageSize.width,
    stageSize.height / imageSize.height,
  )
})
const imageDisplay = computed(() => {
  const width = imageSize.width * displayScale.value
  const height = imageSize.height * displayScale.value
  return {
    left: `${(stageSize.width - width) / 2}px`,
    top: `${(stageSize.height - height) / 2}px`,
    width: `${width}px`,
    height: `${height}px`,
  }
})
const selectionStyle = computed(() => ({
  left: `${Number.parseFloat(imageDisplay.value.left) + crop.value.x * displayScale.value}px`,
  top: `${Number.parseFloat(imageDisplay.value.top) + crop.value.y * displayScale.value}px`,
  width: `${crop.value.size * displayScale.value}px`,
  height: `${crop.value.size * displayScale.value}px`,
}))

function measureStage() {
  if (!stage.value) return
  stageSize.width = stage.value.clientWidth
  stageSize.height = stage.value.clientHeight
}

function loadImage() {
  if (!image.value) return
  imageSize.width = image.value.naturalWidth
  imageSize.height = image.value.naturalHeight
  crop.value = initialSquareCrop(imageSize.width, imageSize.height)
  imageError.value = false
  nextTick(() => {
    measureStage()
    drawPreview()
    cropSelection.value?.focus()
  })
}

function beginDrag(event: PointerEvent) {
  if (!ready.value) return
  dragStart = {
    pointerX: event.clientX,
    pointerY: event.clientY,
    crop: { ...crop.value },
  }
  cropSelection.value?.setPointerCapture?.(event.pointerId)
}

function dragCrop(event: PointerEvent) {
  if (!dragStart) return
  crop.value = moveSquareCrop(
    dragStart.crop,
    (event.clientX - dragStart.pointerX) / displayScale.value,
    (event.clientY - dragStart.pointerY) / displayScale.value,
    imageSize.width,
    imageSize.height,
  )
}

function endDrag(event: PointerEvent) {
  if (!dragStart) return
  dragStart = null
  cropSelection.value?.releasePointerCapture?.(event.pointerId)
}

function moveCropWithKeyboard(event: KeyboardEvent) {
  const distance = event.shiftKey ? 1 : Math.max(2, crop.value.size * 0.02)
  const directions: Partial<Record<string, [number, number]>> = {
    ArrowLeft: [-distance, 0],
    ArrowRight: [distance, 0],
    ArrowUp: [0, -distance],
    ArrowDown: [0, distance],
  }
  const movement = directions[event.key]
  if (!movement) return
  event.preventDefault()
  crop.value = moveSquareCrop(
    crop.value,
    movement[0],
    movement[1],
    imageSize.width,
    imageSize.height,
  )
}

function changeCropRange(event: Event) {
  const percentage = Number((event.target as HTMLInputElement).value)
  crop.value = resizeSquareCrop(
    crop.value,
    maximumCropSize.value * percentage / 100,
    imageSize.width,
    imageSize.height,
  )
}

function drawPreview() {
  const canvas = preview.value
  const source = image.value
  if (!canvas || !source || !ready.value) return
  const context = canvas.getContext('2d')
  if (!context) return
  context.clearRect(0, 0, canvas.width, canvas.height)
  context.drawImage(
    source,
    crop.value.x,
    crop.value.y,
    crop.value.size,
    crop.value.size,
    0,
    0,
    canvas.width,
    canvas.height,
  )
}

function canvasBlob(canvas: HTMLCanvasElement): Promise<Blob | null> {
  return new Promise((resolve) => canvas.toBlob(resolve, 'image/webp', 0.9))
}

async function confirmCrop() {
  if (!image.value || !ready.value || processing.value) return
  processing.value = true
  const canvas = document.createElement('canvas')
  canvas.width = OUTPUT_EDGE
  canvas.height = OUTPUT_EDGE
  const context = canvas.getContext('2d')
  if (!context) {
    processing.value = false
    return
  }
  context.imageSmoothingEnabled = true
  context.imageSmoothingQuality = 'high'
  context.drawImage(
    image.value,
    crop.value.x,
    crop.value.y,
    crop.value.size,
    crop.value.size,
    0,
    0,
    OUTPUT_EDGE,
    OUTPUT_EDGE,
  )
  const blob = await canvasBlob(canvas)
  processing.value = false
  if (!blob) return
  const baseName = props.file.name.replace(/\.[^.]+$/, '') || 'avatar'
  emit('confirm', new File([blob], `${baseName}-avatar.webp`, {
    type: 'image/webp',
  }))
}

function closeOnEscape(event: KeyboardEvent) {
  if (event.key === 'Escape' && !processing.value) emit('close')
}

watch(crop, () => nextTick(drawPreview))

onMounted(() => {
  measureStage()
  if (typeof ResizeObserver !== 'undefined' && stage.value) {
    resizeObserver = new ResizeObserver(measureStage)
    resizeObserver.observe(stage.value)
  }
  window.addEventListener('keydown', closeOnEscape)
})

onBeforeUnmount(() => {
  URL.revokeObjectURL(imageUrl)
  resizeObserver?.disconnect()
  window.removeEventListener('keydown', closeOnEscape)
})
</script>

<template>
  <Teleport to="body">
    <div class="crop-backdrop" @click.self="!processing && $emit('close')">
      <section class="crop-modal" role="dialog" aria-modal="true" aria-labelledby="avatar-crop-title">
        <UiIconButton
          compact
          class="crop-close"
          aria-label="关闭头像裁剪"
          :disabled="processing"
          @click="$emit('close')"
        >
          <X :size="20" />
        </UiIconButton>

        <header class="crop-header">
          <span><Crop :size="21" /></span>
          <div>
            <h2 id="avatar-crop-title">裁剪你的头像</h2>
            <p><Move :size="13" />拖动选框定位，调整取景范围后再保存</p>
          </div>
        </header>

        <div class="crop-workspace">
          <div ref="stage" class="crop-stage">
            <img
              ref="image"
              :src="imageUrl"
              :style="imageDisplay"
              alt="待裁剪头像"
              draggable="false"
              @load="loadImage"
              @error="imageError = true"
            />
            <div v-if="!ready && !imageError" class="crop-placeholder">
              <ImageIcon :size="26" />正在读取图片…
            </div>
            <div v-else-if="imageError" class="crop-placeholder crop-error">
              图片读取失败，请换一张图片重试。
            </div>
            <div
              v-if="ready"
              ref="cropSelection"
              class="crop-selection"
              :style="selectionStyle"
              role="application"
              tabindex="0"
              aria-label="头像裁剪选框，可拖动或用方向键移动"
              @pointerdown.prevent="beginDrag"
              @pointermove.prevent="dragCrop"
              @pointerup="endDrag"
              @pointercancel="endDrag"
              @keydown="moveCropWithKeyboard"
            >
              <i class="grid-line vertical first" />
              <i class="grid-line vertical second" />
              <i class="grid-line horizontal first" />
              <i class="grid-line horizontal second" />
              <span class="corner top-left" />
              <span class="corner top-right" />
              <span class="corner bottom-left" />
              <span class="corner bottom-right" />
            </div>
          </div>

          <aside class="crop-preview-panel">
            <span>最终效果</span>
            <canvas ref="preview" class="crop-preview" width="192" height="192" />
            <small>房间内将显示为圆形</small>
          </aside>
        </div>

        <label class="crop-range">
          <span><ZoomIn :size="15" />取景范围</span>
          <input
            type="range"
            :min="MIN_CROP_RATIO * 100"
            max="100"
            step="1"
            :value="cropPercent"
            :disabled="!ready || processing"
            aria-label="调整头像取景范围"
            @input="changeCropRange"
          />
          <small><span>近</span><span>远</span></small>
        </label>

        <div class="crop-actions">
          <button type="button" class="crop-cancel" :disabled="processing" @click="$emit('close')">
            重新选择
          </button>
          <button
            type="button"
            class="crop-confirm"
            :disabled="!ready || processing"
            @click="confirmCrop"
          >
            <Check :size="17" />{{ processing ? '正在生成…' : '确认并上传' }}
          </button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.crop-backdrop {
  position: fixed;
  z-index: 80;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(1, 8, 10, .88);
  backdrop-filter: blur(13px);
}
.crop-modal {
  position: relative;
  width: min(720px, calc(100vw - 28px));
  max-height: calc(100dvh - 28px);
  overflow-y: auto;
  border: 1px solid color-mix(in srgb, var(--gold) 28%, var(--line));
  border-radius: 24px;
  padding: 22px;
  color: var(--text);
  background:
    radial-gradient(circle at 10% 0%, rgba(225, 188, 104, .1), transparent 34%),
    var(--modal-surface);
  box-shadow: 0 28px 90px rgba(0, 0, 0, .58);
  text-align: left;
}
.crop-close {
  position: absolute;
  z-index: 2;
  top: 14px;
  right: 14px;
}
.crop-header { display: flex; align-items: center; gap: 12px; padding-right: 38px; }
.crop-header > span { display: grid; width: 42px; height: 42px; flex: 0 0 auto; place-items: center; border-radius: 13px; color: var(--gold); background: rgba(225, 188, 104, .11); }
.crop-header h2 { margin: 0; font-family: "Songti SC", serif; font-size: 21px; }
.crop-header p { display: flex; align-items: center; gap: 5px; margin: 5px 0 0; color: var(--muted); font-size: 10px; }
.crop-workspace { display: grid; grid-template-columns: minmax(0, 1fr) 150px; align-items: center; gap: 18px; margin-top: 18px; }
.crop-stage {
  position: relative;
  aspect-ratio: 1.18;
  min-height: 290px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, .1);
  border-radius: 17px;
  background:
    linear-gradient(45deg, rgba(255, 255, 255, .035) 25%, transparent 25%) 0 0 / 20px 20px,
    linear-gradient(-45deg, rgba(255, 255, 255, .035) 25%, transparent 25%) 0 10px / 20px 20px,
    #020d0f;
}
.crop-stage > img { position: absolute; max-width: none; user-select: none; }
.crop-placeholder { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 8px; color: var(--muted); font-size: 11px; }
.crop-error { color: #ef9e9e; }
.crop-selection {
  position: absolute;
  z-index: 2;
  touch-action: none;
  border: 2px solid #f1d183;
  border-radius: 5px;
  outline: none;
  box-shadow: 0 0 0 9999px rgba(0, 6, 8, .66), 0 0 0 1px rgba(255, 255, 255, .25), 0 8px 32px rgba(0, 0, 0, .25);
  cursor: move;
}
.crop-selection:focus-visible { border-color: #fff1bd; box-shadow: 0 0 0 9999px rgba(0, 6, 8, .66), 0 0 0 4px rgba(225, 188, 104, .25); }
.grid-line { position: absolute; display: block; pointer-events: none; background: rgba(255, 255, 255, .28); }
.grid-line.vertical { top: 0; bottom: 0; width: 1px; }
.grid-line.horizontal { right: 0; left: 0; height: 1px; }
.grid-line.first.vertical { left: 33.333%; }
.grid-line.second.vertical { left: 66.666%; }
.grid-line.first.horizontal { top: 33.333%; }
.grid-line.second.horizontal { top: 66.666%; }
.corner { position: absolute; width: 18px; height: 18px; border-color: #fff4c8; }
.corner.top-left { top: -3px; left: -3px; border-top: 4px solid; border-left: 4px solid; }
.corner.top-right { top: -3px; right: -3px; border-top: 4px solid; border-right: 4px solid; }
.corner.bottom-left { bottom: -3px; left: -3px; border-bottom: 4px solid; border-left: 4px solid; }
.corner.bottom-right { right: -3px; bottom: -3px; border-right: 4px solid; border-bottom: 4px solid; }
.crop-preview-panel { display: grid; justify-items: center; gap: 9px; color: var(--muted); font-size: 10px; text-align: center; }
.crop-preview-panel > span { color: var(--text); font-weight: 800; }
.crop-preview { width: 112px; height: 112px; border: 3px solid rgba(225, 188, 104, .72); border-radius: 50%; background: #061719; box-shadow: 0 12px 32px rgba(0, 0, 0, .34); }
.crop-preview-panel small { font-size: 9px; line-height: 1.45; }
.crop-range { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: center; gap: 9px 14px; margin-top: 18px; }
.crop-range > span { display: flex; align-items: center; gap: 6px; color: var(--text); font-size: 10px; font-weight: 800; }
.crop-range input { width: 100%; accent-color: var(--gold); }
.crop-range small { grid-column: 2; display: flex; justify-content: space-between; margin-top: -8px; color: var(--muted); font-size: 8px; }
.crop-actions { display: grid; grid-template-columns: 1fr 1.45fr; gap: 10px; margin-top: 18px; }
.crop-actions button { min-height: 48px; border-radius: 14px; font-weight: 850; }
.crop-cancel { border: 1px solid var(--line); color: var(--muted); background: rgba(4, 27, 28, .72); }
.crop-confirm { display: inline-flex; align-items: center; justify-content: center; gap: 7px; border: 0; color: #172018; background: linear-gradient(135deg, #efd58e, var(--gold)); box-shadow: 0 10px 26px rgba(166, 121, 39, .22); }
.crop-actions button:disabled { opacity: .52; cursor: not-allowed; }
@media (max-width: 620px) {
  .crop-backdrop { padding: 10px; }
  .crop-modal { width: calc(100vw - 20px); max-height: calc(100dvh - 20px); padding: 17px; border-radius: 20px; }
  .crop-header { align-items: flex-start; }
  .crop-header > span { width: 38px; height: 38px; }
  .crop-header h2 { font-size: 19px; }
  .crop-workspace { grid-template-columns: 1fr; gap: 13px; margin-top: 14px; }
  .crop-stage { aspect-ratio: 1; min-height: 0; }
  .crop-preview-panel { grid-template-columns: auto auto; justify-content: center; align-items: center; column-gap: 12px; }
  .crop-preview-panel > span { grid-column: 1; }
  .crop-preview { grid-column: 2; grid-row: 1 / 3; width: 76px; height: 76px; }
  .crop-preview-panel small { grid-column: 1; }
  .crop-range { margin-top: 13px; }
  .crop-actions { margin-top: 14px; }
}
</style>
