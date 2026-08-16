<script setup lang="ts">
import { Check, ChevronRight, Images, LockKeyhole, Trophy, X } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { RoleSkinLoadoutRoleOption } from './uiTypes'
import UiIconButton from './ui/UiIconButton.vue'

const props = withDefaults(defineProps<{
  roles: RoleSkinLoadoutRoleOption[]
  loading?: boolean
  error?: string | null
}>(), {
  loading: false,
  error: null,
})

const emit = defineEmits<{
  select: [roleCode: string, skinId: string]
  retry: []
}>()
const DESKTOP_MAX_PICKER_COLUMNS = 5
const MEDIUM_MAX_PICKER_COLUMNS = 3
const COMPACT_MAX_PICKER_COLUMNS = 2
const activeRoleCode = ref<string | null>(null)
const activeRole = computed(() => (
  props.roles.find((role) => role.code === activeRoleCode.value) ?? null
))
const eventAllUnlocked = computed(() => (
  props.roles.some((role) => role.eventAllUnlocked)
))
const pickerColumnCount = computed(() => Math.max(
  1,
  Math.min(
    activeRole.value?.choices.length ?? 0,
    DESKTOP_MAX_PICKER_COLUMNS,
  ),
))
const pickerLayoutStyle = computed(() => ({
  '--role-skin-choice-columns': pickerColumnCount.value,
  '--role-skin-choice-medium-columns': Math.min(
    pickerColumnCount.value,
    MEDIUM_MAX_PICKER_COLUMNS,
  ),
  '--role-skin-choice-compact-columns': Math.min(
    pickerColumnCount.value,
    COMPACT_MAX_PICKER_COLUMNS,
  ),
}))

function closePicker() {
  activeRoleCode.value = null
}

function chooseSkin(role: RoleSkinLoadoutRoleOption, skinId: string, unlocked: boolean) {
  if (!unlocked) return
  emit('select', role.code, skinId)
  closePicker()
}

function handleEscape(event: KeyboardEvent) {
  if (event.key === 'Escape') closePicker()
}

onMounted(() => window.addEventListener('keydown', handleEscape))
onBeforeUnmount(() => window.removeEventListener('keydown', handleEscape))
</script>

<template>
  <section class="surface role-skin-loadout" aria-labelledby="role-skin-loadout-title">
    <header class="role-skin-loadout-heading">
      <span><Images :size="20" /></span>
      <div>
        <strong id="role-skin-loadout-title">十角色身份画风</strong>
        <small v-if="eventAllUnlocked">本周限时开放 · 所有角色的全部皮肤均可自由选择 · 开局后锁定</small>
        <small v-else>每个角色单独选择 · 暗影梅林与梅林共享解锁进度 · 心怀异念之臣与忠臣共享解锁进度 · 开局后锁定</small>
      </div>
    </header>

    <button v-if="error" type="button" class="role-skin-error" @click="emit('retry')">
      {{ error }} · 点击重试
    </button>
    <p v-else-if="loading" class="role-skin-loading" role="status">正在读取角色胜场与皮肤权限…</p>

    <div class="role-skin-role-grid" aria-label="为十个角色选择身份画风">
      <button
        v-for="role in roles"
        :key="role.code"
        type="button"
        class="role-skin-role"
        :data-role-skin-role="role.code"
        :aria-label="`设置${role.name}的身份画风，当前为${role.currentSkinName}`"
        @click="activeRoleCode = role.code"
      >
        <span class="role-skin-role-art">
          <img
            :src="role.currentArtwork"
            :alt="`${role.name}的${role.currentSkinName}画风`"
            :style="{ '--artwork-scale': role.currentFraming.scale, '--artwork-origin': `${role.currentFraming.originXPercent}% ${role.currentFraming.originYPercent}%` }"
            loading="lazy"
            draggable="false"
          />
          <small>{{ role.group }}</small>
        </span>
        <span class="role-skin-role-copy">
          <span><strong>{{ role.name }}</strong><em>{{ role.currentSkinName }}</em></span>
          <small v-if="role.eventAllUnlocked">本周限时 · 全部皮肤可用</small>
          <small v-else-if="role.legacyAllUnlocked">老账号 · 全部已解锁</small>
          <small v-else>排位胜场 {{ role.wins }} · 升级 {{ Math.min(role.wins, role.upgradeWinsRequired) }}/{{ role.upgradeWinsRequired }} · 终极 {{ Math.min(role.wins, role.ultimateWinsRequired) }}/{{ role.ultimateWinsRequired }}</small>
        </span>
        <ChevronRight :size="17" aria-hidden="true" />
      </button>
    </div>
  </section>

  <Teleport to="body">
    <div v-if="activeRole" class="role-skin-picker-backdrop" @click.self="closePicker">
      <section
        class="role-skin-picker-modal adaptive-dialog"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="`role-skin-picker-${activeRole.code}`"
        :style="pickerLayoutStyle"
      >
        <header>
          <div>
            <small>{{ activeRole.group }} · 排位胜场 {{ activeRole.wins }}</small>
            <h2 :id="`role-skin-picker-${activeRole.code}`">{{ activeRole.name }}的对局画风</h2>
            <p v-if="activeRole.eventAllUnlocked">本周限时开放至 8 月 10 日 00:00，全部画风可自由选择；活动结束后恢复原解锁进度。</p>
            <p v-else-if="activeRole.legacyAllUnlocked">老账号已保留全部画风，可自由选择。</p>
            <p v-else>赢 {{ activeRole.upgradeWinsRequired }} 局解锁全部升级款，赢 {{ activeRole.ultimateWinsRequired }} 局解锁终极款。</p>
          </div>
          <UiIconButton
            class="adaptive-touch-target"
            aria-label="关闭角色画风选择"
            @click="closePicker"
          >
            <X :size="20" />
          </UiIconButton>
        </header>

        <div class="role-skin-choice-grid adaptive-scroll-region">
          <button
            v-for="choice in activeRole.choices"
            :key="choice.id"
            type="button"
            class="role-skin-choice"
            :class="{ locked: !choice.unlocked, selected: choice.name === activeRole.currentSkinName }"
            :data-role-skin-choice="choice.id"
            :disabled="!choice.unlocked"
            @click="chooseSkin(activeRole, choice.id, choice.unlocked)"
          >
            <span class="role-skin-choice-art">
              <img
                :src="choice.artwork"
                :alt="`${activeRole.name}的${choice.name}画风`"
                :style="{ '--artwork-scale': choice.framing.scale, '--artwork-origin': `${choice.framing.originXPercent}% ${choice.framing.originYPercent}%` }"
                draggable="false"
              />
              <small>{{ choice.tier }}</small>
              <span v-if="choice.name === activeRole.currentSkinName" class="role-skin-selected"><Check :size="15" /></span>
              <span v-else-if="!choice.unlocked" class="role-skin-lock"><LockKeyhole :size="15" /></span>
            </span>
            <span class="role-skin-choice-copy">
              <strong>{{ choice.name }}</strong>
              <small v-if="choice.unlocked">{{ choice.description }}</small>
              <small v-else><Trophy :size="12" /> 再用该角色赢 {{ choice.remainingWins }} 局</small>
            </span>
          </button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.role-skin-loadout { display: grid; gap: 14px; padding: 16px; }
