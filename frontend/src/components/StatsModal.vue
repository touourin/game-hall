<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ArrowLeft, History, LoaderCircle, Shield, Swords, X } from '@lucide/vue'
import {
  loadMatchDetail,
  loadPersonalStats,
  type MatchDetail,
  type MatchHistoryItem,
  type StatsSummary,
} from '../stats'

const props = defineProps<{ gameKey?: string; gameName?: string }>()
defineEmits<{ close: [] }>()

const summary = ref<StatsSummary | null>(null)
const history = ref<MatchHistoryItem[]>([])
const selectedMatch = ref<MatchDetail | null>(null)
const loading = ref(true)
const detailLoading = ref(false)
const error = ref<string | null>(null)

const roleLabels: Record<string, string> = {
  merlin: '梅林',
  percival: '派西维尔',
  loyal_servant: '亚瑟的忠臣',
  assassin: '刺客',
  morgana: '莫甘娜',
  mordred: '莫德雷德',
  oberon: '奥伯伦',
  minion: '莫德雷德的爪牙',
  black: '黑方',
  white: '白方',
  red: '红方',
  landlord: '地主',
  farmer: '农民',
  blue: '蓝方',
  'dark-red': '暗军旗·红方',
  'dark-blue': '暗军旗·蓝方',
  'flip-red': '翻棋军旗·红方',
  'flip-blue': '翻棋军旗·蓝方',
  tester: '测试者',
}

function roleLabel(role: string): string {
  return roleLabels[role] ?? role
}

function winnerLabel(match: MatchDetail): string {
  if (match.gameKey === 'reaction') return '三轮测试完成'
  if (match.winner === 'draw') return '双方和棋'
  if (match.gameKey === 'avalon') return match.winner === 'good' ? '好人获胜' : '坏人获胜'
  return `${roleLabel(match.winner)}获胜`
}

