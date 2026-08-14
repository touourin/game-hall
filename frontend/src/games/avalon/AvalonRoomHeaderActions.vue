<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  CircleHelp,
  Eye,
} from '@lucide/vue'
import BaseModal from '../../components/ui/BaseModal.vue'
import ModeGuide from '../../components/ModeGuide.vue'
import PressRevealCard from '../../components/PressRevealCard.vue'
import type { ArcadeSnapshot } from '../../types/arcade'
import { AVALON_COURT_GUIDE } from './modeGuide'
import {
  defaultRoleSkinLoadout,
  roleArtwork,
  roleArtworkFraming,
  roleSkinName,
  roleSkinRoleCode,
  storedRoleSkinLoadout,
  storedRoleSkinLoadoutLock,
  type RoleSkinId,
} from './roleSkins'
import { isAvalonArcadeSnapshot } from './types'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const showIdentity = ref(false)
const showRules = ref(false)

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
const activeRoleSkin = computed<RoleSkinId>(() => {
  const snapshot = avalonSnapshot.value
  const role = roleSkinRoleCode(snapshot?.game.self.role?.code ?? '')
  if (!snapshot || !role) return 'classic-tabletop'
  const loadout = storedRoleSkinLoadoutLock(snapshot.roomCode)
    ?? (viewerIsGuest.value
      ? defaultRoleSkinLoadout()
      : storedRoleSkinLoadout(roleSkinAccountId.value))
  return loadout[role]
})

function playerLabel(playerId: string): string {
  const player = props.snapshot.players.find((item) => item.id === playerId)
  return player ? `${player.seat + 1}号 ${player.name}` : '未知玩家'
}

function selfRoleArtwork(): string | null {
  const roleCode = avalonSnapshot.value?.game.self.role?.code
  return roleCode ? roleArtwork(roleCode, activeRoleSkin.value) : null
}

function selfRoleArtworkFraming() {
  return roleArtworkFraming(
    avalonSnapshot.value?.game.self.role?.code ?? '',
    activeRoleSkin.value,
  )
}
</script>

<template>
  <button
    v-if="avalonSnapshot?.game.self.role && avalonSnapshot.game.phase !== 'game_over'"
    class="header-action"
    type="button"
    aria-label="查看我的身份"
    @click="showIdentity = true"
  >
    <Eye :size="20" />
  </button>
  <button
    v-if="avalonSnapshot"
    class="header-action"
    type="button"
    aria-label="查看玩法说明"
    @click="showRules = true"
  >
    <CircleHelp :size="21" />
  </button>

  <BaseModal
    v-if="showIdentity && avalonSnapshot?.game.self.role"
    aria-label="我的身份"
    panel-class="identity-modal"
    close-label="关闭身份"
    inline
    @close="showIdentity = false"
  >
    <PressRevealCard
      :title="avalonSnapshot.game.self.role.label"
      :subtitle="avalonSnapshot.game.self.role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营'"
      :artwork="selfRoleArtwork()"
      :artwork-label="roleSkinName(activeRoleSkin)"
      :artwork-framing="selfRoleArtworkFraming()"
      hint="按住重新查看身份"
    >
      <p class="secret-description">{{ avalonSnapshot.game.self.role.description }}</p>
      <div v-if="avalonSnapshot.game.self.role.knowledge.length" class="knowledge-list">
        <span
          v-for="item in avalonSnapshot.game.self.role.knowledge"
          :key="item.playerId"
        >
          {{ playerLabel(item.playerId) }} · {{ item.label }}
        </span>
      </div>
      <div v-if="avalonSnapshot.game.lady.myChecks.length" class="knowledge-list">
        <span
          v-for="check in avalonSnapshot.game.lady.myChecks"
          :key="`${check.missionNumber}-${check.targetId}`"
        >
          仙女：{{ playerLabel(check.targetId) }} ·
          {{ check.alignment === 'good' ? '好人阵营' : '坏人阵营' }}
        </span>
      </div>
    </PressRevealCard>
  </BaseModal>

  <BaseModal
    v-if="showRules && avalonSnapshot"
    aria-label="阿瓦隆玩法说明"
    panel-class="rules-modal"
    close-label="关闭玩法说明"
    mobile-sheet
    inline
    @close="showRules = false"
  >
    <span class="modal-icon"><CircleHelp :size="25" /></span>
    <h2>{{ avalonSnapshot.game.settings.mode === 'court_undercurrent' ? '王庭暗流 · 玩法说明' : '标准阿瓦隆 · 玩法说明' }}</h2>
    <p>{{ avalonSnapshot.game.settings.mode === 'court_undercurrent' ? '背景故事、特殊角色与终局规则集中在这里。' : '本局采用标准阿瓦隆规则。' }}</p>
    <ModeGuide
      v-if="avalonSnapshot.game.settings.mode === 'court_undercurrent'"
      :content="AVALON_COURT_GUIDE"
    />
    <section class="avalon-core-rules">
      <h3>阿瓦隆基础规则</h3>
      <ul>
        <li>好人只能提交任务成功，坏人可选择成功或失败。</li>
        <li>队伍表决需要过半赞成，平票视为否决。</li>
        <li>同一任务连续五次组队被否决，当前任务直接失败。</li>
        <li>部分玩家掉线超过 10 分钟，其所属阵营弃权；全员离线只进入房间清理流程。</li>
        <li v-if="snapshot.players.length >= 7">第四次任务需要两张失败票才会失败。</li>
        <li v-if="avalonSnapshot.game.settings.ladyEnabled">仙女只查阵营，持有者可以谎报查验结果。</li>
      </ul>
    </section>
  </BaseModal>
</template>
