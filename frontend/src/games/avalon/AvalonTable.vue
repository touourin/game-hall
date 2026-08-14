<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  ArrowRight,
  Check,
  ChevronRight,
  Crown,
  Eye,
  History,
  MessageCircle,
  RotateCcw,
  Shield,
  Sparkles,
  Swords,
  UsersRound,
  X,
} from '@lucide/vue'
import MissionProgressTrack from '../../components/MissionProgressTrack.vue'
import PressRevealCard from '../../components/PressRevealCard.vue'
import AvatarImage from '../../components/AvatarImage.vue'
import UiButton from '../../components/ui/UiButton.vue'
import UiIconButton from '../../components/ui/UiIconButton.vue'
import {
  roleArtwork,
  roleArtworkFraming,
  roleSkinName,
  type RoleSkinId,
} from './roleSkins'
import { useArcadeStore } from '../../stores/arcade'
import type { MissionProgressItem } from '../../components/uiTypes'
import type { PlayerView, RoomSnapshot } from './types'

const props = withDefaults(defineProps<{
  snapshot: RoomSnapshot
  roleSkin?: RoleSkinId
}>(), {
  roleSkin: 'classic-tabletop',
})
const emit = defineEmits<{ openChat: [] }>()
const room = useArcadeStore()

const selectedTeamIds = ref<string[]>([])
const ladyTargetId = ref<string | null>(null)
const assassinTargetId = ref<string | null>(null)
const daggerTargetId = ref<string | null>(null)
const dissentingTargetId = ref<string | null>(null)
const earlyAssassinTargetId = ref<string | null>(null)
const exileCouncilTargetId = ref<string | null>(null)
const councilAssassinateChoice = ref<boolean | null>(null)
const councilAssassinationTargetId = ref<string | null>(null)
const roleSeen = ref(false)
const ladySeen = ref(false)
const showReplay = ref(false)
const showLadyHistory = ref(false)
const showEarlyAssassination = ref(false)
const selectedReplayMission = ref<number | null>(null)

const leader = computed(() =>
  props.snapshot.players.find(
    (player) => player.id === props.snapshot.game.leaderId,
  ),
)
const ladyHolder = computed(() =>
  props.snapshot.players.find(
    (player) => player.id === props.snapshot.lady.holderId,
  ),
)
const showLadyReminder = computed(
  () =>
    props.snapshot.lady.enabled &&
    Boolean(props.snapshot.lady.holderId) &&
    ['team_building', 'team_voting', 'mission_voting'].includes(
      props.snapshot.phase,
    ),
)
const ladyReminderTiming = computed(() => {
  const missionNumber = props.snapshot.game.missionNumber
  if (missionNumber === 1) {
    return '第 2 次任务结束后首次查验'
  }
  if (missionNumber <= 4) {
    return '本次任务结束后负责查验'
  }
  return '本局仙女查验已经结束'
})
const selectedPlayers = computed(() =>
  props.snapshot.players.filter((player) =>
    props.snapshot.game.selectedTeamIds.includes(player.id),
  ),
)
const latestMission = computed(
  () => props.snapshot.game.missionHistory.at(-1) ?? null,
)
const assassinPlayer = computed(() =>
  props.snapshot.players.find((player) => player.role === 'assassin'),
)
const assassinTarget = computed(() =>
  props.snapshot.players.find(
    (player) => player.id === props.snapshot.result.assassinTargetId,
  ),
)
const assassinationHit = computed(
  () => assassinTarget.value?.role === 'merlin',
)
const assassinationCandidates = computed(() => {
  const eligibleTargetIds = new Set(
    props.snapshot.result.eligibleTargetIds,
  )
  return props.snapshot.players.filter((player) =>
    eligibleTargetIds.has(player.id),
  )
})
const daggerTarget = computed(() =>
  props.snapshot.players.find(
    (player) => player.id === props.snapshot.courtUndercurrent.daggerTargetId,
  ),
)
const dissentingAssassinationTarget = computed(() =>
  props.snapshot.players.find(
    (player) =>
      player.id === props.snapshot.courtUndercurrent.assassinationTargetId,
  ),
)
const dissentingAssassinationHit = computed(
  () => dissentingAssassinationTarget.value?.role === 'merlin',
)
const replayMissionNumbers = computed(() => [
  ...new Set(
    props.snapshot.game.proposalHistory.map(
      (proposal) => proposal.missionNumber,
    ),
  ),
])
const replayProposals = computed(() =>
  selectedReplayMission.value === null
    ? props.snapshot.game.proposalHistory
    : props.snapshot.game.proposalHistory.filter(
        (proposal) =>
          proposal.missionNumber === selectedReplayMission.value,
      ),
)
const missionTeamSizes: Record<number, readonly number[]> = {
  5: [2, 3, 2, 3, 3],
  6: [2, 3, 4, 3, 4],
  7: [2, 3, 3, 4, 4],
  8: [3, 4, 4, 5, 5],
  9: [3, 4, 4, 5, 5],
  10: [3, 4, 4, 5, 5],
}

const missionProgressItems = computed<MissionProgressItem[]>(() =>
  [1, 2, 3, 4, 5].map((number) => {
    const record = props.snapshot.game.missionHistory.find(
      (mission) => mission.number === number,
    )
    const requirement =
      missionTeamSizes[props.snapshot.players.length]?.[number - 1] ?? 0
    const replayable = replayMissionNumbers.value.includes(number)
    const status: MissionProgressItem['status'] = record
      ? record.success
        ? 'success'
        : 'failed'
      : number === props.snapshot.game.missionNumber
        ? 'current'
        : 'pending'
    const outcome = record
      ? record.success
        ? '，任务成功'
        : '，任务失败'
      : ''
    return {
      number,
      requirement,
      status,
      replayable,
      note:
        props.snapshot.players.length >= 7 && number === 4
          ? '双败'
          : undefined,
      label: `第 ${number} 轮，需要 ${requirement} 人${outcome}${
        replayable ? '，点击查看本轮投票复盘' : ''
      }`,
    }
  }),
)

watch(
  () => props.snapshot.phase,
  (phase) => {
    selectedTeamIds.value = []
    ladyTargetId.value = null
    assassinTargetId.value = null
    daggerTargetId.value = null
    dissentingTargetId.value = null
    earlyAssassinTargetId.value = null
    exileCouncilTargetId.value = null
    councilAssassinateChoice.value = null
    councilAssassinationTargetId.value = null
    ladySeen.value = false
    if (phase === 'role_reveal') {
      roleSeen.value = false
    }
    if (phase === 'game_over') {
      showEarlyAssassination.value = false
    }
  },
)
function playerName(playerId: string | null): string {
  const player = props.snapshot.players.find((item) => item.id === playerId)
  return player ? playerDisplayName(player) : '未知玩家'
}