function outcomeLabel(match: MatchHistoryItem): string {
  if (match.outcome === 'draw') return '和'
  if (match.outcome === 'completed') return '测'
  return match.outcome === 'win' ? '胜' : '负'
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function playerFor(match: MatchDetail, playerId: string) {
  return match.details.players.find((player) => player.id === playerId)
}

function playerLabel(match: MatchDetail, playerId: string): string {
  const player = playerFor(match, playerId)
  return player ? `${player.seat + 1}号 ${player.name}` : '未知玩家'
}

function seatList(match: MatchDetail, playerIds: string[]): string {
  return playerIds
    .map((playerId) => playerFor(match, playerId))
    .filter((player) => player !== undefined)
    .map((player) => `${player.seat + 1}号`)
    .join('、')
}

async function openMatch(matchId: string) {
  detailLoading.value = true
  error.value = null
  try {
    selectedMatch.value = await loadMatchDetail(matchId)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '读取战绩失败'
  } finally {
    detailLoading.value = false
  }
}

onMounted(async () => {
  try {
    const data = await loadPersonalStats(props.gameKey)
    summary.value = data.summary
    history.value = data.history
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '读取战绩失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="modal-card stats-modal" role="dialog" aria-modal="true">
      <button class="modal-close" type="button" aria-label="关闭战绩" @click="$emit('close')">
        <X :size="20" />
      </button>

      <template v-if="selectedMatch">
        <button class="stats-back" type="button" @click="selectedMatch = null">
          <ArrowLeft :size="16" /> 返回战绩列表
        </button>
        <span class="modal-icon"><History :size="24" /></span>
        <h2>{{ selectedMatch.gameName }} · 房间 {{ selectedMatch.roomCode }}</h2>
        <p>{{ formatDate(selectedMatch.endedAt) }} · {{ selectedMatch.playerCount }} 人局</p>
        <p v-if="selectedMatch.gameKey === 'junqi'" class="match-mode-label">
          {{ selectedMatch.details.options?.mode === 'flip' ? '翻棋军旗' : '暗军旗' }}
        </p>

        <div class="match-detail-result" :class="selectedMatch.winner">
          <strong>{{ winnerLabel(selectedMatch) }}</strong>
          <span>{{ selectedMatch.reason }}</span>
        </div>

        <div v-if="selectedMatch.gameKey === 'avalon'" class="match-detail-section">
          <span>最终身份</span>
          <div class="match-player-list">
            <div v-for="player in selectedMatch.details.players" :key="player.id">
              <b>{{ player.seat + 1 }}号</b>
              <strong>{{ player.name }}<small v-if="player.isBot">AI</small></strong>
              <em :class="player.alignment">{{ roleLabel(player.role ?? '') }}</em>
            </div>
          </div>
        </div>

        <div v-if="selectedMatch.gameKey === 'avalon'" class="match-detail-section">
          <span>任务结果</span>
          <div class="match-mission-list">
            <div
              v-for="mission in selectedMatch.details.missions ?? []"
              :key="mission.number"
              :class="mission.success ? 'success' : 'failed'"
            >
              <strong>第 {{ mission.number }} 次任务</strong>
              <span>{{ mission.success ? '成功' : `失败 · ${mission.failCount} 张失败票` }}</span>
              <small>队伍：{{ seatList(selectedMatch, mission.teamIds) }}</small>
            </div>
          </div>
        </div>

        <div v-if="selectedMatch.gameKey === 'avalon'" class="match-detail-section">
          <span>组队与投票复盘</span>
          <div class="match-proposal-list">
            <article
              v-for="(proposal, index) in selectedMatch.details.proposals ?? []"
              :key="`${proposal.missionNumber}-${proposal.attempt}-${index}`"
            >
              <header>
                <strong>第 {{ proposal.missionNumber }} 轮 · 第 {{ proposal.attempt }} 次组队</strong>
                <em :class="proposal.accepted ? 'accepted' : 'rejected'">
                  {{ proposal.accepted ? '通过' : '否决' }}
                </em>
              </header>
              <p>队长：{{ playerLabel(selectedMatch, proposal.leaderId) }}</p>
              <p>队伍：{{ seatList(selectedMatch, proposal.teamIds) }}</p>
              <div class="match-vote-list">
                <span
                  v-for="player in selectedMatch.details.players"
                  :key="player.id"
                  :class="proposal.votes[player.id] ? 'approve' : 'reject'"
                >
                  {{ player.seat + 1 }}号 {{ proposal.votes[player.id] ? '赞成' : '反对' }}
                </span>
              </div>
            </article>
          </div>
        </div>

        <div v-if="selectedMatch.gameKey === 'avalon' && selectedMatch.details.ladyChecks?.length" class="match-detail-section">
          <span>湖中仙女查验</span>
          <div class="match-lady-list">
            <div v-for="check in selectedMatch.details.ladyChecks" :key="`${check.missionNumber}-${check.targetId}`">
              <strong>第 {{ check.missionNumber }} 次任务后</strong>
              <span>
                {{ playerLabel(selectedMatch, check.inspectorId) }} →
                {{ playerLabel(selectedMatch, check.targetId) }}
              </span>
              <em :class="check.alignment">
                {{ check.alignment === 'good' ? '好人阵营' : '坏人阵营' }}
              </em>
            </div>
          </div>
        </div>

        <div v-if="selectedMatch.gameKey === 'avalon' && selectedMatch.details.assassinTargetId" class="match-assassination-record">
          <strong>{{ selectedMatch.details.assassinationWasEarly ? '提前刺杀' : '最终刺杀' }}</strong>
          <span>目标：{{ playerLabel(selectedMatch, selectedMatch.details.assassinTargetId) }}</span>
          <em :class="selectedMatch.assassinationHit ? 'hit' : 'miss'">
            {{ selectedMatch.assassinationHit ? '命中梅林' : '刺杀失败' }}
          </em>
        </div>

        <div v-if="selectedMatch.gameKey === 'reaction'" class="match-detail-section">
          <span>反应挑战成绩</span>
          <div class="match-mission-list">
            <div
              v-for="(result, index) in selectedMatch.details.state?.results_ms ?? []"
              :key="index"
              class="success"
            >
              <strong>第 {{ index + 1 }} 轮</strong>
              <span>{{ result }} ms</span>
            </div>
          </div>
        </div>

        <div v-if="selectedMatch.gameKey !== 'avalon' && selectedMatch.gameKey !== 'reaction'" class="match-detail-section">
          <span>参赛玩家</span>
          <div class="match-player-list">
            <div v-for="player in selectedMatch.details.players" :key="player.id">
              <b>{{ player.seat + 1 }}号</b>
              <strong>{{ player.name }}</strong>
              <em v-if="selectedMatch.gameKey === 'junqi'" :class="player.alignment">
                {{ roleLabel(player.role ?? '') }}
              </em>
            </div>
          </div>
        </div>

        <p class="match-detail-note">
          {{ selectedMatch.gameKey === 'reaction'
            ? selectedMatch.ranked ? '本次成绩计入反应时间排行榜' : '本次成绩不计排行榜'
            : selectedMatch.ranked ? '本局计入排行榜' : '本局含 AI，不计排行榜' }}
        </p>
      </template>

      <template v-else>
        <span class="modal-icon"><History :size="24" /></span>
        <h2>{{ props.gameName ? `${props.gameName}战绩` : '我的全部战绩' }}</h2>
        <p>{{ props.gameKey === 'reaction' ? '记录每次三轮测试的平均值与单轮明细。' : '每款游戏独立记录胜负，对局详情绑定当前账号。' }}</p>

        <div v-if="loading" class="stats-loading">
          <LoaderCircle :size="24" /> 正在读取战绩…
        </div>
        <template v-else-if="summary">
          <div class="stats-summary-grid">
            <template v-if="props.gameKey === 'reaction'">
              <div><strong>{{ summary.games }}</strong><span>测试次数</span></div>
              <div><strong>{{ summary.bestMs === null ? '—' : `${summary.bestMs} ms` }}</strong><span>历史最佳</span></div>
              <div><strong>{{ summary.averageMs === null ? '—' : `${summary.averageMs} ms` }}</strong><span>总平均</span></div>
            </template>
            <template v-else>
              <div><strong>{{ summary.games }}</strong><span>总场次</span></div>
              <div><strong>{{ summary.wins }}</strong><span>胜场</span></div>
              <div><strong>{{ summary.winRate }}%</strong><span>胜率</span></div>
            </template>
          </div>
          <div v-if="props.gameKey === 'avalon'" class="alignment-summary">
            <span><Shield :size="15" /> 好人 {{ summary.goodWins }}/{{ summary.goodGames }}</span>
            <span><Swords :size="15" /> 坏人 {{ summary.evilWins }}/{{ summary.evilGames }}</span>
          </div>
          <div v-if="['gomoku', 'xiangqi', 'go'].includes(props.gameKey ?? '')" class="match-result-summary">
            <span>胜 {{ summary.wins }}</span>
            <span>和 {{ summary.draws }}</span>
            <span>负 {{ summary.losses }}</span>
          </div>

          <div v-if="history.length" class="match-history-list">
            <button v-for="match in history" :key="match.id" type="button" @click="openMatch(match.id)">
              <span :class="['match-outcome', match.outcome]">
                {{ outcomeLabel(match) }}
              </span>
              <span class="match-history-copy">
                <strong v-if="match.gameKey === 'avalon'">{{ roleLabel(match.role) }} · {{ match.alignment === 'good' ? '好人' : '坏人' }}</strong>
                <strong v-else-if="match.gameKey === 'reaction'">三轮平均 · {{ match.scoreMs }} ms</strong>
                <strong v-else>{{ match.gameName }} · {{ roleLabel(match.role) }}</strong>
                <small v-if="match.gameKey === 'reaction'">{{ formatDate(match.endedAt) }} · 三轮测试</small>
                <small v-else>{{ formatDate(match.endedAt) }} · {{ match.playerCount }} 人 · 房间 {{ match.roomCode }}</small>
              </span>
              <em :class="{ unranked: !match.ranked }">{{ match.ranked ? '计榜' : '测试局' }}</em>
            </button>
          </div>
          <div v-else class="stats-empty">还没有完成的对局</div>
        </template>

        <p v-if="detailLoading" class="stats-loading"><LoaderCircle :size="17" /> 正在打开记录…</p>
      </template>

      <p v-if="error" class="account-error" role="alert">{{ error }}</p>
    </section>
  </div>
</template>
