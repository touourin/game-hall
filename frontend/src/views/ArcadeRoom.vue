<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  Bot,
  ChevronRight,
  CircleHelp,
  Crown,
  Eye,
  Handshake,
  QrCode,
  RotateCcw,
  Settings2,
  Undo2,
  UsersRound,
  X,
} from '@lucide/vue'
import ArcadeChatPanel from '../components/ArcadeChatPanel.vue'
import ArtworkSkinPicker from '../components/ArtworkSkinPicker.vue'
import GameSkinPicker from '../components/GameSkinPicker.vue'
import InviteLinkPanel from '../components/InviteLinkPanel.vue'
import GameRuleSettings from '../components/GameRuleSettings.vue'
import HostTransferNotice from '../components/HostTransferNotice.vue'
import RoomExitButton from '../components/RoomExitButton.vue'
import RoomDissolveButton from '../components/RoomDissolveButton.vue'
import RoomPageHeader from '../components/RoomPageHeader.vue'
import RoomRecordActions from '../components/RoomRecordActions.vue'
import RoomInviteModal from '../components/RoomInviteModal.vue'
import RoomKickButton from '../components/RoomKickButton.vue'
import ModeGuide from '../components/ModeGuide.vue'
import PressRevealCard from '../components/PressRevealCard.vue'
import { useArcadeStore } from '../stores/arcade'
import {
  isAvalonArcadeSnapshot,
  type ArcadeSnapshot,
} from '../types/arcade'
import type { ArtworkSkinOption } from '../components/uiTypes'
import { gameRuleLabels, withDefaultGameRules } from '../gameRules'
import { AVALON_COURT_GUIDE } from '../gameModeGuides'
import {
  ROLE_SKINS,
  clearRoleSkinLock,
  lockRoleSkin,
  rememberRoleSkin,
  roleArtwork,
  roleArtworkFraming,
  roleSkinName,
  roleSkinPreviewRoles,
  storedRoleSkin,
  storedRoleSkinLock,
  type RoleSkinId,
} from '../gameRoleSkins'
import {
  gameSkinCssVariables,
  gameSkinKind,
  rememberGameSkin,
  storedGameSkin,
  type GameSkinId,
} from '../gameSkins'
import DoudizhuTable from '../games/doudizhu/DoudizhuTable.vue'
import GoBoard from '../games/go/GoBoard.vue'
import GomokuBoard from '../games/gomoku/GomokuBoard.vue'
import XiangqiBoard from '../games/xiangqi/XiangqiBoard.vue'
import JunqiBoard from '../games/junqi/JunqiBoard.vue'
import ReactionTest from '../games/reaction/ReactionTest.vue'
import SchulteGrid from '../games/schulte/SchulteGrid.vue'
import MinesweeperBoard from '../games/minesweeper/MinesweeperBoard.vue'
import HanoiGame from '../games/hanoi/HanoiGame.vue'
import PokerTable from '../games/poker/PokerTable.vue'
import AvalonTable from '../games/avalon/AvalonTable.vue'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const emit = defineEmits<{ settings: [] }>()
const arcade = useArcadeStore()
const avalonSnapshot = computed(
  () => isAvalonArcadeSnapshot(props.snapshot) ? props.snapshot.game : null,
)
const ruleEditor = ref<Record<string, unknown> | null>(null)
const showQr = ref(false)
const showPlayerNumbers = ref(false)
const showIdentity = ref(false)
const showAvalonRules = ref(false)
const sharedChat = ref<{ openChat: () => Promise<void> } | null>(null)
const activeGameSkin = ref<GameSkinId>(storedGameSkin())
const selectedRoleSkin = ref<RoleSkinId>(storedRoleSkin())
const lockedRoleSkin = ref<RoleSkinId | null>(null)
const missingPlayers = computed(
  () => Math.max(0, (props.snapshot.minimumPlayers ?? props.snapshot.requiredPlayers) - props.snapshot.players.length),
)
const availableSeats = computed(
  () => Math.max(0, props.snapshot.requiredPlayers - props.snapshot.players.length),
)
const playerStripColumns = computed(() => {
  const playerCount = props.snapshot.players.length
  if (playerCount <= 5) return Math.max(1, playerCount)
  if (playerCount === 6) return 3
  return Math.ceil(playerCount / 2)
})
const playerStripStyle = computed(() => {
  const columns = playerStripColumns.value
  const widthPercent = Number((100 / columns).toFixed(6))
  const gapCorrection = Number((10 * (columns - 1) / columns).toFixed(3))
  return {
    '--player-card-width': `calc(${widthPercent}% - ${gapCorrection}px)`,
  }
})
const inviteUrl = computed(() => {
  const url = new URL(window.location.href)
  url.pathname = `/games/${props.snapshot.gameKey}/rooms/${props.snapshot.roomCode}`
  url.search = ''
  url.hash = ''
  return url.toString()
})
const selfRematchReady = computed(() =>
  props.snapshot.rematchReadyPlayerIds.includes(props.snapshot.self.id),
)
const isSolo = computed(() => ['reaction', 'schulte', 'minesweeper', 'hanoi'].includes(props.snapshot.gameKey))
const activeGameSkinKind = computed(() => gameSkinKind(props.snapshot.gameKey))
const activeGameSkinStyle = computed(() => (
  activeGameSkinKind.value ? gameSkinCssVariables(activeGameSkin.value) : undefined
))
const activeRoleSkin = computed(
  () => lockedRoleSkin.value ?? selectedRoleSkin.value,
)
const roleArtworkOptions: ArtworkSkinOption[] = ROLE_SKINS.map((skin) => ({
  ...skin,
  items: roleSkinPreviewRoles(skin.id).map((role) => ({
    id: role.code,
    name: role.name,
    group: role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营',
    artwork: role.artwork,
    framing: role.framing,
  })),
}))
const avalonPhaseLabel = computed(() => {
  const phase = avalonSnapshot.value?.phase
  if (!phase) return ''
  return {
    lobby: '等待圆桌集结',
    role_reveal: '确认身份',
    team_building: '组建任务队伍',
    team_voting: '表决任务队伍',
    mission_voting: '执行秘密任务',
    round_result: '任务结算',
    lady_select: '湖中仙女',
    lady_reveal: '仙女启示',
    assassination: '最后刺杀',
    dagger_grant: '黑誓授刃',
    final_council: '最后议事',
    game_over: '本局终章',
  }[phase]
})
const roomHeaderEyebrow = computed(() => {
  const suffix = props.snapshot.gameKey === 'avalon'
    ? ` · ${avalonSnapshot.value?.settings.mode === 'court_undercurrent' ? '王庭暗流' : '标准模式'} · ${avalonPhaseLabel.value}`
    : props.snapshot.gameKey === 'junqi'
    ? ` · ${props.snapshot.options.mode === 'flip' ? '翻棋军旗' : '暗军旗'}`
    : props.snapshot.gameKey === 'reaction'
      ? ' · 单人测试'
      : props.snapshot.gameKey === 'schulte'
        ? ' · 单人专注'
        : props.snapshot.gameKey === 'minesweeper'
          ? ` · ${props.snapshot.game.difficultyLabel}`
          : props.snapshot.gameKey === 'hanoi'
            ? ' · 单人益智'
            : ''
  return `${props.snapshot.gameName}${suffix}`
})
const roomHeaderTitle = computed(() => {
  const soloTitles: Partial<Record<ArcadeSnapshot['gameKey'], string>> = {
    reaction: '反应挑战',
    schulte: '舒尔特挑战',
    minesweeper: '扫雷挑战',
    hanoi: '汉诺塔挑战',
  }
  return soloTitles[props.snapshot.gameKey] ?? `房间 ${props.snapshot.roomCode}`
})
const roomStatsMode = computed(() => (
  props.snapshot.gameKey === 'minesweeper'
    ? String(props.snapshot.options.difficulty ?? 'beginner')
    : undefined
))
watch(
  () => [props.snapshot.phase, props.snapshot.gameKey] as const,
  ([phase]) => {
    if (phase !== 'lobby' || isSolo.value) showQr.value = false
  },
)
watch(
  () => [props.snapshot.roomCode, avalonSnapshot.value?.phase] as const,
  ([roomCode, phase]) => {
    if (!phase) return
    if (phase === 'lobby') {
      clearRoleSkinLock(roomCode)
      lockedRoleSkin.value = null
      selectedRoleSkin.value = storedRoleSkin()
      return
    }
    lockedRoleSkin.value =
      storedRoleSkinLock(roomCode) ??
      lockRoleSkin(roomCode, selectedRoleSkin.value)
  },
  { immediate: true },
)
const exitDescription = computed(() => {
  if (props.snapshot.phase === 'lobby') {
    return '你会离开房间并让出座位；如果你是房主，房主将自动移交。'
  }
  if (props.snapshot.phase === 'finished') {
    return '你会退出当前房间并返回游戏大厅。'
  }
  return '你的座位和本局进度都会保留，可以从大厅随时返回。'
})

