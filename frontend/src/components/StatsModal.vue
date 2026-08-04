<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { History, LoaderCircle, Shield, Swords, X } from '@lucide/vue'
import BackNavigationButton from './BackNavigationButton.vue'
import {
  loadMatchDetail,
  loadPersonalStats,
  type MatchDetail,
  type MatchHistoryItem,
  type StatsSummary,
} from '../stats'

const props = defineProps<{ gameKey?: string; gameName?: string; gameMode?: string }>()
defineEmits<{ close: [] }>()

const summary = ref<StatsSummary | null>(null)
const history = ref<MatchHistoryItem[]>([])
const selectedMatch = ref<MatchDetail | null>(null)
const loading = ref(true)
const detailLoading = ref(false)
const error = ref<string | null>(null)
const activeGameMode = ref<string | undefined>(
  props.gameMode ?? (props.gameKey === 'avalon' ? 'standard' : undefined),
)

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
  challenger: '挑战者',
  sweeper: '排雷员',
  solver: '解谜者',
}

function roleLabel(role: string): string {
  return roleLabels[role] ?? role
}

function winnerLabel(match: MatchDetail): string {
  if (match.gameKey === 'reaction') return '三轮测试完成'
  if (match.gameKey === 'schulte') return '舒尔特挑战完成'
  if (match.gameKey === 'minesweeper') return match.winner === 'completed' ? '扫雷挑战完成' : '踩中地雷'
  if (match.gameKey === 'hanoi') return '汉诺塔挑战完成'
  if (match.gameKey === 'poker') return '筹码结算完成'
  if (match.winner === 'draw') return '双方和棋'
  if (match.gameKey === 'avalon') return match.winner === 'good' ? '好人获胜' : '坏人获胜'
  return `${roleLabel(match.winner)}获胜`
}

function outcomeLabel(match: MatchHistoryItem): string {
  if (match.gameKey === 'hanoi') return '成'
  if (match.gameKey === 'schulte') return '格'
  if (match.gameKey === 'minesweeper') return match.outcome === 'completed' ? '通' : '雷'
  if (match.outcome === 'draw') return '和'
  if (match.outcome === 'completed') return match.gameKey === 'hanoi' ? '成' : '测'
  return match.outcome === 'win' ? '胜' : '负'
}