.role-skin-loadout-heading { display: flex; align-items: center; gap: 12px; }
.role-skin-loadout-heading > span { display: grid; flex: 0 0 auto; place-items: center; width: 42px; height: 42px; border: 1px solid color-mix(in srgb, var(--accent) 28%, var(--line)); border-radius: 14px; color: var(--accent); background: color-mix(in srgb, var(--accent) 8%, var(--surface-inset)); }
.role-skin-loadout-heading > div { display: grid; gap: 4px; }
.role-skin-loadout-heading strong { font-family: "Songti SC", "STSong", serif; font-size: 14px; }
.role-skin-loadout-heading small { color: var(--muted); font-size: 10px; }
.role-skin-loading, .role-skin-error { margin: 0; border: 1px solid var(--line); border-radius: 10px; padding: 9px 11px; color: var(--muted); background: var(--surface-inset); font-size: 10px; }
.role-skin-error { width: 100%; color: #f2a7a2; text-align: left; cursor: pointer; }
.role-skin-role-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }
.role-skin-role { display: grid; grid-template-columns: 56px minmax(0, 1fr) auto; align-items: center; gap: 10px; min-width: 0; min-height: 72px; overflow: hidden; border: 1px solid var(--line); border-radius: 14px; padding: 7px 9px 7px 7px; color: var(--text); background: rgba(var(--surface-header-rgb), .56); text-align: left; cursor: pointer; }
.role-skin-role:hover { border-color: color-mix(in srgb, var(--accent) 42%, var(--line)); background: color-mix(in srgb, var(--accent) 7%, var(--surface-inset)); }
.role-skin-role > svg { flex: 0 0 auto; color: var(--muted); }
.role-skin-role-art { position: relative; align-self: stretch; min-height: 56px; overflow: hidden; border-radius: 9px; background: #061313; }
.role-skin-role-art img, .role-skin-choice-art img { width: 100%; height: 100%; object-fit: cover; transform: scale(var(--artwork-scale, 1)); transform-origin: var(--artwork-origin, 50% 50%); }
.role-skin-role-art small { position: absolute; inset: auto 4px 4px; overflow: hidden; border-radius: 999px; padding: 2px 5px; color: #f4f1df; background: rgba(2, 9, 10, .76); font-size: 7px; font-weight: 850; text-align: center; text-overflow: ellipsis; white-space: nowrap; }
.role-skin-role-copy, .role-skin-role-copy > span { display: grid; gap: 3px; min-width: 0; }
.role-skin-role-copy > span { grid-template-columns: minmax(0, 1fr) auto; align-items: baseline; }
.role-skin-role-copy strong, .role-skin-role-copy em { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.role-skin-role-copy strong { font-family: "Songti SC", "STSong", serif; font-size: 12px; }
.role-skin-role-copy em { color: var(--accent); font-size: 8px; font-style: normal; }
.role-skin-role-copy > small { overflow: hidden; color: var(--muted); font-size: 8px; line-height: 1.45; text-overflow: ellipsis; white-space: nowrap; }
.role-skin-picker-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; place-items: center; padding: 16px; background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: blur(12px); }
.role-skin-picker-modal { display: grid; grid-template-rows: auto minmax(0, 1fr); width: fit-content; max-width: calc(100vw - 32px); max-height: min(90dvh, 760px); min-height: 0; overflow: hidden; border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--line)); border-radius: 24px; color: var(--text); background: var(--modal-surface); box-shadow: var(--shadow); }
.role-skin-picker-modal > header { display: flex; align-items: center; justify-content: space-between; gap: 16px; border-bottom: 1px solid var(--line); padding: 18px 22px; background: rgba(var(--surface-header-rgb), .92); }
.role-skin-picker-modal > header > div { display: grid; gap: 4px; }
.role-skin-picker-modal header small { color: var(--accent); font-size: 9px; font-weight: 850; }
.role-skin-picker-modal h2 { margin: 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(22px, 3vw, 32px); }
.role-skin-picker-modal p { margin: 0; color: var(--muted); font-size: 10px; }
.role-skin-choice-grid { display: grid; grid-template-columns: repeat(var(--role-skin-choice-columns, 5), minmax(160px, 180px)); grid-auto-rows: max-content; align-content: start; align-items: start; gap: 11px; min-height: 0; padding: 18px 20px 24px; overflow-y: auto; }
.role-skin-choice { display: grid; gap: 9px; min-width: 0; overflow: hidden; border: 1px solid var(--line); border-radius: 15px; padding: 6px 6px 10px; color: var(--text); background: rgba(var(--surface-header-rgb), .56); text-align: left; cursor: pointer; }
.role-skin-choice.selected { border-color: color-mix(in srgb, var(--accent) 58%, var(--line)); background: color-mix(in srgb, var(--accent) 9%, var(--surface-inset)); }
.role-skin-choice.locked { cursor: not-allowed; opacity: .62; }
.role-skin-choice-art { position: relative; display: block; aspect-ratio: 2 / 3; overflow: hidden; border-radius: 10px; background: #061313; }
.role-skin-choice-art > small, .role-skin-selected, .role-skin-lock { position: absolute; z-index: 2; top: 7px; display: grid; place-items: center; min-height: 24px; border: 1px solid rgba(255, 255, 255, .18); color: #f5f2e8; background: rgba(2, 9, 10, .76); backdrop-filter: blur(8px); }
.role-skin-choice-art > small { left: 7px; border-radius: 999px; padding: 0 8px; font-size: 8px; font-weight: 900; }
.role-skin-selected, .role-skin-lock { right: 7px; width: 24px; border-radius: 50%; color: #ffe297; }
.role-skin-lock { color: #f3b0ad; }
.role-skin-choice-copy { display: grid; gap: 3px; min-width: 0; padding-inline: 3px; }
.role-skin-choice-copy strong { overflow: hidden; font-family: "Songti SC", "STSong", serif; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.role-skin-choice-copy small { display: flex; align-items: center; gap: 4px; min-height: 26px; color: var(--muted); font-size: 8px; line-height: 1.4; }
@container (max-width: 980px) { .role-skin-role-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@container (max-width: 620px) { .role-skin-loadout { padding-inline: 13px; } .role-skin-role-grid { grid-template-columns: 1fr 1fr; gap: 7px; } .role-skin-role { grid-template-columns: 44px minmax(0, 1fr); min-height: 62px; gap: 8px; padding: 6px; } .role-skin-role > svg { display: none; } .role-skin-role-art { min-height: 50px; } .role-skin-role-copy > span { grid-template-columns: 1fr; } .role-skin-role-copy em { font-size: 7px; } .role-skin-role-copy > small { white-space: normal; } }
@container (max-width: 370px) { .role-skin-role-grid { grid-template-columns: 1fr; } }
@media (max-width: 980px) { .role-skin-choice-grid { grid-template-columns: repeat(var(--role-skin-choice-medium-columns, 3), minmax(160px, 180px)); } }
@media (max-width: 620px) { .role-skin-picker-backdrop { align-items: end; padding: 8px; } .role-skin-picker-modal { width: 100%; max-width: 100%; max-height: calc(100dvh - 8px); border-radius: 20px 20px 0 0; } .role-skin-picker-modal > header { padding: 14px; } .role-skin-choice-grid { grid-template-columns: repeat(var(--role-skin-choice-compact-columns, 2), minmax(0, 1fr)); gap: 9px; padding: 12px 12px 20px; } }
</style>