function openRuleEditor() {
  ruleEditor.value = withDefaultGameRules(
    props.snapshot.gameKey,
    props.snapshot.options,
  )
}

async function saveRules() {
  if (!ruleEditor.value) return
  if (await arcade.updateRules(ruleEditor.value)) ruleEditor.value = null
}

function selectGameSkin(skin: GameSkinId) {
  activeGameSkin.value = skin
  rememberGameSkin(skin)
}

function selectRoleSkin(skin: string) {
  if (avalonSnapshot.value?.phase !== 'lobby') return
  const selected = ROLE_SKINS.find((option) => option.id === skin)?.id
  if (!selected) return
  selectedRoleSkin.value = selected
  rememberRoleSkin(selected)
}

function playerNumber(playerId: string): number | null {
  const player = props.snapshot.players.find((item) => item.id === playerId)
  return player ? player.seat + 1 : null
}

function avalonPlayerLabel(playerId: string): string {
  const player = props.snapshot.players.find((item) => item.id === playerId)
  return player ? `${player.seat + 1}号 ${player.name}` : '未知玩家'
}

function selfRoleArtwork(): string | null {
  const roleCode = avalonSnapshot.value?.self.role?.code
  return roleCode ? roleArtwork(roleCode, activeRoleSkin.value) : null
}

