<script setup lang="ts">
import type { MatchDetail } from '../../stats'

const props = defineProps<{ match: MatchDetail }>()

const roleLabels: Record<string, string> = {
  merlin: '梅林',
  percival: '派西维尔',
  loyal_servant: '亚瑟的忠臣',
  dissenting_courtier: '心怀异念之臣',
  shadow_merlin: '暗影梅林',
  assassin: '刺客',
  morgana: '莫甘娜',
  mordred: '莫德雷德',
  oberon: '奥伯伦',
  minion: '莫德雷德的爪牙',
}

function roleLabel(role: string): string {
  return roleLabels[role] ?? role
}

function playerFor(playerId: string) {
  return props.match.details.players.find((player) => player.id === playerId)
}

function playerLabel(playerId: string): string {
  const player = playerFor(playerId)
  return player ? `${player.seat + 1}号 ${player.name}` : '未知玩家'
}

function seatList(playerIds: string[]): string {
  return playerIds
    .map(playerFor)
    .filter((player) => player !== undefined)
    .map((player) => `${player.seat + 1}号`)
    .join('、')
}
</script>

<template>
  <div class="match-detail-section">
    <span>最终身份</span>
    <div class="match-player-list">
      <div v-for="player in match.details.players" :key="player.id">
        <b>{{ player.seat + 1 }}号</b>
        <strong>{{ player.name }}<small v-if="player.isBot">AI</small></strong>
        <em :class="player.finalAlignment ?? player.alignment">
          {{ roleLabel(player.role ?? '') }}
          <small v-if="player.transformed"> · 已转化</small>
        </em>
      </div>
    </div>
  </div>

  <div class="match-detail-section">
    <span>任务结果</span>
    <div class="match-mission-list">
      <div
        v-for="mission in match.details.missions ?? []"
        :key="mission.number"
        :class="mission.success ? 'success' : 'failed'"
      >
        <strong>第 {{ mission.number }} 次任务</strong>
        <span>
          {{ mission.success
            ? '成功'
            : mission.failedByRejections
              ? '失败 · 五次组队均被否决'
              : `失败 · ${mission.failCount} 张失败票` }}
        </span>
        <small>
          {{ mission.failedByRejections
            ? '本次任务未执行'
            : `队伍：${seatList(mission.teamIds)}` }}
        </small>
      </div>
    </div>
  </div>

  <div class="match-detail-section">
    <span>组队与投票复盘</span>
    <div class="match-proposal-list">
      <article
        v-for="(proposal, index) in match.details.proposals ?? []"
        :key="`${proposal.missionNumber}-${proposal.attempt}-${index}`"
      >
        <header>
          <strong>第 {{ proposal.missionNumber }} 轮 · 第 {{ proposal.attempt }} 次组队</strong>
          <em :class="proposal.accepted ? 'accepted' : 'rejected'">
            {{ proposal.accepted ? '通过' : '否决' }}
          </em>
        </header>
        <p>队长：{{ playerLabel(proposal.leaderId) }}</p>
        <p>队伍：{{ seatList(proposal.teamIds) }}</p>
        <div class="match-vote-list">
          <span
            v-for="player in match.details.players"
            :key="player.id"
            :class="proposal.votes[player.id] ? 'approve' : 'reject'"
          >
            {{ player.seat + 1 }}号 {{ proposal.votes[player.id] ? '赞成' : '反对' }}
          </span>
        </div>
      </article>
    </div>
  </div>

  <div v-if="match.details.ladyChecks?.length" class="match-detail-section">
    <span>湖中仙女查验</span>
    <div class="match-lady-list">
      <div
        v-for="check in match.details.ladyChecks"
        :key="`${check.missionNumber}-${check.targetId}`"
      >
        <strong>第 {{ check.missionNumber }} 次任务后</strong>
        <span>
          {{ playerLabel(check.inspectorId) }} → {{ playerLabel(check.targetId) }}
        </span>
        <em :class="check.alignment">
          {{ check.alignment === 'good' ? '好人阵营' : '坏人阵营' }}
        </em>
      </div>
    </div>
  </div>

  <div v-if="match.details.assassinTargetId" class="match-assassination-record">
    <strong>
      {{ match.endingRoute === 'exile_council_assassination'
        ? '祓影议庭刺杀'
        : match.details.assassinationWasEarly
          ? '提前刺杀'
          : '最终刺杀' }}
    </strong>
    <span>目标：{{ playerLabel(match.details.assassinTargetId) }}</span>
    <em :class="match.assassinationHit ? 'hit' : 'miss'">
      {{ match.assassinationHit ? '命中梅林' : '刺杀失败' }}
    </em>
  </div>

  <div
    v-if="match.details.shadowMerlin?.councilTriggered"
    class="match-detail-section"
  >
    <span>祓影议庭</span>
    <div class="match-court-timeline">
      <div>
        <strong>议庭结果</strong>
        <span>
          {{ match.details.shadowMerlin.councilOpened ? '祓影议庭开启' : '祓影议庭未开启' }}
        </span>
      </div>
      <div v-if="match.details.shadowMerlin.councilOpened">
        <strong>刺客选择</strong>
        <span>
          {{ match.details.shadowMerlin.assassinationChosen
            ? '发动刺杀'
            : '放弃刺杀并结算祓影票' }}
        </span>
      </div>
      <div v-if="match.details.shadowMerlin.exileTargetId">
        <strong>祓影目标</strong>
        <span>{{ playerLabel(match.details.shadowMerlin.exileTargetId) }}</span>
        <em :class="match.details.shadowMerlin.exileSuccess ? 'hit' : 'miss'">
          {{ match.details.shadowMerlin.exileSuccess ? '祓影成功' : '祓影失败' }}
        </em>
      </div>
    </div>
  </div>

  <div
    v-if="match.details.courtUndercurrent?.daggerTargetId"
    class="match-detail-section"
  >
    <span>王庭暗流终局</span>
    <div class="match-court-timeline">
      <div>
        <strong>授刃候选</strong>
        <span>{{ seatList(match.details.courtUndercurrent.daggerCandidateIds) }}</span>
      </div>
      <div>
        <strong>刺客选择</strong>
        <span>{{ playerLabel(match.details.courtUndercurrent.daggerTargetId) }}</span>
        <em :class="match.recruitmentHit ? 'hit' : 'miss'">
          {{ match.recruitmentHit ? '授刃成功' : '授刃失败' }}
        </em>
      </div>
      <div v-if="match.details.courtUndercurrent.assassinationTargetId">
        <strong>心怀异念之臣刺杀</strong>
        <span>
          {{ playerLabel(match.details.courtUndercurrent.assassinationTargetId) }}
        </span>
        <em :class="match.assassinationHit ? 'hit' : 'miss'">
          {{ match.assassinationHit ? '命中梅林' : '刺杀失败' }}
        </em>
      </div>
    </div>
  </div>
</template>
