<script setup lang="ts">
import { Check, Images, Maximize2, X } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  ROLE_SKINS,
  roleSkinPreviewRoles,
  type RoleSkinId,
} from '../roleSkins'

const props = defineProps<{
  modelValue: RoleSkinId
}>()

const emit = defineEmits<{
  'update:modelValue': [skin: RoleSkinId]
}>()

const previewSkinId = ref<RoleSkinId | null>(null)
const previewSkin = computed(() =>
  ROLE_SKINS.find((skin) => skin.id === previewSkinId.value),
)
const previewRoles = computed(() =>
  previewSkinId.value ? roleSkinPreviewRoles(previewSkinId.value) : [],
)

function openPreview(skin: RoleSkinId): void {
  previewSkinId.value = skin
}

function closePreview(): void {
  previewSkinId.value = null
}

function usePreviewedSkin(): void {
  if (!previewSkinId.value) return
  emit('update:modelValue', previewSkinId.value)
  closePreview()
}

function handleEscape(event: KeyboardEvent): void {
  if (event.key === 'Escape' && previewSkinId.value) closePreview()
}

onMounted(() => window.addEventListener('keydown', handleEscape))
onBeforeUnmount(() => window.removeEventListener('keydown', handleEscape))
</script>

<template>
  <section class="surface role-skin-lobby-card" aria-labelledby="role-skin-title">
    <div class="role-skin-lobby-heading">
      <span class="role-skin-lobby-icon"><Images :size="20" /></span>
      <div>
        <strong id="role-skin-title">我的身份卡画风</strong>
        <small>仅影响你看到的身份卡 · 开局后锁定</small>
      </div>
    </div>

    <div class="role-skin-options" role="group" aria-label="预览并选择本局身份卡画风">
      <button
        v-for="skin in ROLE_SKINS"
        :key="skin.id"
        type="button"
        :data-role-skin="skin.id"
        :class="{ active: modelValue === skin.id }"
        :aria-pressed="modelValue === skin.id"
        :aria-label="`查看${skin.name}大图预览，${skin.tier}画风：${skin.description}${modelValue === skin.id ? '，当前正在使用' : ''}`"
        @click="openPreview(skin.id)"
      >
        <span class="role-skin-preview">
          <img
            :src="skin.preview"
            :alt="`${skin.name}身份卡画风预览`"
            loading="lazy"
            draggable="false"
          />
          <small class="role-skin-tier" :data-tier="skin.tier">
            {{ skin.tier }}
          </small>
          <span
            v-if="modelValue === skin.id"
            class="role-skin-check"
            aria-hidden="true"
          >
            <Check :size="15" />
          </span>
          <span class="role-skin-expand" aria-hidden="true">
            <Maximize2 :size="11" />
            大图
          </span>
        </span>
        <span class="role-skin-copy">
          <strong>{{ skin.name }}</strong>
          <small>{{ skin.description }}</small>
        </span>
      </button>
    </div>
  </section>

  <Teleport to="body">
    <div
      v-if="previewSkin"
      class="role-skin-modal-backdrop"
      @click.self="closePreview"
    >
      <section
        class="role-skin-modal"
        :data-tier="previewSkin.tier"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="`role-skin-preview-${previewSkin.id}`"
      >
        <header class="role-skin-modal-header">
          <div class="role-skin-modal-heading">
            <span class="role-skin-modal-tier">{{ previewSkin.tier }}画风</span>
            <h2 :id="`role-skin-preview-${previewSkin.id}`">
              {{ previewSkin.name }}
            </h2>
            <p>{{ previewSkin.description }} · 点击“使用此皮肤”后才会更换</p>
          </div>
          <button
            type="button"
            class="role-skin-modal-close"
            aria-label="关闭皮肤大图预览"
            @click="closePreview"
          >
            <X :size="20" />
          </button>
        </header>

        <div class="role-skin-gallery" :data-tier="previewSkin.tier">
          <article
            v-for="role in previewRoles"
            :key="role.code"
            class="role-skin-portrait"
            :data-role="role.code"
            :data-alignment="role.alignment"
          >
            <img
              class="role-skin-artwork"
              :class="{ 'preserves-frame': role.framing.preserveFrame }"
              :src="role.artwork"
              :alt="`${previewSkin.name}中的${role.name}`"
              :style="{
                '--role-art-scale': role.framing.scale,
                '--role-art-hover-scale': role.framing.scale * 1.025,
                '--role-art-origin': `${role.framing.originXPercent}% ${role.framing.originYPercent}%`,
              }"
              draggable="false"
            />
            <img
              v-if="role.framing.preserveFrame"
              class="role-skin-inner-artwork"
              :src="role.artwork"
              :style="{
                '--role-art-scale': role.framing.scale,
                '--role-art-hover-scale': role.framing.scale * 1.025,
                '--role-art-origin': `${role.framing.originXPercent}% ${role.framing.originYPercent}%`,
              }"
              alt=""
              aria-hidden="true"
              draggable="false"
            />
            <div class="role-skin-identity">
              <small>
                {{ role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营' }}
              </small>
              <strong>{{ role.name }}</strong>
            </div>
          </article>
        </div>

        <footer class="role-skin-modal-footer">
          <span>完整展示 8 个身份 · 仅改变你自己的身份卡画风</span>
          <button
            type="button"
            class="role-skin-use-button"
            :class="{ selected: props.modelValue === previewSkin.id }"
            @click="usePreviewedSkin"
          >
            <Check v-if="props.modelValue === previewSkin.id" :size="16" />
            {{ props.modelValue === previewSkin.id ? '当前正在使用' : '使用此皮肤' }}
          </button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.role-skin-lobby-card {
  display: grid;
  gap: 14px;
  padding: 16px;
}

.role-skin-lobby-heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-skin-lobby-heading > div {
  display: grid;
  gap: 4px;
}

.role-skin-lobby-heading strong {
  font-family: "Songti SC", "STSong", serif;
  font-size: 14px;
}

.role-skin-lobby-heading small {
  color: var(--muted);
  font-size: 10px;
}

.role-skin-lobby-icon {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 42px;
  height: 42px;
  border: 1px solid rgba(225, 188, 104, 0.18);
  border-radius: 14px;
  color: var(--gold);
  background: rgba(225, 188, 104, 0.08);
}

.role-skin-options {
  display: grid;
  grid-auto-columns: minmax(154px, 1fr);
  grid-auto-flow: column;
  gap: 10px;
  margin-inline: -4px;
  padding: 2px 4px 9px;
  overflow-x: auto;
  overscroll-behavior-inline: contain;
  scrollbar-color: rgba(225, 188, 104, 0.34) transparent;
  scrollbar-width: thin;
  scroll-snap-type: inline proximity;
}

.role-skin-options button {
  display: grid;
  align-content: start;
  gap: 9px;
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 15px;
  padding: 6px 6px 10px;
  color: var(--text);
  background: rgba(var(--surface-header-rgb), 0.58);
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  scroll-snap-align: start;
  transition: border-color 160ms ease, background 160ms ease, transform 160ms ease;
}

.role-skin-options button.active {
  border-color: rgba(225, 188, 104, 0.52);
  background: rgba(225, 188, 104, 0.11);
  box-shadow: inset 0 0 0 1px rgba(225, 188, 104, 0.08);
}

.role-skin-options button:active {
  transform: scale(0.985);
}

.role-skin-preview {
  position: relative;
  display: block;
  aspect-ratio: 4 / 3;
  border-radius: 10px;
  background: rgba(2, 10, 12, 0.78);
  overflow: hidden;
}

.role-skin-preview::after {
  position: absolute;
  inset: auto 0 0;
  height: 42%;
  background: linear-gradient(transparent, rgba(2, 10, 12, 0.76));
  content: '';
  pointer-events: none;
}

.role-skin-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 220ms ease;
}

.role-skin-options button:hover .role-skin-preview img {
  transform: scale(1.035);
}

.role-skin-tier,
.role-skin-check {
  position: absolute;
  z-index: 1;
  top: 7px;
  display: inline-grid;
  place-items: center;
  min-height: 23px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  background: rgba(2, 10, 12, 0.72);
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(7px);
}

.role-skin-tier {
  left: 7px;
  border-radius: 999px;
  padding: 0 8px;
  font-size: 8px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.role-skin-tier[data-tier="终极"] {
  border-color: rgba(255, 226, 151, 0.62);
  color: #ffe297;
  background: rgba(83, 55, 9, 0.76);
}

.role-skin-check {
  right: 7px;
  width: 23px;
  border-color: rgba(225, 188, 104, 0.58);
  border-radius: 50%;
  color: #ffe297;
  background: rgba(69, 46, 8, 0.82);
}

.role-skin-expand {
  position: absolute;
  z-index: 1;
  right: 7px;
  bottom: 7px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  padding: 3px 7px;
  color: rgba(255, 255, 255, 0.88);
  background: rgba(2, 10, 12, 0.62);
  font-size: 8px;
  font-weight: 850;
  backdrop-filter: blur(6px);
}

.role-skin-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
  padding-inline: 3px;
}

.role-skin-copy strong,
.role-skin-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-skin-copy strong {
  font-family: "Songti SC", "STSong", serif;
  font-size: 12px;
}

.role-skin-copy small {
  color: var(--muted);
  font-size: 8px;
}

.role-skin-modal-backdrop {
  position: fixed;
  z-index: 80;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 16px;
  background:
    radial-gradient(circle at 50% 0%, rgba(225, 188, 104, 0.1), transparent 40%),
    rgba(1, 8, 9, 0.9);
  backdrop-filter: blur(12px);
}

.role-skin-modal {
  position: relative;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  width: min(1120px, calc(100vw - 32px));
  height: min(94dvh, 940px);
  min-height: 0;
  border: 1px solid rgba(225, 188, 104, 0.25);
  border-radius: 24px;
  color: #f4f7f2;
  background:
    linear-gradient(145deg, rgba(225, 188, 104, 0.06), transparent 32%),
    #071d1d;
  box-shadow: 0 32px 100px rgba(0, 0, 0, 0.72);
  overflow: hidden;
}

.role-skin-modal[data-tier="终极"] {
  border-color: rgba(255, 216, 120, 0.46);
  background:
    radial-gradient(circle at 50% -14%, rgba(142, 183, 255, 0.18), transparent 37%),
    radial-gradient(circle at 90% 0%, rgba(171, 105, 255, 0.13), transparent 28%),
    linear-gradient(145deg, rgba(255, 210, 100, 0.1), transparent 35%),
    #07171c;
  box-shadow:
    0 0 0 1px rgba(255, 229, 158, 0.08),
    0 34px 110px rgba(0, 0, 0, 0.78),
    0 0 54px rgba(113, 145, 255, 0.12);
}

.role-skin-modal-header,
.role-skin-modal-footer {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 22px;
  background: rgba(4, 19, 20, 0.82);
  backdrop-filter: blur(14px);
}

.role-skin-modal-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.role-skin-modal-heading {
  display: grid;
  gap: 4px;
}

.role-skin-modal-tier {
  width: max-content;
  border: 1px solid rgba(225, 188, 104, 0.32);
  border-radius: 999px;
  padding: 3px 8px;
  color: #e9cb81;
  background: rgba(225, 188, 104, 0.08);
  font-size: 9px;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.role-skin-modal-heading h2 {
  margin: 0;
  font-family: "Songti SC", "STSong", serif;
  font-size: clamp(22px, 3vw, 34px);
  line-height: 1.15;
}

.role-skin-modal[data-tier="升级"] .role-skin-modal-heading h2 {
  color: #f1d995;
  letter-spacing: 0.1em;
  text-shadow: 0 2px 15px rgba(225, 188, 104, 0.18);
}

.role-skin-modal[data-tier="终极"] .role-skin-modal-heading h2 {
  color: transparent;
  background: linear-gradient(180deg, #fff9db 4%, #f5d579 48%, #bd7924 100%);
  background-clip: text;
  font-family: "STKaiti", "KaiTi", "Songti SC", serif;
  font-size: clamp(25px, 3.4vw, 39px);
  font-weight: 900;
  letter-spacing: 0.16em;
  filter: drop-shadow(0 3px 10px rgba(244, 198, 86, 0.2));
}

.role-skin-modal-heading p {
  margin: 0;
  color: #98b4ae;
  font-size: 11px;
}

.role-skin-modal-close {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  color: #bdcfca;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
}

.role-skin-modal-close:hover {
  border-color: rgba(225, 188, 104, 0.42);
  color: #ffe297;
}

.role-skin-gallery {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-auto-rows: max-content;
  align-content: start;
  gap: 14px;
  min-height: 0;
  padding: 20px 22px 26px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-color: rgba(225, 188, 104, 0.4) transparent;
  scrollbar-width: thin;
}

.role-skin-portrait {
  position: relative;
  min-width: 0;
  aspect-ratio: 2 / 3;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 17px;
  background: #031010;
  box-shadow: 0 12px 27px rgba(0, 0, 0, 0.28);
  overflow: hidden;
}

.role-skin-portrait[data-alignment="good"] {
  border-color: rgba(100, 188, 211, 0.28);
}

.role-skin-portrait[data-alignment="evil"] {
  border-color: rgba(191, 94, 116, 0.28);
}

.role-skin-gallery[data-tier="升级"] .role-skin-portrait {
  border-color: rgba(225, 188, 104, 0.3);
  box-shadow:
    inset 0 0 0 1px rgba(255, 231, 169, 0.04),
    0 14px 32px rgba(0, 0, 0, 0.36);
}

.role-skin-gallery[data-tier="终极"] .role-skin-portrait {
  border-color: rgba(255, 216, 120, 0.52);
  box-shadow:
    inset 0 0 0 1px rgba(255, 244, 204, 0.11),
    0 16px 38px rgba(0, 0, 0, 0.46),
    0 0 23px rgba(114, 151, 255, 0.08);
}

.role-skin-artwork,
.role-skin-inner-artwork {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: filter 260ms ease;
}

.role-skin-artwork {
  transform: scale(var(--role-art-scale, 1));
  transform-origin: var(--role-art-origin, 50% 50%);
  transition: transform 260ms ease, filter 260ms ease;
}

.role-skin-artwork.preserves-frame {
  transform: none;
}

.role-skin-inner-artwork {
  position: absolute;
  z-index: 1;
  inset: 0;
  pointer-events: none;
  transform: scale(var(--role-art-scale, 1));
  transform-origin: var(--role-art-origin, 50% 50%);
  -webkit-mask-image: radial-gradient(
    ellipse 38% 42% at 50% 42%,
    #000 0 75%,
    rgba(0, 0, 0, 0.76) 84%,
    transparent 100%
  );
  mask-image: radial-gradient(
    ellipse 38% 42% at 50% 42%,
    #000 0 75%,
    rgba(0, 0, 0, 0.76) 84%,
    transparent 100%
  );
  transition: transform 260ms ease, filter 260ms ease;
}

.role-skin-portrait:hover .role-skin-artwork,
.role-skin-portrait:hover .role-skin-inner-artwork {
  filter: brightness(1.06);
}

.role-skin-portrait:hover .role-skin-artwork {
  transform: scale(var(--role-art-hover-scale, 1.025));
}

.role-skin-portrait:hover .role-skin-artwork.preserves-frame {
  transform: none;
}

.role-skin-portrait:hover .role-skin-inner-artwork {
  transform: scale(var(--role-art-hover-scale, 1.025));
}

.role-skin-identity {
  position: absolute;
  z-index: 2;
  inset: auto 0 0;
  display: grid;
  justify-items: center;
  gap: 3px;
  min-height: 30%;
  align-content: end;
  padding: 34px 9px 13px;
  background: linear-gradient(transparent, rgba(2, 9, 10, 0.93) 50%, #02090a);
  text-align: center;
}

.role-skin-identity small {
  color: #92aaa5;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.role-skin-portrait[data-alignment="good"] .role-skin-identity small {
  color: #a9d9e3;
}

.role-skin-portrait[data-alignment="evil"] .role-skin-identity small {
  color: #e2a0ad;
}

.role-skin-identity strong {
  color: #f3f2e8;
  font-family: "Songti SC", "STSong", serif;
  font-size: clamp(15px, 1.8vw, 22px);
  line-height: 1.2;
}

.role-skin-gallery[data-tier="升级"] .role-skin-identity strong {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 8px;
  color: #f3d88d;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-shadow: 0 2px 11px rgba(225, 188, 104, 0.3);
}

.role-skin-gallery[data-tier="升级"] .role-skin-identity strong::before,
.role-skin-gallery[data-tier="升级"] .role-skin-identity strong::after {
  height: 1px;
  flex: 1;
  background: linear-gradient(90deg, transparent, rgba(225, 188, 104, 0.68));
  content: '';
}

.role-skin-gallery[data-tier="升级"] .role-skin-identity strong::after {
  transform: scaleX(-1);
}

.role-skin-gallery[data-tier="终极"] .role-skin-identity {
  padding-bottom: 16px;
  background:
    radial-gradient(ellipse at 50% 100%, rgba(84, 114, 195, 0.2), transparent 72%),
    linear-gradient(transparent, rgba(3, 8, 14, 0.91) 44%, #02070c);
}

.role-skin-gallery[data-tier="终极"] .role-skin-identity::before {
  color: #f6da85;
  font-size: 10px;
  line-height: 1;
  text-shadow: 0 0 10px rgba(255, 224, 133, 0.7);
  content: '◆';
}

.role-skin-gallery[data-tier="终极"] .role-skin-identity strong {
  width: 100%;
  color: transparent;
  background: linear-gradient(180deg, #fffbdc, #f5d06b 58%, #bc7520);
  background-clip: text;
  font-family: "STKaiti", "KaiTi", "Songti SC", serif;
  font-size: clamp(18px, 2.1vw, 26px);
  font-weight: 900;
  letter-spacing: 0.13em;
  filter: drop-shadow(0 2px 7px rgba(245, 202, 89, 0.38));
}

.role-skin-modal-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.role-skin-modal-footer > span {
  color: #94ada8;
  font-size: 10px;
}

.role-skin-use-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 146px;
  min-height: 43px;
  border: 1px solid rgba(245, 209, 119, 0.58);
  border-radius: 12px;
  padding: 0 18px;
  color: #17201a;
  background: linear-gradient(180deg, #f4d98e, #cfa94d);
  box-shadow: 0 8px 22px rgba(189, 135, 31, 0.2);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
}

.role-skin-use-button.selected {
  color: #e8d69f;
  background: rgba(225, 188, 104, 0.09);
  box-shadow: none;
}

@media (min-width: 820px) {
  .role-skin-options {
    grid-auto-flow: initial;
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }
}

@media (max-width: 430px) {
  .role-skin-lobby-card {
    padding-inline: 13px;
  }

  .role-skin-options {
    grid-auto-columns: minmax(148px, 46vw);
  }
}

@media (max-width: 720px) {
  .role-skin-modal-backdrop {
    align-items: end;
    padding: 8px;
  }

  .role-skin-modal {
    width: 100%;
    height: calc(100dvh - 8px);
    border-radius: 20px 20px 0 0;
  }

  .role-skin-modal-header,
  .role-skin-modal-footer {
    padding: 14px;
  }

  .role-skin-modal-heading h2 {
    font-size: 23px;
  }

  .role-skin-modal-heading p {
    max-width: 75vw;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .role-skin-gallery {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    padding: 12px 12px 20px;
  }

  .role-skin-identity strong {
    font-size: clamp(14px, 4.7vw, 20px);
  }

  .role-skin-gallery[data-tier="终极"] .role-skin-identity strong {
    font-size: clamp(16px, 5.4vw, 23px);
  }

  .role-skin-modal-footer {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    justify-content: stretch;
  }

  .role-skin-modal-footer > span {
    display: none;
  }

  .role-skin-use-button {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .role-skin-portrait img,
  .role-skin-preview img {
    transition: none;
  }
}
</style>