function selfRoleArtworkFraming() {
  return roleArtworkFraming(
    avalonSnapshot.value?.self.role?.code ?? '',
    activeRoleSkin.value,
  )
}

function openSharedChat() {
  void sharedChat.value?.openChat()
}

</script>

<template>
  <main
    class="arcade-room page-container"
    :class="{ 'arcade-room--wide': ['avalon', 'poker', 'doudizhu', 'junqi', 'minesweeper'].includes(snapshot.gameKey) }"
    :data-game-skin="activeGameSkinKind ? activeGameSkin : undefined"
    :style="activeGameSkinStyle"
  >
    <RoomPageHeader
      :eyebrow="roomHeaderEyebrow"
      :title="roomHeaderTitle"
    >
      <template v-if="avalonSnapshot" #details>
        <button
          class="self-number-trigger"
          type="button"
          :aria-label="`我的号码是 ${playerNumber(snapshot.self.id)} 号，查看玩家号码表`"
          @click="showPlayerNumbers = true"
        >
          <span class="self-number-value">
            {{ playerNumber(snapshot.self.id) }}号
          </span>
          <span class="self-number-copy">
            <small>我的号码</small>
            <span>查看号码表</span>
          </span>
          <ChevronRight :size="14" aria-hidden="true" />
        </button>
      </template>
      <template #actions>
        <RoomRecordActions
          :account-id="snapshot.self.accountId"
          :game-key="snapshot.gameKey"
          :game-name="snapshot.gameName"
          :game-mode="roomStatsMode"
          :guest="snapshot.self.isGuest"
        />
        <button
          type="button"
          class="header-action"
          aria-label="打开设置"
          @click="emit('settings')"
        >
          <Settings2 :size="20" />
        </button>
        <button
          v-if="snapshot.phase === 'lobby' && !isSolo"
          type="button"
          class="header-action"
          aria-label="显示加入二维码"
          @click="showQr = true"
        >
          <QrCode :size="21" />
        </button>
        <button
          v-if="avalonSnapshot?.self.role && avalonSnapshot.phase !== 'game_over'"
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
          @click="showAvalonRules = true"
        >
          <CircleHelp :size="21" />
        </button>
        <RoomDissolveButton
          v-if="snapshot.actions.canDissolve"
          :busy="arcade.busy"
          @confirm="arcade.dissolveRoom"
        />
        <RoomExitButton
          :busy="arcade.busy"
          :description="exitDescription"
          @confirm="arcade.leaveRoom"
        />
      </template>
    </RoomPageHeader>

    <HostTransferNotice :transfer-at="snapshot.hostTransferAt" />

    <section
      v-if="snapshot.statsEligible === false || (snapshot.phase === 'lobby' && snapshot.options.allowGuests)"
      class="surface guest-match-notice"
      role="status"
    >
      <strong>{{ snapshot.statsEligible !== false ? '本房间允许游客加入' : '休闲局 · 本局不计战绩' }}</strong>
      <span>{{ snapshot.statsEligible !== false ? '目前尚无游客；若游客加入并参与开局，整局不会计入任何玩家战绩。' : '本局阵容包含游客，所有玩家的场次、胜负、历史和排行榜成绩均不会记录。' }}</span>
    </section>

    <section
      v-if="!isSolo"
      class="surface arcade-player-strip"
      :data-player-columns="playerStripColumns"
      :style="playerStripStyle"
      aria-label="房间玩家"
    >
      <article
        v-for="player in snapshot.players"
        :key="player.id"
        :class="{ self: player.id === snapshot.self.id }"
      >
        <span class="arcade-player-avatar">
          <img
            v-if="player.avatarUrl"
            :src="player.avatarUrl"
            alt=""
            draggable="false"
          />
          <template v-else>{{ player.seat + 1 }}</template>
        </span>
        <div>
          <strong>{{ player.name }}</strong>
          <small>
            <Crown v-if="player.isHost" :size="13" />
            {{ player.isHost ? '房主' : '玩家' }}{{ player.isGuest ? ' · 游客' : '' }}
            {{ player.connected
              ? '· 在线'
              : player.disconnectForfeited
                ? '· 掉线弃权'
                : player.disconnectForfeitAt
                  ? '· 离线，10 分钟后弃权'
                  : '· 离线' }}
          </small>
        </div>
        <RoomKickButton
          v-if="snapshot.actions.canKickPlayers && player.id !== snapshot.self.id"
          :player-name="player.name"
          :busy="arcade.busy"
          @confirm="arcade.kickPlayer(player.id)"
        />
      </article>
    </section>

    <section v-if="!isSolo" class="surface room-rule-bar" aria-label="房间规则">
      <div>
        <Settings2 :size="18" />
        <span v-for="label in gameRuleLabels(snapshot.gameKey, snapshot.options)" :key="label">{{ label }}</span>
        <span>掉线保护 10 分钟</span>
      </div>
      <div class="room-rule-actions">
        <button
          v-if="avalonSnapshot?.actions.canAddAiPlayer"
          type="button"
          :disabled="arcade.busy"
          @click="arcade.action('add_ai')"
        >
          <Bot :size="16" /> 添加 AI
        </button>
        <button v-if="snapshot.actions.canEditRules" type="button" @click="openRuleEditor">{{ snapshot.phase === 'finished' ? '修改下局规则' : '修改规则' }}</button>
      </div>
    </section>

    <GameSkinPicker
      v-if="snapshot.phase === 'lobby' && activeGameSkinKind"
      :model-value="activeGameSkin"
      :kind="activeGameSkinKind"
      @update:model-value="selectGameSkin"
    />

    <ArtworkSkinPicker
      v-if="avalonSnapshot?.phase === 'lobby'"
      :model-value="selectedRoleSkin"
      :options="roleArtworkOptions"
      title="我的身份卡画风"
      description="仅影响你看到的身份卡 · 开局后锁定"
      item-name="身份"
      @update:model-value="selectRoleSkin"
    />

    <section v-if="snapshot.phase === 'lobby'" class="surface arcade-waiting">
      <UsersRound :size="48" />
      <h2>等待玩家到齐</h2>
      <p v-if="missingPlayers > 0">还需要 {{ missingPlayers }} 名玩家</p>
      <p v-else-if="availableSeats > 0">已可开始，还可加入 {{ availableSeats }} 名玩家</p>
      <p v-else>人员已到齐，房主可以开始</p>
      <button v-if="!isSolo" type="button" class="room-code-share" aria-label="显示加入二维码" @click="showQr = true">
        {{ snapshot.roomCode }}
      </button>
      <InviteLinkPanel
        v-if="!isSolo"
        :url="inviteUrl"
        :share-title="`加入${snapshot.gameName}房间 ${snapshot.roomCode}`"
        :share-text="`点击链接加入我的${snapshot.gameName}房间 ${snapshot.roomCode}`"
      />
      <button
        v-if="snapshot.actions.canStart"
        type="button"
        class="primary-button"
        @click="arcade.startGame"
      >
        开始{{ snapshot.gameName }}
      </button>
    </section>

    <section v-else class="arcade-game-stage">
      <div v-if="snapshot.phase === 'finished' && !isSolo && !avalonSnapshot" class="surface result-banner">
        <small>本局结束</small>
        <h2>{{ snapshot.winReason }}</h2>
        <p>
          {{ snapshot.winnerPlayerIds.includes(snapshot.self.id) ? '你赢了' : '再接再厉' }}
          · 战绩已保存
        </p>
        <p class="rematch-progress">
          {{ snapshot.rematchReadyPlayerIds.length }} / {{ snapshot.players.length }} 人已准备
        </p>
        <button
          v-if="snapshot.actions.canRestart || selfRematchReady"
          type="button"
          class="primary-button"
          :disabled="selfRematchReady"
          @click="arcade.restartGame"
        >
          <RotateCcw :size="18" />
          {{ selfRematchReady ? '等待其他玩家' : '准备再来一局' }}
        </button>
      </div>

      <section
        v-if="snapshot.phase === 'playing' && (snapshot.actions.canRequestUndo || snapshot.actions.canRequestDraw || snapshot.request)"
        class="surface match-request-panel"
      >
        <template v-if="snapshot.request">
          <div>
            <strong>{{ snapshot.request.requesterName }}</strong>
            <span>申请{{ snapshot.request.kind === 'undo' ? '悔棋' : '和棋' }}</span>
          </div>
          <div v-if="snapshot.request.isMine" class="request-response-actions request-waiting-actions">
            <p>等待其他玩家确认</p>
            <button type="button" @click="arcade.resolveGameRequest(false)">撤回申请</button>
          </div>
          <div v-else class="request-response-actions">
            <button type="button" @click="arcade.resolveGameRequest(false)">拒绝</button>
            <button type="button" class="accept" @click="arcade.resolveGameRequest(true)">同意</button>
          </div>
        </template>
        <template v-else>
          <span>对局协商</span>
          <div>
            <button
              v-if="snapshot.actions.canRequestUndo"
              type="button"
              @click="arcade.requestGameAction('undo')"
            >
              <Undo2 :size="16" />申请悔棋
            </button>
            <button
              v-if="snapshot.actions.canRequestDraw"
              type="button"
              @click="arcade.requestGameAction('draw')"
            >
              <Handshake :size="16" />申请和棋
            </button>
          </div>
        </template>
      </section>

      <GomokuBoard v-if="snapshot.gameKey === 'gomoku'" :snapshot="snapshot" />
      <XiangqiBoard v-else-if="snapshot.gameKey === 'xiangqi'" :snapshot="snapshot" />
      <GoBoard v-else-if="snapshot.gameKey === 'go'" :snapshot="snapshot" />
      <PokerTable v-else-if="snapshot.gameKey === 'poker'" :snapshot="snapshot" />
      <DoudizhuTable v-else-if="snapshot.gameKey === 'doudizhu'" :snapshot="snapshot" />
      <JunqiBoard v-else-if="snapshot.gameKey === 'junqi'" :snapshot="snapshot" />
      <ReactionTest v-else-if="snapshot.gameKey === 'reaction'" :snapshot="snapshot" />
      <SchulteGrid v-else-if="snapshot.gameKey === 'schulte'" :snapshot="snapshot" />
      <MinesweeperBoard v-else-if="snapshot.gameKey === 'minesweeper'" :snapshot="snapshot" />
      <HanoiGame v-else-if="snapshot.gameKey === 'hanoi'" :snapshot="snapshot" />
      <AvalonTable
        v-else-if="avalonSnapshot"
        :snapshot="avalonSnapshot"
        :role-skin="activeRoleSkin"
        @open-chat="openSharedChat"
      />
    </section>

    <ArcadeChatPanel
      v-if="!isSolo"
      ref="sharedChat"
      :messages="snapshot.chat.messages"
      :max-length="snapshot.chat.maxLength"
      :self-id="snapshot.self.id"
      :busy="arcade.busy"
      :send="arcade.sendChat"
    />

    <RoomInviteModal
      v-if="showQr && snapshot.phase === 'lobby' && !isSolo"
      :url="inviteUrl"
      :room-code="snapshot.roomCode"
      :title="`扫描加入${snapshot.gameName}房间`"
      @close="showQr = false"
    />

    <div v-if="ruleEditor" class="modal-backdrop" @click.self="ruleEditor = null">
      <section class="modal-card rule-editor-modal" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭规则设置" @click="ruleEditor = null">
          <X :size="20" />
        </button>
        <span class="modal-icon"><Settings2 :size="25" /></span>
        <h2>房间规则</h2>
        <p>{{ snapshot.phase === 'finished' ? '保存后所有玩家会返回等待阶段，新规则从下一局生效。' : '保存后会同步给房间中的所有玩家，开局后不可修改。' }}</p>
        <GameRuleSettings v-model="ruleEditor" :game-key="snapshot.gameKey" :guest-mode="snapshot.self.isGuest" />
        <button type="button" class="primary-button wide-button" :disabled="arcade.busy" @click="saveRules">保存规则</button>
      </section>
    </div>

    <div v-if="showPlayerNumbers && avalonSnapshot" class="modal-backdrop" @click.self="showPlayerNumbers = false">
      <section class="modal-card player-number-modal" role="dialog" aria-modal="true" aria-label="玩家号码表">
        <button class="modal-close" type="button" aria-label="关闭玩家号码表" @click="showPlayerNumbers = false">
          <X :size="20" />
        </button>
        <span class="modal-icon"><UsersRound :size="25" /></span>
        <h2>玩家号码表</h2>
        <p>本局号码保持不变</p>
        <div class="player-number-list">
          <div
            v-for="player in snapshot.players"
            :key="player.id"
            :class="{ self: player.id === snapshot.self.id }"
          >
            <span>{{ player.seat + 1 }}</span>
            <strong>{{ player.name }}</strong>
            <small v-if="player.isBot">AI</small>
            <small v-if="player.id === snapshot.self.id">你</small>
          </div>
        </div>
      </section>
    </div>

    <div v-if="showIdentity && avalonSnapshot?.self.role" class="modal-backdrop" @click.self="showIdentity = false">
      <section class="modal-card identity-modal" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭身份" @click="showIdentity = false">
          <X :size="20" />
        </button>
        <PressRevealCard
          :title="avalonSnapshot.self.role.label"
          :subtitle="avalonSnapshot.self.role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营'"
          :artwork="selfRoleArtwork()"
          :artwork-label="roleSkinName(activeRoleSkin)"
          :artwork-framing="selfRoleArtworkFraming()"
          hint="按住重新查看身份"
        >
          <p class="secret-description">{{ avalonSnapshot.self.role.description }}</p>
          <div v-if="avalonSnapshot.self.role.knowledge.length" class="knowledge-list">
            <span v-for="item in avalonSnapshot.self.role.knowledge" :key="item.playerId">
              {{ avalonPlayerLabel(item.playerId) }} · {{ item.label }}
            </span>
          </div>
          <div v-if="avalonSnapshot.lady.myChecks.length" class="knowledge-list">
            <span v-for="check in avalonSnapshot.lady.myChecks" :key="`${check.missionNumber}-${check.targetId}`">
              仙女：{{ avalonPlayerLabel(check.targetId) }} · {{ check.alignment === 'good' ? '好人阵营' : '坏人阵营' }}
            </span>
          </div>
        </PressRevealCard>
      </section>
    </div>

    <div v-if="showAvalonRules && avalonSnapshot" class="modal-backdrop" @click.self="showAvalonRules = false">
      <section class="modal-card rules-modal" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭玩法说明" @click="showAvalonRules = false">
          <X :size="20" />
        </button>
        <span class="modal-icon"><CircleHelp :size="25" /></span>
        <h2>{{ avalonSnapshot.settings.mode === 'court_undercurrent' ? '王庭暗流 · 玩法说明' : '标准阿瓦隆 · 玩法说明' }}</h2>
        <p>{{ avalonSnapshot.settings.mode === 'court_undercurrent' ? '背景故事、特殊角色与终局规则集中在这里。' : '本局采用标准阿瓦隆规则。' }}</p>
        <ModeGuide
          v-if="avalonSnapshot.settings.mode === 'court_undercurrent'"
          :content="AVALON_COURT_GUIDE"
        />
        <section class="avalon-core-rules">
          <h3>圆桌通用规则</h3>
          <ul>
            <li>好人只能提交任务成功，坏人可选择成功或失败。</li>
            <li>队伍表决需要过半赞成，平票视为否决。</li>
            <li>连续五次组队被否决，坏人直接获胜。</li>
            <li>部分玩家掉线超过 10 分钟，其所属阵营弃权；全员离线只进入房间清理流程。</li>
            <li v-if="snapshot.players.length >= 7">第四次任务需要两张失败票才会失败。</li>
            <li v-if="avalonSnapshot.settings.ladyEnabled">仙女只查阵营，持有者可以谎报查验结果。</li>
          </ul>
        </section>
      </section>
    </div>
  </main>