function playerDisplayName(player: PlayerView): string {
  return player.isBot ? `${player.name} · AI` : player.name
}

function playerNumber(playerId: string | null): number | null {
  const player = props.snapshot.players.find((item) => item.id === playerId)
  return player ? player.seat + 1 : null
}

function playerAvatar(playerId: string | null): string | null {
  return props.snapshot.players.find((item) => item.id === playerId)
    ?.avatarUrl ?? null
}

function playerLabel(playerId: string | null): string {
  const number = playerNumber(playerId)
  const name = playerName(playerId)
  return number ? `${number}号 ${name}` : name
}

function playerLabels(playerIds: string[]): string {
  return playerIds.map((playerId) => playerLabel(playerId)).join('、')
}

function toggleTeamPlayer(playerId: string) {
  const current = selectedTeamIds.value
  if (current.includes(playerId)) {
    selectedTeamIds.value = current.filter((id) => id !== playerId)
    return
  }
  const required = props.snapshot.game.requiredTeamSize ?? 0
  if (current.length < required) {
    selectedTeamIds.value = [...current, playerId]
  }
}

function playerClasses(player: PlayerView) {
  return {
    selected: selectedTeamIds.value.includes(player.id),
    offline: !player.connected,
    leader: player.isLeader,
  }
}

function openReplay(missionNumber: number | null = null) {
  selectedReplayMission.value = missionNumber
  showReplay.value = true
}

function missionOutcome(missionNumber: number) {
  return props.snapshot.game.missionHistory.find(
    (mission) => mission.number === missionNumber,
  )
}

function myLadyCheck(missionNumber: number, targetId: string) {
  return props.snapshot.lady.myChecks.find(
    (check) =>
      check.missionNumber === missionNumber && check.targetId === targetId,
  )
}

function revealedAlignment(playerId: string) {
  return props.snapshot.players.find((player) => player.id === playerId)
    ?.alignment
}

async function proposeTeam() {
  await room.action('propose_team', {
    team_ids: selectedTeamIds.value,
  })
}

async function inspectWithLady() {
  if (!ladyTargetId.value) return
  await room.action('lady_inspect', {
    target_id: ladyTargetId.value,
  })
}

async function assassinate() {
  if (!assassinTargetId.value) return
  await room.action('assassinate', {
    target_id: assassinTargetId.value,
  })
}

async function grantDagger() {
  if (!daggerTargetId.value) return
  await room.action('grant_dagger', {
    target_id: daggerTargetId.value,
  })
}

async function dissentingAssassinate() {
  if (!dissentingTargetId.value) return
  await room.action('dissenting_assassinate', {
    target_id: dissentingTargetId.value,
  })
}

async function earlyAssassinate() {
  if (!earlyAssassinTargetId.value) return
  const response = await room.actionWithResult('early_assassinate', {
    target_id: earlyAssassinTargetId.value,
  })
  if (response) showEarlyAssassination.value = false
}

async function submitExileCouncilBallot() {
  if (!exileCouncilTargetId.value) return
  await room.action('exile_council_ballot', {
    open_council: true,
    target_id: exileCouncilTargetId.value,
  })
}

async function submitCouncilAssassinationDecision() {
  if (councilAssassinateChoice.value === null) return
  await room.action('council_assassination_decision', {
    assassinate: councilAssassinateChoice.value,
  })
}

async function submitCouncilAssassinationTarget() {
  if (!councilAssassinationTargetId.value) return
  await room.action('council_assassination_target', {
    target_id: councilAssassinationTargetId.value,
  })
}

function openSharedChat() {
  emit('openChat')
}

function selfRoleArtwork(): string | null {
  const roleCode = props.snapshot.self.role?.code
  return roleCode ? roleArtwork(roleCode, props.roleSkin) : null
}

function selfRoleArtworkFraming() {
  return roleArtworkFraming(
    props.snapshot.self.role?.code ?? '',
    props.roleSkin,
  )
}
</script>

