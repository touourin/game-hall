<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import RoleSkinLoadoutPicker from '../../components/RoleSkinLoadoutPicker.vue'
import type { RoleSkinLoadoutRoleOption } from '../../components/uiTypes'
import type { ArcadeSnapshot } from '../../types/arcade'
import {
  ROLE_SKINS,
  ROLE_SKIN_ROLES,
  clearRoleSkinLoadoutLock,
  defaultRoleSkinLoadout,
  rememberRoleSkinLoadout,
  roleArtwork,
  roleArtworkFraming,
  roleSkinRoleCode,
  storedRoleSkinLoadout,
  type RoleSkinLoadout,
} from './roleSkins'
import {
  emptyAvalonRoleSkinProgress,
  isAvalonRoleSkinFreeWeek,
  isRoleSkinUnlocked,
  loadAvalonRoleSkinProgress,
} from './roleSkinProgress'
import { isAvalonArcadeSnapshot } from './types'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const avalonSnapshot = computed(() => (
  isAvalonArcadeSnapshot(props.snapshot) ? props.snapshot : null
))
const viewerIsGuest = computed(() => (
  props.snapshot.viewer?.isGuest ?? props.snapshot.self.isGuest
))
const roleSkinAccountId = computed(() => (
  props.snapshot.viewer?.accountId
  ?? props.snapshot.self.accountId
  ?? props.snapshot.viewer?.id
  ?? props.snapshot.self.id
))
const selectedLoadout = ref<RoleSkinLoadout>(defaultRoleSkinLoadout())
const progress = ref(emptyAvalonRoleSkinProgress())
const loading = ref(false)
const errorMessage = ref<string | null>(null)
let progressRequest = 0

const roleOptions = computed<RoleSkinLoadoutRoleOption[]>(() => (
  ROLE_SKIN_ROLES.map((role) => {
    const progressCode = role.code === 'shadow_merlin'
      ? 'merlin'
      : role.code === 'dissenting_courtier'
        ? 'loyal_servant'
        : role.code
    const roleProgress = progress.value.roles[progressCode]
    const selectedSkinId = selectedLoadout.value[role.code]
    const selectedSkin = ROLE_SKINS.find((skin) => skin.id === selectedSkinId)
      ?? ROLE_SKINS[0]!
    return {
      code: role.code,
      name: role.name,
      group: role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营',
      wins: roleProgress.wins,
      currentSkinName: selectedSkin.name,
      currentArtwork: roleArtwork(role.code, selectedSkin.id) ?? selectedSkin.preview,
      currentFraming: roleArtworkFraming(role.code, selectedSkin.id),
      legacyAllUnlocked: progress.value.legacyAllUnlocked,
      eventAllUnlocked: progress.value.eventAllUnlocked,
      upgradeWinsRequired: progress.value.upgradeWinsRequired,
      ultimateWinsRequired: progress.value.ultimateWinsRequired,
      choices: ROLE_SKINS.map((skin) => {
        const requiredWins = skin.tier === '终极'
          ? progress.value.ultimateWinsRequired
          : skin.tier === '升级'
            ? progress.value.upgradeWinsRequired
            : 0
        return {
          id: skin.id,
          name: skin.name,
          description: skin.description,
          tier: skin.tier,
          artwork: roleArtwork(role.code, skin.id) ?? skin.preview,
          framing: roleArtworkFraming(role.code, skin.id),
          unlocked: isRoleSkinUnlocked(progress.value, role.code, skin.id),
          remainingWins: Math.max(0, requiredWins - roleProgress.wins),
        }
      }),
    }
  })
))

function reconciledLoadout(loadout: RoleSkinLoadout): RoleSkinLoadout {
  return Object.fromEntries(
    ROLE_SKIN_ROLES.map((role) => {
      const skin = loadout[role.code]
      return [
        role.code,
        isRoleSkinUnlocked(progress.value, role.code, skin)
          ? skin
          : 'classic-tabletop',
      ]
    }),
  ) as RoleSkinLoadout
}

async function refreshProgress() {
  if (!avalonSnapshot.value) return
  const request = ++progressRequest
  errorMessage.value = null
  if (viewerIsGuest.value) {
    progress.value = emptyAvalonRoleSkinProgress(isAvalonRoleSkinFreeWeek())
    selectedLoadout.value = defaultRoleSkinLoadout()
    return
  }
  loading.value = true
  try {
    const loaded = await loadAvalonRoleSkinProgress()
    if (request !== progressRequest) return
    progress.value = loaded
    const reconciled = reconciledLoadout(selectedLoadout.value)
    selectedLoadout.value = reconciled
    rememberRoleSkinLoadout(roleSkinAccountId.value, reconciled)
  } catch (error) {
    if (request !== progressRequest) return
    progress.value = emptyAvalonRoleSkinProgress(isAvalonRoleSkinFreeWeek())
    selectedLoadout.value = defaultRoleSkinLoadout()
    errorMessage.value = error instanceof Error
      ? error.message
      : '身份皮肤进度读取失败'
  } finally {
    if (request === progressRequest) loading.value = false
  }
}

function selectRoleSkin(roleCode: string, skinId: string) {
  const role = roleSkinRoleCode(roleCode)
  const skin = ROLE_SKINS.find((option) => option.id === skinId)?.id
  if (!role || !skin || !isRoleSkinUnlocked(progress.value, role, skin)) return
  const next = { ...selectedLoadout.value, [role]: skin }
  selectedLoadout.value = next
  if (!viewerIsGuest.value) rememberRoleSkinLoadout(roleSkinAccountId.value, next)
}

watch(
  () => [props.snapshot.roomCode, roleSkinAccountId.value, viewerIsGuest.value] as const,
  () => {
    if (!avalonSnapshot.value) return
    clearRoleSkinLoadoutLock(props.snapshot.roomCode)
    selectedLoadout.value = viewerIsGuest.value
      ? defaultRoleSkinLoadout()
      : storedRoleSkinLoadout(roleSkinAccountId.value)
    void refreshProgress()
  },
  { immediate: true },
)
</script>

<template>
  <RoleSkinLoadoutPicker
    v-if="avalonSnapshot"
    :roles="roleOptions"
    :loading="loading"
    :error="errorMessage"
    @select="selectRoleSkin"
    @retry="refreshProgress"
  />
</template>