</template>

<style scoped>
.arcade-room { padding-bottom: 70px; }
.guest-match-notice { margin: 0 0 18px; padding: 12px 15px; border-color: color-mix(in srgb, var(--gold) 35%, var(--line)); background: color-mix(in srgb, var(--gold) 7%, var(--surface)); }
.guest-match-notice strong,.guest-match-notice span { display: block; }.guest-match-notice strong { color: var(--gold); font-size: 13px; }.guest-match-notice span { margin-top: 4px; color: var(--muted); font-size: 11px; line-height: 1.55; }
.arcade-player-strip { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 24px; padding: 14px; }
.arcade-player-strip article { display: flex; flex: 0 0 var(--player-card-width); gap: 10px; align-items: center; min-width: 0; min-height: 68px; padding: 10px; border: 1px solid color-mix(in srgb, var(--line) 72%, transparent); border-radius: 12px; background: color-mix(in srgb, var(--surface-elevated) 42%, transparent); }
.arcade-player-strip article > div { min-width: 0; flex: 1; }
.arcade-player-strip article.self { border-color: color-mix(in srgb, var(--gold) 40%, transparent); background: color-mix(in srgb, var(--gold) 7%, transparent); }
.arcade-player-strip article > span { width: 34px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 10px; color: var(--gold); background: color-mix(in srgb, var(--gold) 13%, transparent); font-weight: 900; }
.arcade-player-avatar { overflow: hidden; }
.arcade-player-avatar img { width: 100%; height: 100%; object-fit: cover; }
.arcade-player-strip strong, .arcade-player-strip small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.arcade-player-strip small { margin-top: 2px; color: var(--muted); }
.arcade-player-strip small svg { vertical-align: -2px; color: var(--gold); }
.room-rule-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: -12px 0 24px; padding: 11px 13px; }
.room-rule-bar > div { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; min-width: 0; }
.room-rule-bar svg { flex: 0 0 auto; color: var(--gold); }
.room-rule-bar span { border: 1px solid var(--line); border-radius: 999px; padding: 4px 8px; color: var(--muted); background: rgba(0, 0, 0, .1); font-size: 10px; }
.room-rule-actions { flex: 0 0 auto; display: flex; gap: 8px; }
.room-rule-actions button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 36px; border: 1px solid color-mix(in srgb, var(--gold) 38%, var(--line)); border-radius: 10px; padding: 0 11px; color: var(--gold); background: color-mix(in srgb, var(--gold) 7%, transparent); font-weight: 850; }
.game-skin-card + .arcade-waiting,
.artwork-skin-picker + .arcade-waiting { margin-top: 18px; }
.arcade-waiting { min-height: 390px; display: grid; place-items: center; align-content: center; gap: 12px; text-align: center; }
.arcade-waiting > svg { color: var(--gold); }
.arcade-waiting h2, .arcade-waiting p { margin: 0; }
.arcade-waiting p { color: var(--muted); }
.room-code-share { margin: 14px 0 0; border: 0; padding: 0; color: var(--text); background: transparent; font-size: 28px; font-weight: 800; letter-spacing: .18em; }
.arcade-waiting :deep(.invite-link-panel) { width: min(100%, 620px); }
.arcade-game-stage { display: grid; gap: 22px; }
.result-banner { padding: 18px; text-align: center; }
.result-banner small { color: var(--gold); }
.result-banner h2 { margin: 5px 0; }
.result-banner p { color: var(--muted); }
.result-banner .rematch-progress { margin-bottom: 0; font-size: 11px; }
.result-banner .primary-button { margin: 12px auto 0; }
.match-request-panel { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 15px; }
.match-request-panel > span { color: var(--muted); font-weight: 800; }
.match-request-panel > div { display: flex; align-items: center; gap: 8px; }
.match-request-panel > div:first-child { display: grid; gap: 2px; }
.match-request-panel > div:first-child span { color: var(--muted); }
.match-request-panel p { margin: 0; color: var(--gold); }
.match-request-panel button { display: inline-flex; align-items: center; gap: 6px; min-height: 38px; border: 1px solid var(--line); border-radius: 10px; padding: 0 11px; color: var(--text); background: transparent; font-weight: 800; }
.request-waiting-actions { justify-content: flex-end; }
.request-response-actions button.accept { border-color: color-mix(in srgb, var(--gold) 38%, var(--line)); color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, transparent); }
.rule-editor-modal { width: min(94vw, 620px); max-height: min(88vh, 820px); overflow-y: auto; }
.rule-editor-modal > p { margin: -4px 0 20px; color: var(--muted); }
.rule-editor-modal > .wide-button { margin-top: 22px; }
@media (max-width: 860px) {
  .arcade-player-strip article { flex-basis: calc(33.333333% - 6.667px); }
}
@media (max-width: 620px) {
  .arcade-player-strip article { flex-basis: calc(50% - 5px); }
  .match-request-panel { align-items: stretch; flex-direction: column; }
  .match-request-panel > div { display: grid; grid-template-columns: 1fr 1fr; }
  .match-request-panel button { justify-content: center; }
  .room-rule-bar { align-items: stretch; flex-direction: column; }
  .room-rule-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); }
  .room-rule-actions button { width: 100%; }
}
@media (max-width: 430px) {
  .arcade-player-strip article { flex-basis: 100%; }
}
@media (min-width: 860px) {
  .arcade-room.arcade-room--wide { width: min(100%, 1080px); }
}
</style>