function formatDuration(milliseconds: number | null | undefined): string {
  if (milliseconds === null || milliseconds === undefined) return '—'
  const totalSeconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return minutes ? `${minutes} 分 ${seconds} 秒` : `${seconds}.${Math.floor(milliseconds % 1000 / 100)} 秒`
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function percentage(hits: number | undefined, attempts: number | undefined): string {
  if (!attempts) return '—'
  return `${Math.round(Number(hits ?? 0) / attempts * 100)}%`
}

function difficultyLabel(value: string | null | undefined): string {
  if (value === 'expert') return '高级'
  if (value === 'intermediate') return '中级'
  if (value === 'beginner') return '初级'
  return ''
}

function avalonModeLabel(value: string | null | undefined): string {
  return value === 'court_undercurrent' ? '王庭暗流' : '标准模式'
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

async function loadStats() {
  loading.value = true
  error.value = null
  try {
    const data = await loadPersonalStats(props.gameKey, activeGameMode.value)
    summary.value = data.summary
    history.value = data.history
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '读取战绩失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
watch(activeGameMode, loadStats)
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="modal-card stats-modal" role="dialog" aria-modal="true">
      <button class="modal-close" type="button" aria-label="关闭战绩" @click="$emit('close')">
        <X :size="20" />
      </button>

      <template v-if="selectedMatch">
        <BackNavigationButton
          class="stats-back"
          label="返回战绩列表"
          @click="selectedMatch = null"
        />
        <span class="modal-icon"><History :size="24" /></span>
        <h2>{{ selectedMatch.gameName }} · 房间 {{ selectedMatch.roomCode }}</h2>
        <p>{{ formatDate(selectedMatch.endedAt) }} · {{ selectedMatch.playerCount }} 人局</p>
        <p v-if="selectedMatch.gameKey === 'avalon'" class="match-mode-label">
          {{ avalonModeLabel(selectedMatch.gameMode ?? selectedMatch.details.mode) }}
        </p>
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
              <em :class="player.finalAlignment ?? player.alignment">
                {{ roleLabel(player.role ?? '') }}
                <small v-if="player.transformed"> · 已转化</small>
              </em>
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
              <span>
                {{
                  mission.success
                    ? '成功'
                    : mission.failedByRejections
                      ? '失败 · 五次组队均被否决'
                      : `失败 · ${mission.failCount} 张失败票`
                }}
              </span>
              <small>
                {{
                  mission.failedByRejections
                    ? '本次任务未执行'
                    : `队伍：${seatList(selectedMatch, mission.teamIds)}`
                }}
              </small>
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
          <strong>
            {{
              selectedMatch.endingRoute === 'exile_council_assassination'
                ? '驱逐议会刺杀'
                : selectedMatch.details.assassinationWasEarly
                  ? '提前刺杀'
                  : '最终刺杀'
            }}
          </strong>
          <span>目标：{{ playerLabel(selectedMatch, selectedMatch.details.assassinTargetId) }}</span>
          <em :class="selectedMatch.assassinationHit ? 'hit' : 'miss'">
            {{ selectedMatch.assassinationHit ? '命中梅林' : '刺杀失败' }}
          </em>
        </div>

        <div
          v-if="selectedMatch.gameKey === 'avalon' && selectedMatch.details.shadowMerlin?.councilTriggered"
          class="match-detail-section"
        >
          <span>驱逐议会</span>
          <div class="match-court-timeline">
            <div>
              <strong>议会结果</strong>
              <span>
                {{ selectedMatch.details.shadowMerlin.councilOpened ? '议会开启' : '议会未开启' }}
              </span>
            </div>
            <div v-if="selectedMatch.details.shadowMerlin.councilOpened">
              <strong>刺客选择</strong>
              <span>
                {{ selectedMatch.details.shadowMerlin.assassinationChosen ? '发动刺杀' : '放弃刺杀并结算驱逐' }}
              </span>
            </div>
            <div v-if="selectedMatch.details.shadowMerlin.exileTargetId">
              <strong>驱逐目标</strong>
              <span>{{ playerLabel(selectedMatch, selectedMatch.details.shadowMerlin.exileTargetId) }}</span>
              <em :class="selectedMatch.details.shadowMerlin.exileSuccess ? 'hit' : 'miss'">
                {{ selectedMatch.details.shadowMerlin.exileSuccess ? '正确驱逐' : '驱逐错误' }}
              </em>
            </div>
          </div>
        </div>

        <div
          v-if="
            selectedMatch.gameKey === 'avalon' &&
            selectedMatch.details.courtUndercurrent?.daggerTargetId
          "
          class="match-detail-section"
        >
          <span>王庭暗流终局</span>
          <div class="match-court-timeline">
            <div>
              <strong>授刃候选</strong>
              <span>
                {{
                  seatList(
                    selectedMatch,
                    selectedMatch.details.courtUndercurrent.daggerCandidateIds,
                  )
                }}
              </span>
            </div>
            <div>
              <strong>刺客选择</strong>
              <span>
                {{
                  playerLabel(
                    selectedMatch,
                    selectedMatch.details.courtUndercurrent.daggerTargetId,
                  )
                }}
              </span>
              <em :class="selectedMatch.recruitmentHit ? 'hit' : 'miss'">
                {{ selectedMatch.recruitmentHit ? '授刃成功' : '授刃失败' }}
              </em>
            </div>
            <div
              v-if="selectedMatch.details.courtUndercurrent.assassinationTargetId"
            >
              <strong>心怀异念之臣刺杀</strong>
              <span>
                {{
                  playerLabel(
                    selectedMatch,
                    selectedMatch.details.courtUndercurrent.assassinationTargetId,
                  )
                }}
              </span>
              <em :class="selectedMatch.assassinationHit ? 'hit' : 'miss'">
                {{ selectedMatch.assassinationHit ? '命中梅林' : '刺杀失败' }}
              </em>
            </div>
          </div>
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

        <div v-if="selectedMatch.gameKey === 'hanoi'" class="match-detail-section">
          <span>汉诺塔挑战成绩</span>
          <div class="match-mission-list">
            <div class="success">
              <strong>{{ selectedMatch.details.state?.disc_count }} 层圆盘</strong>
              <span>{{ selectedMatch.details.state?.moves }} 步完成</span>
              <small>理论最少 {{ 2 ** Number(selectedMatch.details.state?.disc_count ?? 0) - 1 }} 步</small>
            </div>
            <div class="success">
              <strong>完成用时</strong>
              <span>{{ formatDuration(selectedMatch.details.state?.elapsed_ms) }}</span>
            </div>
          </div>
        </div>

        <div v-if="selectedMatch.gameKey === 'schulte'" class="match-detail-section">
          <span>舒尔特挑战成绩</span>
          <div class="match-mission-list">
            <div class="success">
              <strong>5×5 标准方格</strong>
              <span>{{ formatDuration(selectedMatch.details.state?.elapsed_ms) }}</span>
              <small>按顺序完成 1–25</small>
            </div>
            <div class="success">
              <strong>点击准确率</strong>
              <span>{{ Math.round(25 / (25 + Number(selectedMatch.details.state?.mistakes ?? 0)) * 100) }}%</span>
              <small>{{ selectedMatch.details.state?.mistakes ?? 0 }} 次错误点击</small>
            </div>
          </div>
        </div>

        <div v-if="selectedMatch.gameKey === 'minesweeper'" class="match-detail-section">
          <span>扫雷挑战成绩</span>
          <div class="match-mission-list">
            <div :class="selectedMatch.winner === 'completed' ? 'success' : 'failed'">
              <strong>{{ difficultyLabel(selectedMatch.details.state?.difficulty) }} · {{ selectedMatch.details.state?.rows }}×{{ selectedMatch.details.state?.columns }}</strong>
              <span>{{ selectedMatch.winner === 'completed' ? formatDuration(selectedMatch.details.state?.elapsed_ms) : '踩中地雷' }}</span>
              <small>{{ selectedMatch.details.state?.mine_count }} 雷 · 已翻开 {{ selectedMatch.details.state?.revealed_count }} 个安全格</small>
            </div>
            <div class="success">
              <strong>本轮标记</strong>
              <span>{{ selectedMatch.details.state?.flagged_count ?? 0 }} 面旗帜</span>
              <small>首次翻开区域由服务端保证安全</small>
            </div>
          </div>
        </div>

        <div v-if="!['avalon', 'reaction', 'schulte', 'minesweeper', 'hanoi'].includes(selectedMatch.gameKey)" class="match-detail-section">
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
            : selectedMatch.gameKey === 'schulte'
              ? selectedMatch.ranked ? '本次成绩计入舒尔特方格排行榜' : '本次成绩不计排行榜'
            : selectedMatch.gameKey === 'minesweeper'
              ? selectedMatch.winner === 'completed' && selectedMatch.ranked ? `本次成绩计入${difficultyLabel(selectedMatch.details.state?.difficulty)}扫雷排行榜` : '未通关，不计入排行榜'
            : selectedMatch.gameKey === 'hanoi'
              ? selectedMatch.ranked ? '本次通关计入汉诺塔累计通关榜' : '本次通关不计排行榜'
            : selectedMatch.ranked ? '本局计入排行榜' : '本局含 AI，不计排行榜' }}
        </p>
      </template>

      <template v-else>
        <span class="modal-icon"><History :size="24" /></span>
        <h2>{{ props.gameName ? `${props.gameName}${props.gameKey === 'avalon' ? ` · ${avalonModeLabel(activeGameMode)}` : difficultyLabel(activeGameMode)}战绩` : '我的全部战绩' }}</h2>
        <p>{{ props.gameKey === 'reaction' ? '记录每次三轮测试的平均值与单轮明细。' : props.gameKey === 'schulte' ? '记录每次 5×5 标准挑战的完成用时与点击准确率。' : props.gameKey === 'minesweeper' ? '不同难度分别统计通关时间，失败记录也会保留在战绩中。' : props.gameKey === 'hanoi' ? '记录每次通关的层数、步数与完成用时。' : '每款游戏独立记录胜负，对局详情绑定当前账号。' }}</p>

        <div
          v-if="props.gameKey === 'avalon' && !props.gameMode"
          class="stats-mode-tabs"
          role="group"
          aria-label="筛选阿瓦隆模式战绩"
        >
          <button
            type="button"
            :class="{ active: activeGameMode === 'standard' }"
            @click="activeGameMode = 'standard'"
          >
            标准模式
          </button>
          <button
            type="button"
            :class="{ active: activeGameMode === 'court_undercurrent' }"
            @click="activeGameMode = 'court_undercurrent'"
          >
            王庭暗流
          </button>
        </div>

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
            <template v-else-if="props.gameKey === 'schulte'">
              <div><strong>{{ summary.games }}</strong><span>挑战次数</span></div>
              <div><strong>{{ summary.bestMs === null ? '—' : formatDuration(summary.bestMs) }}</strong><span>历史最佳</span></div>
              <div><strong>{{ summary.averageMs === null ? '—' : formatDuration(summary.averageMs) }}</strong><span>平均用时</span></div>
            </template>
            <template v-else-if="props.gameKey === 'minesweeper'">
              <div><strong>{{ summary.games }}</strong><span>通关次数</span></div>
              <div><strong>{{ summary.bestMs === null ? '—' : formatDuration(summary.bestMs) }}</strong><span>最快通关</span></div>
              <div><strong>{{ summary.averageMs === null ? '—' : formatDuration(summary.averageMs) }}</strong><span>平均用时</span></div>
            </template>
            <template v-else-if="props.gameKey === 'hanoi'">
              <div><strong>{{ summary.games }}</strong><span>挑战次数</span></div>
              <div><strong>{{ summary.wins }}</strong><span>完成次数</span></div>
              <div><strong>{{ summary.winRate }}%</strong><span>完成率</span></div>
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
          <div
            v-if="
              props.gameKey === 'avalon' &&
              activeGameMode === 'court_undercurrent'
            "
            class="court-balance-summary"
          >
            <div>
              <strong>
                {{ percentage(summary.missionRouteGames, summary.games) }}
              </strong>
              <span>邪恶任务路线</span>
            </div>
            <div>
              <strong>
                {{
                  percentage(
                    summary.recruitmentHits,
                    summary.recruitmentAttempts,
                  )
                }}
              </strong>
              <span>授刃命中</span>
            </div>
            <div>
              <strong>
                {{
                  percentage(
                    summary.dissentingAssassinationHits,
                    summary.dissentingAssassinationAttempts,
                  )
                }}
              </strong>
              <span>心怀异念之臣刺杀命中</span>
            </div>
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
                <strong v-else-if="match.gameKey === 'schulte'">5×5 方格 · {{ formatDuration(match.scoreMs) }}</strong>
                <strong v-else-if="match.gameKey === 'minesweeper'">{{ difficultyLabel(match.gameMode) }}扫雷 · {{ match.scoreMs === null ? '踩中地雷' : formatDuration(match.scoreMs) }}</strong>
                <strong v-else-if="match.gameKey === 'hanoi'">{{ match.reason }}</strong>
                <strong v-else>{{ match.gameName }} · {{ roleLabel(match.role) }}</strong>
                <small v-if="match.gameKey === 'reaction'">{{ formatDate(match.endedAt) }} · 三轮测试</small>
                <small v-else-if="match.gameKey === 'schulte'">{{ formatDate(match.endedAt) }} · 标准挑战</small>
                <small v-else-if="match.gameKey === 'minesweeper'">{{ formatDate(match.endedAt) }} · {{ match.reason }}</small>
                <small v-else-if="match.gameKey === 'hanoi'">{{ formatDate(match.endedAt) }} · 单人益智挑战</small>
                <small v-else-if="match.gameKey === 'avalon'">
                  {{ formatDate(match.endedAt) }} · {{ avalonModeLabel(match.gameMode) }} ·
                  {{ match.playerCount }} 人 · 房间 {{ match.roomCode }}
                </small>
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
