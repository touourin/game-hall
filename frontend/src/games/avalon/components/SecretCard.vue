<script setup lang="ts">
import { computed, ref } from 'vue'
import { Eye, EyeOff, Lock } from '@lucide/vue'
import {
  roleArtwork,
  roleArtworkFraming,
  roleSkinName,
  type RoleSkinId,
} from '../roleSkins'

const props = withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    hint?: string
    roleCode?: string
    roleSkin?: RoleSkinId
  }>(),
  {
    subtitle: '',
    hint: '按住查看，松开隐藏',
    roleCode: '',
    roleSkin: 'classic-tabletop',
  },
)

const emit = defineEmits<{ seen: [] }>()
const pressed = ref(false)
const hasSeen = ref(false)
const artwork = computed(() =>
  props.roleCode ? roleArtwork(props.roleCode, props.roleSkin) : null,
)
const artworkFraming = computed(() =>
  roleArtworkFraming(props.roleCode, props.roleSkin),
)
const activeSkinName = computed(() => roleSkinName(props.roleSkin))

function reveal() {
  pressed.value = true
  if (!hasSeen.value) {
    hasSeen.value = true
    emit('seen')
  }
}

function hide() {
  pressed.value = false
}
</script>

<template>
  <div class="secret-card-shell" :class="{ 'has-role-art': Boolean(artwork) }">
    <div v-if="roleCode && artwork" class="role-skin-lock" aria-label="本局身份卡画风">
      <Lock :size="13" />
      <span>本局画风</span>
      <strong>{{ activeSkinName }}</strong>
    </div>

    <button
      type="button"
      class="secret-card"
      :class="{ 'has-role-art': Boolean(artwork) }"
      :data-skin="artwork ? roleSkin : undefined"
      @pointerdown.prevent="reveal"
      @pointerup.prevent="hide"
      @pointercancel="hide"
      @pointerleave="hide"
      @keydown.space.prevent="reveal"
      @keyup.space.prevent="hide"
      @keydown.enter.prevent="reveal"
      @keyup.enter.prevent="hide"
      @contextmenu.prevent
    >
      <template v-if="pressed">
        <img
          v-if="artwork"
          class="secret-card__art"
          :class="{ 'preserves-frame': artworkFraming.preserveFrame }"
          :src="artwork"
          :style="{
            '--role-art-scale': artworkFraming.scale,
            '--role-art-origin': `${artworkFraming.originXPercent}% ${artworkFraming.originYPercent}%`,
          }"
          alt=""
          aria-hidden="true"
        />
        <img
          v-if="artwork && artworkFraming.preserveFrame"
          class="secret-card__inner-art"
          :src="artwork"
          :style="{
            '--role-art-scale': artworkFraming.scale,
            '--role-art-origin': `${artworkFraming.originXPercent}% ${artworkFraming.originYPercent}%`,
          }"
          alt=""
          aria-hidden="true"
        />
        <span v-if="artwork" class="secret-card__shade" aria-hidden="true" />
        <div class="secret-card__content" :class="{ illustrated: Boolean(artwork) }">
          <Eye :size="22" />
          <strong>{{ title }}</strong>
          <span v-if="subtitle">{{ subtitle }}</span>
          <slot />
        </div>
      </template>
      <div v-else class="secret-card__cover">
        <EyeOff :size="25" />
        <strong>私密信息</strong>
        <span>{{ hint }}</span>
      </div>
    </button>
  </div>
</template>

<style scoped>
.secret-card-shell {
  display: grid;
  gap: 10px;
}

.secret-card-shell.has-role-art {
  width: min(100%, 400px);
  margin-inline: auto;
}

.role-skin-lock {
  display: inline-flex;
  align-items: center;
  justify-self: end;
  gap: 6px;
  border: 1px solid rgba(225, 188, 104, 0.18);
  border-radius: 999px;
  padding: 6px 9px;
  color: var(--muted);
  background: rgba(225, 188, 104, 0.07);
  font-size: 9px;
  font-weight: 850;
}

.role-skin-lock svg,
.role-skin-lock strong {
  color: var(--gold);
}

.secret-card.has-role-art {
  aspect-ratio: 2 / 3;
  min-height: 0;
  padding: 0;
  isolation: isolate;
}

.secret-card__art,
.secret-card__inner-art,
.secret-card__shade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.secret-card__art {
  z-index: 0;
  object-fit: cover;
  transform: scale(var(--role-art-scale, 1));
  transform-origin: var(--role-art-origin, 50% 50%);
}

.secret-card__art.preserves-frame {
  transform: none;
}

.secret-card__inner-art {
  z-index: 0;
  object-fit: cover;
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
}

.secret-card__shade {
  z-index: 1;
  background:
    linear-gradient(180deg, transparent 30%, rgba(3, 13, 15, 0.2) 49%, rgba(3, 13, 15, 0.94) 76%),
    linear-gradient(90deg, rgba(3, 13, 15, 0.16), transparent 26%, transparent 74%, rgba(3, 13, 15, 0.16));
}

.secret-card__content.illustrated {
  z-index: 2;
  align-content: end;
  min-height: inherit;
  padding: 58% 22px 23px;
}

.secret-card__content.illustrated > svg {
  color: var(--gold);
  filter: drop-shadow(0 2px 7px rgba(0, 0, 0, 0.75));
}

.secret-card__content.illustrated > strong,
.secret-card__content.illustrated > span,
.secret-card__content.illustrated :deep(.secret-description),
.secret-card__content.illustrated :deep(.muted-secret) {
  text-shadow: 0 2px 9px rgba(0, 0, 0, 0.9);
}

.secret-card__content.illustrated :deep(.knowledge-list span) {
  border-color: rgba(255, 255, 255, 0.18);
  background: rgba(2, 10, 12, 0.66);
  backdrop-filter: blur(7px);
}

@media (max-width: 430px) {
  .secret-card__content.illustrated {
    padding-right: 16px;
    padding-bottom: 18px;
    padding-left: 16px;
  }
}
</style>