<template>
  <div class="avalon-table">
    <MissionProgressTrack
      v-if="snapshot.phase !== 'lobby' && snapshot.phase !== 'role_reveal'"
      :items="missionProgressItems"
      @select="openReplay"
    />
    <p
      v-if="snapshot.game.proposalHistory.length"
      class="mission-replay-hint"
    >
      <History :size="14" />
      点击有记录的任务圈查看该轮复盘
    </p>
    <div
      v-if="
        snapshot.lady.history.length ||
        snapshot.actions.canEarlyAssassinate
      "
      class="game-toolbar"
    >
      <button
        v-if="snapshot.actions.canEarlyAssassinate"
        class="danger-tool"
        type="button"
        @click="showEarlyAssassination = true"
      >
        <Swords :size="17" />
        提前刺杀
      </button>
      <button
        v-if="snapshot.lady.history.length"
        type="button"
        @click="showLadyHistory = true"
      >
        <Sparkles :size="17" />
        仙女记录
        <span>{{ snapshot.lady.history.length }}</span>
      </button>
    </div>

    <div
      v-if="showLadyReminder"
      class="surface mission-lady-reminder"
      aria-label="湖中仙女当前持有者"
    >
      <span class="mission-lady-icon"><Sparkles :size="20" /></span>
      <div>
        <small>湖中仙女当前持有者</small>
        <strong>{{ playerLabel(ladyHolder?.id ?? null) }}</strong>
      </div>
      <em>{{ ladyReminderTiming }}</em>
    </div>

    <section v-if="snapshot.phase === 'role_reveal'" class="phase-stack">
      <div class="phase-intro">
        <span class="phase-icon"><Eye :size="22" /></span>
        <div>
          <h2>只让自己看到</h2>
          <p>确认周围没人偷看，再按住下方卡片。</p>
        </div>
      </div>

      <div
        v-if="snapshot.game.leaderId"
        class="surface first-leader-card"
        role="status"
      >
        <span class="first-leader-icon"><Crown :size="24" /></span>
        <div>
          <small>本局首任队长</small>
          <strong>{{ playerLabel(snapshot.game.leaderId) }}</strong>
          <p>身份确认结束后，由这位玩家首先组建任务队伍</p>
        </div>
        <em>首先带队</em>
      </div>

      <div
        v-if="snapshot.settings.ladyEnabled && snapshot.lady.holderId"
        class="surface initial-lady-card"
        role="status"
      >
        <span class="initial-lady-icon"><Sparkles :size="24" /></span>
        <div>
          <small>湖中仙女初始持有者</small>
          <strong>{{ playerLabel(snapshot.lady.holderId) }}</strong>
          <p>第 2 次任务结束后，由这位玩家首先秘密查验阵营</p>
        </div>
        <em>持有仙女</em>
      </div>

      <div class="surface player-number-roster">
        <header>
          <UsersRound :size="19" />
          <div>
            <strong>玩家号码表</strong>
            <small>本局所有讨论和投票都使用以下号码</small>
          </div>
        </header>
        <div>
          <span
            v-for="player in snapshot.players"
            :key="player.id"
            :class="{
              self: player.id === snapshot.self.id,
              leader: player.id === snapshot.game.leaderId,
            }"
          >
            <b>{{ player.seat + 1 }}号</b>
            <strong>{{ playerDisplayName(player) }}</strong>
            <span class="player-number-badges">
              <em v-if="player.id === snapshot.self.id">你</em>
              <em
                v-if="player.id === snapshot.game.leaderId"
                class="leader-badge"
              >
                <Crown :size="10" /> 队长
              </em>
              <em
                v-if="
                  snapshot.settings.ladyEnabled &&
                  player.id === snapshot.lady.holderId
                "
                class="lady-holder-badge"
              >
                <Sparkles :size="10" /> 仙女
              </em>
            </span>
          </span>
        </div>
      </div>

      <PressRevealCard
        v-if="snapshot.self.role"
        :title="snapshot.self.role.label"
        :subtitle="snapshot.self.role.alignment === 'good' ? '亚瑟阵营' : '莫德雷德阵营'"
        :artwork="selfRoleArtwork()"
        :artwork-label="roleSkinName(roleSkin)"
        :artwork-framing="selfRoleArtworkFraming()"
        @seen="roleSeen = true"
      >
        <p class="secret-description">{{ snapshot.self.role.description }}</p>
        <div v-if="snapshot.self.role.knowledge.length" class="knowledge-list">
          <span
            v-for="item in snapshot.self.role.knowledge"
            :key="item.playerId"
          >
            {{ playerLabel(item.playerId) }} · {{ item.label }}
          </span>
        </div>
        <p v-else class="muted-secret">你没有额外可见信息</p>
      </PressRevealCard>

      <UiButton
        v-if="snapshot.actions.canConfirmRole"
        variant="primary"
        block
        :disabled="!roleSeen"
        @click="room.action('confirm_role')"
      >
        <Check :size="19" /> 我已记住身份
      </UiButton>
      <div v-else class="waiting-card">
        <span class="pulse-dot" />
        已确认，等待其他玩家
      </div>
      <p class="center-note">
        已确认 {{ snapshot.game.roleConfirmedCount }} / {{ snapshot.players.length }}
      </p>
    </section>

    <section v-else-if="snapshot.phase === 'team_building'" class="phase-stack">
      <div class="phase-intro">
        <span class="phase-icon"><UsersRound :size="22" /></span>
        <div>
          <h2>第 {{ snapshot.game.missionNumber }} 次任务</h2>
          <p>
            队长 {{ playerLabel(leader?.id ?? null) }} 需要选择
            {{ snapshot.game.requiredTeamSize }} 名成员
          </p>
        </div>
        <span class="attempt-badge">第 {{ snapshot.game.proposalAttempt }} 次组队</span>
      </div>

      <div
        v-if="snapshot.game.lastTeamVotes.length"
        class="surface previous-votes"
      >
        <span>上一轮表决</span>
        <div>
          <span
            v-for="vote in snapshot.game.lastTeamVotes"
            :key="vote.playerId"
            :class="vote.approve ? 'vote-yes' : 'vote-no'"
          >
            {{ playerLabel(vote.playerId) }} {{ vote.approve ? '赞成' : '反对' }}
          </span>
        </div>
      </div>

      <template v-if="snapshot.actions.canProposeTeam">
        <div class="selection-counter">
          <span>选择任务成员</span>
          <strong>{{ selectedTeamIds.length }} / {{ snapshot.game.requiredTeamSize }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in snapshot.players"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="playerClasses(player)"
            @click="toggleTeamPlayer(player.id)"
          >
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
            <span
              v-if="player.isLeader || player.id === snapshot.lady.holderId"
              class="player-tile-badges"
            >
              <small v-if="player.isLeader" class="leader-chip">
                <Crown :size="10" /> 队长
              </small>
              <small
                v-if="player.id === snapshot.lady.holderId"
                class="lady-chip"
              >
                <Sparkles :size="10" /> 仙女
              </small>
            </span>
            <Check v-if="selectedTeamIds.includes(player.id)" :size="18" />
          </button>
        </div>
        <UiButton
          variant="primary"
          block
          :disabled="selectedTeamIds.length !== snapshot.game.requiredTeamSize"
          @click="proposeTeam"
        >
          提交任务队伍 <ChevronRight :size="19" />
        </UiButton>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot" />
        <strong>{{ playerLabel(leader?.id ?? null) }} 正在选择队伍</strong>
        <small>可以面对面讨论并给队长建议</small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'team_voting'" class="phase-stack">
      <div class="phase-intro">
        <span class="phase-icon"><Shield :size="22" /></span>
        <div>
          <h2>这支队伍可信吗？</h2>
          <p>过半赞成才会进入任务，平票视为否决。</p>
        </div>
      </div>

      <div class="surface selected-team-card">
        <span>任务成员</span>
        <div class="selected-team">
          <div v-for="player in selectedPlayers" :key="player.id">
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
          </div>
        </div>
      </div>

      <div v-if="snapshot.actions.canVoteTeam" class="vote-actions">
        <button
          class="decision-button reject"
          type="button"
          @click="room.action('vote_team', { approve: false })"
        >
          <X :size="25" />
          <strong>反对</strong>
          <span>重新组队</span>
        </button>
        <button
          class="decision-button approve"
          type="button"
          @click="room.action('vote_team', { approve: true })"
        >
          <Check :size="25" />
          <strong>赞成</strong>
          <span>执行任务</span>
        </button>
      </div>
      <div v-else class="waiting-card">
        <span class="pulse-dot" />
        投票已锁定，等待其他玩家
      </div>
      <p class="center-note">
        已提交 {{ snapshot.game.teamVotesSubmitted }} / {{ snapshot.players.length }}
      </p>
    </section>

    <section v-else-if="snapshot.phase === 'mission_voting'" class="phase-stack">
      <div class="phase-intro">
        <span class="phase-icon"><Swords :size="22" /></span>
        <div>
          <h2>任务已经出发</h2>
          <p>
            <template v-if="snapshot.game.failThreshold === 2">本轮至少两张失败票才会失败。</template>
            <template v-else>只要出现一张失败票，任务就会失败。</template>
          </p>
        </div>
      </div>

      <div class="surface selected-team-card">
        <span>执行任务</span>
        <div class="selected-team">
          <div v-for="player in selectedPlayers" :key="player.id">
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
          </div>
        </div>
      </div>

      <template v-if="snapshot.actions.canVoteMission">
        <p class="private-warning"><Eye :size="16" /> 任务选择不会公开你的名字</p>
        <div class="mission-actions">
          <button
            class="mission-card success-card"
            type="button"
            @click="room.action('vote_mission', { success: true })"
          >
            <Check :size="28" />
            <strong>任务成功</strong>
            <span>守护亚瑟的荣光</span>
          </button>
          <button
            v-if="snapshot.actions.canMissionFail"
            class="mission-card fail-card"
            type="button"
            @click="room.action('vote_mission', { success: false })"
          >
            <X :size="28" />
            <strong>任务失败</strong>
            <span>暗中破坏这次行动</span>
          </button>
        </div>
        <p v-if="!snapshot.actions.canMissionFail" class="center-note">
          {{
            snapshot.self.role?.code === 'shadow_merlin'
              ? '暗影梅林不能提交任务失败'
              : '好人阵营只能提交任务成功'
          }}
        </p>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot" />
        <strong>
          {{ snapshot.game.myMissionVoteSubmitted ? '任务票已提交' : '等待任务成员秘密选择' }}
        </strong>
        <small>面对面保持讨论，但不要让别人看到你的屏幕</small>
      </div>
      <p class="center-note">
        已提交 {{ snapshot.game.missionVotesSubmitted }} /
        {{ snapshot.game.selectedTeamIds.length }}
      </p>
    </section>

    <section v-else-if="snapshot.phase === 'round_result'" class="phase-stack">
      <div
        v-if="latestMission"
        class="result-hero"
        :class="latestMission.success ? 'success' : 'failed'"
      >
        <span>
          <Check v-if="latestMission.success" :size="34" />
          <X v-else :size="34" />
        </span>
        <p>第 {{ latestMission.number }} 次任务</p>
        <h2>{{ latestMission.success ? '任务成功' : '任务失败' }}</h2>
        <strong>
          {{
            latestMission.failedByRejections
              ? '连续五次组队被否决，本次任务直接失败'
              : `出现 ${latestMission.failCount} 张失败票`
          }}
        </strong>
      </div>

      <div class="score-summary">
        <div>
          <span>亚瑟阵营</span>
          <strong>{{ snapshot.game.successCount }}</strong>
          <small>次成功</small>
        </div>
        <div>
          <span>莫德雷德阵营</span>
          <strong>{{ snapshot.game.failCount }}</strong>
          <small>次失败</small>
        </div>
      </div>

      <UiButton
        v-if="snapshot.actions.canContinueRound"
        variant="primary"
        block
        @click="room.action('continue_round')"
      >
        继续结算 <ArrowRight :size="19" />
      </UiButton>
      <div v-else class="waiting-card">
        <span class="pulse-dot" />
        等待房主继续
      </div>
    </section>

    <section
      v-else-if="snapshot.phase === 'exile_council_ballot'"
      class="phase-stack"
    >
      <div class="assassination-hero court-hero">
        <span><Crown :size="29" /></span>
        <p>邪恶已经取得两次任务失败</p>
        <h2>祓影议庭强制开启</h2>
        <strong>所有人秘密锁定祓影目标，选票提交后不能修改</strong>
      </div>

      <button class="surface final-council-chat" type="button" @click="openSharedChat">
        <MessageCircle :size="21" />
        <div>
          <strong>打开议庭讨论</strong>
          <small>提交内容不会在游戏进行中公开；选票一经提交不能修改</small>
        </div>
        <ChevronRight :size="18" />
      </button>

      <template v-if="snapshot.actions.canSubmitExileCouncilBallot">
        <div class="surface court-secret-note">
          <Eye :size="19" />
          <div>
            <strong>议庭已经开启，只需提交祓影票</strong>
            <small>只有忠臣、梅林、派西维尔和心怀异念之臣的票有效；系统不会提示你的票是否有效</small>
          </div>
        </div>

        <div class="selection-counter">
          <span>提交祓影票</span>
          <strong>{{ exileCouncilTargetId ? '目标锁定' : '未选择' }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in snapshot.players.filter((item) =>
              snapshot.shadowMerlin.eligibleExileTargetIds.includes(item.id),
            )"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: exileCouncilTargetId === player.id }"
            @click="exileCouncilTargetId = player.id"
          >
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
            <X v-if="exileCouncilTargetId === player.id" :size="18" />
          </button>
        </div>
        <UiButton
          variant="primary"
          block
          :disabled="!exileCouncilTargetId"
          @click="submitExileCouncilBallot"
        >
          匿名提交祓影票 <ChevronRight :size="19" />
        </UiButton>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot" />
        <strong>你的匿名选票已经锁定</strong>
        <small>等待全部玩家完成祓影选择</small>
      </div>
      <p class="center-note">
        已提交 {{ snapshot.shadowMerlin.ballotsSubmitted }} / {{ snapshot.players.length }}
      </p>
    </section>

    <section
      v-else-if="snapshot.phase === 'exile_council_assassination_decision'"
      class="phase-stack"
    >
      <div class="assassination-hero court-hero">
        <span><Swords :size="29" /></span>
        <p>累计第二次任务失败，议庭已经强制开启</p>
        <h2>祓影议庭正式开启</h2>
        <strong>刺客重新获得一次刺杀梅林的机会</strong>
      </div>

      <button class="surface final-council-chat" type="button" @click="openSharedChat">
        <MessageCircle :size="21" />
        <div>
          <strong>打开议庭讨论</strong>
          <small>所有人都可发言；此前锁定的祓影目标仍不可修改</small>
        </div>
        <ChevronRight :size="18" />
      </button>

      <template v-if="snapshot.actions.canSubmitExileCouncilAssassinationDecision">
        <div class="surface court-secret-note">
          <Eye :size="19" />
          <div>
            <strong v-if="snapshot.self.role?.code === 'assassin'">你是刺客，请决定是否发动刺杀</strong>
            <strong v-else>你并非刺客，只需确认放弃刺杀</strong>
            <small>只有刺客拥有发动刺杀的选项；其他玩家的确认不会改变结算路线</small>
          </div>
        </div>
        <div
          class="vote-actions"
          :class="{ 'single-action': snapshot.self.role?.code !== 'assassin' }"
        >
          <button
            class="decision-button reject"
            :class="{ selected: councilAssassinateChoice === false }"
            type="button"
            @click="councilAssassinateChoice = false"
          >
            <Shield :size="25" />
            <strong>放弃刺杀</strong>
            <span>结算已锁定的祓影票</span>
          </button>
          <button
            v-if="snapshot.self.role?.code === 'assassin'"
            class="decision-button approve"
            :class="{ selected: councilAssassinateChoice === true }"
            type="button"
            @click="councilAssassinateChoice = true"
          >
            <Swords :size="25" />
            <strong>发动刺杀</strong>
            <span>出刃，使祓影票作废并寻找梅林</span>
          </button>
        </div>
        <UiButton
          variant="danger"
          block
          :disabled="councilAssassinateChoice === null"
          @click="submitCouncilAssassinationDecision"
        >
          锁定选择
        </UiButton>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot danger-dot" />
        <strong>你的选择已经锁定</strong>
        <small>等待其他玩家完成确认</small>
      </div>
      <p class="center-note">
        已提交 {{ snapshot.shadowMerlin.assassinationDecisionsSubmitted }} /
        {{ snapshot.players.length }}
      </p>
    </section>

    <section
      v-else-if="snapshot.phase === 'exile_council_assassination_target'"
      class="phase-stack"
    >
      <div class="assassination-hero court-hero">
        <span><Swords :size="29" /></span>
        <p>刺客选择发动刺杀</p>
        <h2>寻找真正的梅林</h2>
        <strong>刺杀已经开始，暗影梅林立即转为好人阵营</strong>
      </div>

      <template v-if="snapshot.actions.canSubmitExileCouncilAssassinationTarget">
        <div class="surface court-secret-note transformed">
          <Eye :size="19" />
          <div>
            <strong>你是刺客，请选择刺杀目标</strong>
            <small>目标提交后立即结算，其他玩家不参与选择</small>
          </div>
        </div>
        <div class="selection-counter">
          <span>选择你认为的梅林</span>
          <strong>{{ councilAssassinationTargetId ? '目标锁定' : '谨慎选择' }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in snapshot.players.filter((item) =>
              snapshot.shadowMerlin.eligibleAssassinationTargetIds.includes(item.id),
            )"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: councilAssassinationTargetId === player.id }"
            @click="councilAssassinationTargetId = player.id"
          >
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
            <Swords v-if="councilAssassinationTargetId === player.id" :size="18" />
          </button>
        </div>
        <UiButton
          variant="danger"
          block
          :disabled="!councilAssassinationTargetId"
          @click="submitCouncilAssassinationTarget"
        >
          确认目标 {{ playerLabel(councilAssassinationTargetId) }}
        </UiButton>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot danger-dot" />
        <strong>刺客正在选择目标</strong>
        <small>你不需要进行任何操作</small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'lady_select'" class="phase-stack">
      <div class="phase-intro lady-intro">
        <span class="phase-icon"><Sparkles :size="22" /></span>
        <div>
          <h2>湖中仙女苏醒</h2>
          <p>
            当前持有者是 {{ playerLabel(snapshot.lady.holderId) }}，查验结果只对持有者可见。
          </p>
        </div>
      </div>

      <template v-if="snapshot.actions.canUseLady">
        <div class="selection-counter">
          <span>选择一名玩家查验阵营</span>
          <strong>{{ ladyTargetId ? '已选择' : '未选择' }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in snapshot.players.filter((item) =>
              snapshot.lady.eligibleTargetIds.includes(item.id),
            )"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: ladyTargetId === player.id }"
            @click="ladyTargetId = player.id"
          >
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
            <Sparkles v-if="ladyTargetId === player.id" :size="18" />
          </button>
        </div>
        <UiButton
          variant="primary"
          block
          :disabled="!ladyTargetId"
          @click="inspectWithLady"
        >
          秘密查验 <ChevronRight :size="19" />
        </UiButton>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot" />
        <strong>{{ playerLabel(snapshot.lady.holderId) }} 正在选择查验对象</strong>
        <small>持有者可以隐瞒或谎报最终看到的阵营</small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'lady_reveal'" class="phase-stack">
      <div class="phase-intro lady-intro">
        <span class="phase-icon"><Sparkles :size="22" /></span>
        <div>
          <h2>仙女的启示</h2>
          <p>
            {{ playerLabel(snapshot.lady.pendingInspectorId) }} 查验了
            {{ playerLabel(snapshot.lady.pendingTargetId) }}
          </p>
        </div>
      </div>

      <template v-if="snapshot.actions.canAcknowledgeLady && snapshot.lady.currentResult">
        <PressRevealCard
          :title="playerLabel(snapshot.lady.currentResult.targetId)"
          :subtitle="
            snapshot.lady.currentResult.alignment === 'good'
              ? '属于好人阵营'
              : '属于坏人阵营'
          "
          hint="按住查看查验结果"
          @seen="ladySeen = true"
        />
        <p class="center-note">你可以向大家说出真相，也可以撒谎。</p>
        <UiButton
          variant="primary"
          block
          :disabled="!ladySeen"
          @click="room.action('lady_acknowledge')"
        >
          我已记住结果 <Check :size="19" />
        </UiButton>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot" />
        <strong>等待查验者确认秘密结果</strong>
        <small>
          湖中仙女将传给 {{ playerLabel(snapshot.lady.pendingTargetId) }}
        </small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'assassination'" class="phase-stack">
      <div class="assassination-hero">
        <span><Swords :size="29" /></span>
        <p>好人已完成三次任务</p>
        <h2>刺客的最后机会</h2>
        <strong>找出梅林，邪恶阵营仍可翻盘</strong>
      </div>

      <div class="surface assassination-alignments">
        <header>
          <Eye :size="19" />
          <div>
            <strong>邪恶阵营公开</strong>
            <small
              v-if="snapshot.settings.rolePreset.some(
                (role) => role.code === 'oberon',
              )"
            >
              奥伯伦不会现身，仍与好人一起留在刺杀候选中
            </small>
            <small v-else>邪恶阵营已经现身，具体角色在刺杀后揭晓</small>
          </div>
        </header>
        <div>
          <span
            v-for="player in snapshot.players.filter(
              (item) => item.alignment === 'evil',
            )"
            :key="player.id"
            :class="player.alignment"
          >
            <b>{{ player.seat + 1 }}号</b>
            <strong>{{ playerDisplayName(player) }}</strong>
            <em>坏人</em>
          </span>
        </div>
      </div>

      <template v-if="snapshot.actions.canAssassinate">
        <div class="selection-counter">
          <span>选择你认为的梅林</span>
          <strong>{{ assassinTargetId ? '目标锁定' : '谨慎选择' }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in assassinationCandidates"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: assassinTargetId === player.id }"
            @click="assassinTargetId = player.id"
          >
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
            <Swords v-if="assassinTargetId === player.id" :size="18" />
          </button>
        </div>
        <UiButton
          variant="danger"
          block
          :disabled="!assassinTargetId"
          @click="assassinate"
        >
          确认刺杀 {{ playerLabel(assassinTargetId) }}
        </UiButton>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot danger-dot" />
        <strong>邪恶势力正在做最后判断</strong>
        <small>刺客确认前，所有玩家仍需隐藏身份</small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'dagger_grant'" class="phase-stack">
      <div class="assassination-hero court-hero">
        <span><Swords :size="29" /></span>
        <p>亚瑟一方已完成三次任务</p>
        <h2>刺客最后的授刃</h2>
        <strong>找出心怀异念之臣，将黑誓之刃交到他手中</strong>
      </div>

      <template v-if="snapshot.actions.canGrantDagger">
        <div class="surface court-secret-note">
          <Eye :size="19" />
          <div>
            <strong>以下名单仅你可见</strong>
            <small>其中一人是心怀异念之臣；选错则好人立即获胜</small>
          </div>
        </div>
        <div class="selection-counter">
          <span>选择授刃目标</span>
          <strong>{{ daggerTargetId ? '目标锁定' : '谨慎判断' }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in snapshot.players.filter((item) =>
              snapshot.courtUndercurrent.daggerCandidateIds.includes(item.id),
            )"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: daggerTargetId === player.id }"
            @click="daggerTargetId = player.id"
          >
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
            <Swords v-if="daggerTargetId === player.id" :size="18" />
          </button>
        </div>
        <UiButton
          variant="danger"
          block
          :disabled="!daggerTargetId"
          @click="grantDagger"
        >
          向 {{ playerLabel(daggerTargetId) }} 授刃
        </UiButton>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot danger-dot" />
        <strong>刺客正在寻找心怀异念之臣</strong>
        <small>候选名单与选择过程保持私密</small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'final_council'" class="phase-stack">
      <div class="assassination-hero court-hero">
        <span><Crown :size="29" /></span>
        <p>黑誓授刃成功</p>
        <h2>王庭最后议事</h2>
        <strong>
          {{ playerLabel(snapshot.courtUndercurrent.transformedPlayerId) }}
          已接过黑誓之刃；所有人仍可发言，梅林必须隐藏到最后
        </strong>
      </div>

      <button class="surface final-council-chat" type="button" @click="openSharedChat">
        <MessageCircle :size="21" />
        <div>
          <strong>打开最后议事</strong>
          <small>邪恶方可以判断，好人也可以冒充梅林制造假线索</small>
        </div>
        <ChevronRight :size="18" />
      </button>

      <div
        v-if="snapshot.shadowMerlin.enabled && snapshot.shadowMerlin.transformed"
        class="surface court-secret-note transformed"
      >
        <Shield :size="19" />
        <div>
          <strong>刺杀已经开始，暗影梅林已转为好人</strong>
          <small>梅林若被刺中，暗影梅林也会一同失败</small>
        </div>
      </div>

      <template v-if="snapshot.actions.canDissentingAssassinate">
        <div class="surface court-secret-note transformed">
          <Swords :size="19" />
          <div>
            <strong>你已必定转化为邪恶阵营</strong>
            <small>最终决定只能由你作出；确认目标将立即结束议事</small>
          </div>
        </div>
        <div class="selection-counter">
          <span>选择你认为的梅林</span>
          <strong>{{ dissentingTargetId ? '目标锁定' : '继续观察' }}</strong>
        </div>
        <div class="player-grid">
          <button
            v-for="player in snapshot.players.filter((item) =>
              snapshot.courtUndercurrent.eligibleTargetIds.includes(item.id),
            )"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: dissentingTargetId === player.id }"
            @click="dissentingTargetId = player.id"
          >
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
            <Swords v-if="dissentingTargetId === player.id" :size="18" />
          </button>
        </div>
        <UiButton
          variant="danger"
          block
          :disabled="!dissentingTargetId"
          @click="dissentingAssassinate"
        >
          确认刺杀 {{ playerLabel(dissentingTargetId) }}
        </UiButton>
      </template>
      <div v-else class="waiting-card tall">
        <span class="pulse-dot danger-dot" />
        <strong>
          {{ playerLabel(snapshot.courtUndercurrent.transformedPlayerId) }}
          正在判断梅林
        </strong>
        <small>持刃者已向全场公开，所有人都可以继续发言</small>
      </div>
    </section>

    <section v-else-if="snapshot.phase === 'game_over'" class="phase-stack">
      <div
        class="final-hero"
        :class="snapshot.result.winner === 'good' ? 'good' : 'evil'"
      >
        <span>
          <Shield v-if="snapshot.result.winner === 'good'" :size="31" />
          <Swords v-else :size="31" />
        </span>
        <p>{{ snapshot.result.winner === 'good' ? '亚瑟的荣光延续' : '阴影笼罩阿瓦隆' }}</p>
        <h2>{{ snapshot.result.winner === 'good' ? '好人阵营获胜' : '坏人阵营获胜' }}</h2>
        <strong>{{ snapshot.result.reason }}</strong>
      </div>

      <div
        v-if="snapshot.shadowMerlin.enabled && snapshot.shadowMerlin.councilTriggered"
        class="surface assassination-record court-ending-record"
        :class="snapshot.shadowMerlin.exileSuccess || (snapshot.shadowMerlin.assassinationChosen && !assassinationHit) ? 'missed' : 'hit'"
      >
        <header>
          <span><Crown :size="21" /></span>
          <div>
            <strong>祓影议庭记录</strong>
            <small>全部匿名选票仅在游戏结束后揭示</small>
          </div>
          <span class="assassination-status">
            {{
              snapshot.shadowMerlin.assassinationChosen
                ? '刺客发动刺杀'
                : snapshot.shadowMerlin.exileSuccess
                  ? '祓影成功'
                  : '祓影失败'
            }}
          </span>
        </header>

        <p v-if="snapshot.shadowMerlin.assassinationChosen">
          刺客发动刺杀，已锁定的祓影票随即作废；暗影梅林转为好人，刺客最终选择
          <strong>{{ playerLabel(snapshot.shadowMerlin.assassinationTargetId) }}</strong>。
        </p>
        <p v-else-if="snapshot.shadowMerlin.exileSuccess">
          刺客放弃刺杀；暗影梅林成为有效祓影票的唯一最高票，好人立即获胜。
        </p>
        <p v-else>
          刺客放弃刺杀；暗影梅林未成为唯一最高票，祓影失败。
        </p>

        <div class="court-candidate-summary">
          <small
            v-for="vote in snapshot.shadowMerlin.targetVotes"
            :key="`target-${vote.playerId}`"
          >
            {{ playerLabel(vote.playerId) }} → {{ playerLabel(vote.targetId) }}
            · {{ vote.effective ? '有效票' : '零票' }}
          </small>
        </div>
      </div>

      <div
        v-if="snapshot.courtUndercurrent.enabled && daggerTarget"
        class="surface assassination-record court-ending-record"
        :class="
          snapshot.courtUndercurrent.daggerHit && dissentingAssassinationHit
            ? 'hit'
            : 'missed'
        "
      >
        <header>
          <span><Swords :size="21" /></span>
          <div>
            <strong>王庭暗流终局</strong>
            <small>
              {{
                snapshot.courtUndercurrent.daggerHit
                  ? '授刃命中，心怀异念之臣被强制转化'
                  : '刺客选中了诱饵，授刃失败'
              }}
            </small>
          </div>
          <span class="assassination-status">
            {{
              !snapshot.courtUndercurrent.daggerHit
                ? '授刃失败'
                : dissentingAssassinationHit
                  ? '命中梅林'
                  : '刺杀失败'
            }}
          </span>
        </header>

        <div
          class="assassination-chain court-ending-chain"
          :class="{ complete: dissentingAssassinationTarget }"
        >
          <div v-if="assassinPlayer">
            <AvatarImage
              class="avatar number-avatar"
              :src="assassinPlayer.avatarUrl"
              :name="assassinPlayer.name"
              :fallback="assassinPlayer.seat + 1"
            />
            <strong>{{ playerDisplayName(assassinPlayer) }}</strong>
            <small>刺客</small>
          </div>
          <ArrowRight :size="20" />
          <div>
            <AvatarImage
              class="avatar number-avatar"
              :src="daggerTarget.avatarUrl"
              :name="daggerTarget.name"
              :fallback="daggerTarget.seat + 1"
            />
            <strong>{{ playerDisplayName(daggerTarget) }}</strong>
            <small>{{ daggerTarget.roleLabel }}</small>
          </div>
          <template
            v-if="
              snapshot.courtUndercurrent.daggerHit &&
              dissentingAssassinationTarget
            "
          >
            <ArrowRight :size="20" />
            <div>
              <AvatarImage
                class="avatar number-avatar"
                :src="dissentingAssassinationTarget.avatarUrl"
                :name="dissentingAssassinationTarget.name"
                :fallback="dissentingAssassinationTarget.seat + 1"
              />
              <strong>{{ playerDisplayName(dissentingAssassinationTarget) }}</strong>
              <small>{{ dissentingAssassinationTarget.roleLabel }}</small>
            </div>
          </template>
        </div>

        <p v-if="snapshot.courtUndercurrent.daggerHit && dissentingAssassinationTarget">
          刺客向 {{ playerLabel(daggerTarget.id) }} 成功授刃；心怀异念之臣随后选择
          {{ playerLabel(dissentingAssassinationTarget.id) }}，其真实身份为
          <strong>{{ dissentingAssassinationTarget.roleLabel }}</strong>。
        </p>
        <p v-else>
          刺客选择了 {{ playerLabel(daggerTarget.id) }}，但其真实身份是
          <strong>{{ daggerTarget.roleLabel }}</strong>，好人阵营立即获胜。
        </p>
        <div class="court-candidate-summary">
          <small>
            授刃候选：{{ playerLabels(snapshot.courtUndercurrent.daggerCandidateIds) }}
          </small>
          <small v-if="snapshot.courtUndercurrent.eligibleTargetIds.length">
            刺杀候选：{{ playerLabels(snapshot.courtUndercurrent.eligibleTargetIds) }}
          </small>
        </div>
      </div>

      <div
        v-if="assassinTarget"
        class="surface assassination-record"
        :class="assassinationHit ? 'hit' : 'missed'"
      >
        <header>
          <span><Swords :size="21" /></span>
          <div>
            <strong>刺杀记录</strong>
            <small>
              {{
                snapshot.result.endingRoute === 'exile_council_assassination'
                  ? '祓影议庭开启后，刺客选择发动刺杀'
                  : snapshot.result.assassinationWasEarly
                  ? '刺客在任务结束前发动了提前刺杀'
                  : '好人完成三次任务后的最终选择'
              }}
            </small>
          </div>
          <span class="assassination-status">
            {{ assassinationHit ? '命中梅林' : '刺杀失败' }}
          </span>
        </header>

        <div class="assassination-chain">
          <div v-if="assassinPlayer">
            <AvatarImage
              class="avatar number-avatar"
              :src="assassinPlayer.avatarUrl"
              :name="assassinPlayer.name"
              :fallback="assassinPlayer.seat + 1"
            />
            <strong>{{ playerDisplayName(assassinPlayer) }}</strong>
            <small>刺客</small>
          </div>
          <ArrowRight :size="20" />
          <div>
            <AvatarImage
              class="avatar number-avatar"
              :src="assassinTarget.avatarUrl"
              :name="assassinTarget.name"
              :fallback="assassinTarget.seat + 1"
            />
            <strong>{{ playerDisplayName(assassinTarget) }}</strong>
            <small>{{ assassinTarget.roleLabel }}</small>
          </div>
        </div>

        <p>
          {{ playerLabel(assassinPlayer?.id ?? null) }} 选择刺杀
          {{ playerLabel(assassinTarget.id) }}，其真实身份为
          <strong>{{ assassinTarget.roleLabel }}</strong>。
        </p>
      </div>

      <div class="surface role-reveal-list">
        <span>身份揭晓</span>
        <div
          v-for="player in snapshot.players"
          :key="player.id"
          class="reveal-row"
        >
          <AvatarImage
            class="avatar number-avatar"
            :src="player.avatarUrl"
            :name="player.name"
            :fallback="player.seat + 1"
          />
          <strong>{{ playerDisplayName(player) }}</strong>
          <span :class="['alignment-label', player.alignment]">
            {{ player.roleLabel }}
            <small
              v-if="player.id === snapshot.courtUndercurrent.transformedPlayerId"
            >
              已转为邪恶
            </small>
            <small
              v-if="player.role === 'shadow_merlin' && snapshot.shadowMerlin.transformed"
            >
              已转为好人
            </small>
          </span>
        </div>
      </div>

      <UiButton
        v-if="snapshot.actions.canRestart"
        variant="primary"
        block
        @click="room.restartGame"
      >
        <RotateCcw :size="18" /> 再来一局
      </UiButton>
      <div v-else class="waiting-card">
        <span class="pulse-dot" />
        等待房主决定是否再来一局
      </div>
    </section>

    <div
      v-if="showEarlyAssassination && snapshot.actions.canEarlyAssassinate"
      class="modal-backdrop"
      @click.self="showEarlyAssassination = false"
    >
      <section
        class="modal-card early-assassination-modal"
        role="dialog"
        aria-modal="true"
        aria-label="提前刺杀"
      >
        <UiIconButton
          compact
          class="dialog-close"
          aria-label="关闭提前刺杀"
          @click="showEarlyAssassination = false"
        >
          <X :size="20" />
        </UiIconButton>
        <span class="modal-icon danger-modal-icon">
          <Swords :size="25" />
        </span>
        <h2>发动提前刺杀</h2>
        <p>刺中梅林，坏人立即获胜；刺错，好人立即获胜。确认后无法撤销。</p>

        <div class="player-grid early-assassination-targets">
          <button
            v-for="player in assassinationCandidates"
            :key="player.id"
            type="button"
            class="player-tile"
            :class="{ selected: earlyAssassinTargetId === player.id }"
            @click="earlyAssassinTargetId = player.id"
          >
            <AvatarImage
              class="avatar number-avatar"
              :src="player.avatarUrl"
              :name="player.name"
              :fallback="player.seat + 1"
            />
            <strong>{{ playerDisplayName(player) }}</strong>
            <Swords v-if="earlyAssassinTargetId === player.id" :size="18" />
          </button>
        </div>

        <UiButton
          variant="danger"
          block
          :disabled="!earlyAssassinTargetId"
          @click="earlyAssassinate"
        >
          确认刺杀 {{ playerLabel(earlyAssassinTargetId) }}
        </UiButton>
      </section>
    </div>

    <div
      v-if="showLadyHistory"
      class="modal-backdrop"
      @click.self="showLadyHistory = false"
    >
      <section
        class="modal-card lady-history-modal"
        role="dialog"
        aria-modal="true"
        aria-label="湖中仙女查验历史"
      >
        <UiIconButton
          compact
          class="dialog-close"
          aria-label="关闭仙女记录"
          @click="showLadyHistory = false"
        >
          <X :size="20" />
        </UiIconButton>
        <span class="modal-icon"><Sparkles :size="25" /></span>
        <h2>仙女记录</h2>
        <p>查验关系公开，查验结果在游戏中保持私密</p>

        <div class="lady-history-list">
          <article
            v-for="check in snapshot.lady.history"
            :key="`${check.missionNumber}-${check.inspectorId}-${check.targetId}`"
            class="lady-history-item"
          >
            <header>
              第 {{ check.missionNumber }} 次任务后
            </header>
            <div class="lady-history-chain">
              <div>
                <AvatarImage
                  class="avatar number-avatar"
                  :src="playerAvatar(check.inspectorId)"
                  :name="check.inspectorName"
                  :fallback="playerNumber(check.inspectorId) ?? check.inspectorName.slice(0, 1)"
                />
                <strong>{{ playerLabel(check.inspectorId) }}</strong>
                <small>查验者</small>
              </div>
              <ArrowRight :size="19" />
              <div>
                <AvatarImage
                  class="avatar number-avatar"
                  :src="playerAvatar(check.targetId)"
                  :name="check.targetName"
                  :fallback="playerNumber(check.targetId) ?? check.targetName.slice(0, 1)"
                />
                <strong>{{ playerLabel(check.targetId) }}</strong>
                <small>被查验并接过仙女</small>
              </div>
            </div>

            <div
              v-if="myLadyCheck(check.missionNumber, check.targetId)"
              class="lady-history-result private"
              :class="
                myLadyCheck(check.missionNumber, check.targetId)?.alignment
              "
            >
              <Eye :size="15" />
              你看到：
              {{
                myLadyCheck(check.missionNumber, check.targetId)?.alignment ===
                'good'
                  ? '好人阵营'
                  : '坏人阵营'
              }}
            </div>
            <div
              v-else-if="
                snapshot.phase === 'game_over' &&
                revealedAlignment(check.targetId)
              "
              class="lady-history-result revealed"
              :class="revealedAlignment(check.targetId)"
            >
              真实阵营：
              {{
                revealedAlignment(check.targetId) === 'good'
                  ? '好人阵营'
                  : '坏人阵营'
              }}
            </div>
            <div v-else class="lady-history-result hidden">
              结果仅 {{ playerLabel(check.inspectorId) }} 可见
            </div>
          </article>
        </div>

        <div class="lady-current-holder">
          <Sparkles :size="16" />
          {{ snapshot.phase === 'game_over' ? '最终' : '当前' }}持有者：
          <strong>{{ playerLabel(snapshot.lady.holderId) }}</strong>
        </div>
      </section>
    </div>

    <div
      v-if="showReplay"
      class="modal-backdrop"
      @click.self="showReplay = false"
    >
      <section
        class="modal-card replay-modal"
        role="dialog"
        aria-modal="true"
        aria-label="组队投票复盘"
      >
        <UiIconButton
          compact
          class="dialog-close"
          aria-label="关闭投票复盘"
          @click="showReplay = false"
        >
          <X :size="20" />
        </UiIconButton>
        <span class="modal-icon"><History :size="25" /></span>
        <h2>
          {{ selectedReplayMission === null ? '投票复盘' : `第 ${selectedReplayMission} 轮复盘` }}
        </h2>
        <p>
          {{ selectedReplayMission === null ? '按时间记录每次组队和公开表决' : '本轮全部组队和公开表决' }}
        </p>

        <div class="replay-list">
          <article
            v-for="(proposal, index) in replayProposals"
            :key="`${proposal.missionNumber}-${proposal.attempt}-${index}`"
            class="replay-round"
          >
            <header>
              <div>
                <strong>
                  第 {{ proposal.missionNumber }} 次任务
                </strong>
                <small>第 {{ proposal.attempt }} 次组队</small>
                <span class="replay-leader">
                  <Crown :size="12" />
                  队长 {{ playerLabel(proposal.leaderId) }}
                </span>
              </div>
              <span :class="proposal.accepted ? 'accepted' : 'rejected'">
                {{ proposal.accepted ? '通过' : '否决' }}
              </span>
            </header>

            <div class="replay-team">
              <span>任务队伍</span>
              <div>
                <strong
                  v-for="playerId in proposal.teamIds"
                  :key="playerId"
                  :class="{ leader: playerId === proposal.leaderId }"
                >
                  {{ playerLabel(playerId) }}
                  <small v-if="playerId === proposal.leaderId">队长</small>
                </strong>
              </div>
            </div>

            <div class="replay-votes">
              <span
                v-for="vote in proposal.votes"
                :key="vote.playerId"
                :class="vote.approve ? 'vote-yes' : 'vote-no'"
              >
                {{ playerLabel(vote.playerId) }}
                {{ vote.approve ? '赞成' : '反对' }}
              </span>
            </div>

            <div
              v-if="
                missionOutcome(proposal.missionNumber) &&
                (proposal.accepted ||
                  (proposal.attempt === 5 &&
                    missionOutcome(proposal.missionNumber)?.failedByRejections))
              "
              class="replay-mission-result"
              :class="
                missionOutcome(proposal.missionNumber)?.success
                  ? 'success'
                  : 'failed'
              "
            >
              <span>
                {{
                  missionOutcome(proposal.missionNumber)?.success
                    ? '任务成功'
                    : '任务失败'
                }}
              </span>
              <strong>
                {{
                  missionOutcome(proposal.missionNumber)?.failedByRejections
                    ? '五次组队均被否决'
                    : `${missionOutcome(proposal.missionNumber)?.failCount} 张失败票`
                }}
              </strong>
            </div>
          </article>
        </div>
        <small class="replay-privacy">
          任务票保持匿名，仅展示失败票总数
        </small>
      </section>
    </div>

  </div>
</template>
