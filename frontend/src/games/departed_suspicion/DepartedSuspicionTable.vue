<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  ArrowLeftRight,
  BriefcaseBusiness,
  Crosshair,
  Eye,
  PackageOpen,
  Search,
  SkipForward,
  Target,
  X,
} from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import UiButton from '../../components/ui/UiButton.vue'
import UiIconButton from '../../components/ui/UiIconButton.vue'
import GameHistoryPanel from '../shared/history/GameHistoryPanel.vue'
import IntegrityCardButton from './IntegrityCardButton.vue'
import type {
  EquipmentFieldView,
  EquipmentView,
  IntegrityView,
  PlayerBoardView,
  SuspicionGameView,
} from './types'

interface KnownIntegrityView {
  key: string
  board: PlayerBoardView
  card: IntegrityView
}

type ActionKind = 'investigate' | 'equip' | 'arm' | 'shoot' | 'extra_investigate'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const game = computed(() => props.snapshot.game as unknown as SuspicionGameView)
const historyEntries = computed(() => [...game.value.history].reverse().map((entry) => entry.text))
const actionKind = ref<ActionKind | null>(null)
const actionTargetSeat = ref<number | null>(null)
const actionCardIndex = ref<number | null>(null)
const endAimSeat = ref<number | null>(null)
const equipmentCard = ref<EquipmentView | null>(null)
const equipmentValues = ref<Record<string, boolean | number | null>>({})
const choiceTargetSeat = ref<number | null>(null)
const flashbangOrder = ref<Array<number | null>>([null, null, null])
const scannerOwnCardIndex = ref<number | null>(null)
const scannerTargetCardIndex = ref<number | null>(null)
const showCatalog = ref(false)
const showSelfTeam = ref(false)
const freshKnowledgeKeys = ref<string[]>([])

const playerById = computed(() => new Map(props.snapshot.players.map(player => [player.id, player])))
const selfBoard = computed(() => game.value.players.find(board => board.playerId === props.snapshot.self.id) ?? null)
const selfHiddenCards = computed(() => selfBoard.value?.cards.filter(card => !card.revealed) ?? [])
const livingBoards = computed(() => game.value.players.filter(board => board.alive))
const normalActionIds = computed(() => game.value.legal.normalActionIds)
const investigationTargetPlayerIds = computed(() => new Set(
  game.value.legal.investigationTargetPlayerIds,
))
const targetBoard = computed(() => game.value.players.find(board => board.seat === actionTargetSeat.value) ?? null)
const actionTargetBoards = computed(() => {
  const candidates = livingBoards.value.filter(board => board.playerId !== props.snapshot.self.id)
  if (actionKind.value === 'investigate' || actionKind.value === 'extra_investigate') {
    return candidates.filter(board => investigationTargetPlayerIds.value.has(board.playerId))
  }
  return candidates
})
const pendingTargetBoard = computed(() => game.value.players.find(board => board.playerId === game.value.pendingShot?.targetPlayerId) ?? null)
const canOperate = computed(() => !arcade.busy && !game.value.waiting)
const actionReady = computed(() => {
  if (actionKind.value === 'shoot') return true
  if (actionKind.value === 'equip') {
    return !selfHiddenCards.value.length || actionCardIndex.value !== null
  }
  if (actionKind.value === 'arm') {
    return actionTargetSeat.value !== null
      && (!selfHiddenCards.value.length || actionCardIndex.value !== null)
  }
  if (actionKind.value === 'investigate' || actionKind.value === 'extra_investigate') {
    return actionTargetSeat.value !== null && actionCardIndex.value !== null
  }
  return false
})
const responseCards = computed(() => game.value.equipmentHand.filter(card => game.value.legal.responseEquipmentIds.includes(card.id)))
const knownIntegrityCards = computed<KnownIntegrityView[]>(() => {
  const items: KnownIntegrityView[] = []
  for (const board of game.value.players) {
    for (const card of board.cards) {
      if (card.knowledge === 'known' && card.kind !== null && card.knowledgeKey !== null) {
        items.push({ key: card.knowledgeKey, board, card })
      }
    }
  }
  return items
})
const knownIntegrityByKey = computed(() => new Map(
  knownIntegrityCards.value.map(item => [item.key, item]),
))
const freshKnowledge = computed(() => freshKnowledgeKeys.value
  .map(key => knownIntegrityByKey.value.get(key))
  .filter((item): item is KnownIntegrityView => item !== undefined))
const equipmentOption = computed(() => (
  game.value.legal.equipmentOptions.find(option => option.cardId === equipmentCard.value?.id) ?? null
))
const choiceTargetPlayerIds = computed(() => new Set(game.value.choice?.targetPlayerIds ?? []))
const postShotTargetPlayerIds = computed(() => new Set(game.value.postShot?.targetPlayerIds ?? []))
const flashbangReady = computed(() => (
  flashbangOrder.value.every(index => index !== null)
  && new Set(flashbangOrder.value).size === 3
))

let previousKnowledgeKeys = new Set(knownIntegrityCards.value.map(item => item.key))

watch(
  () => knownIntegrityCards.value.map(item => item.key).sort().join('|'),
  () => {
    const currentItems = knownIntegrityCards.value
    const currentKeys = new Set(currentItems.map(item => item.key))
    const added = currentItems.filter(item => !previousKnowledgeKeys.has(item.key))
    if (added.length) freshKnowledgeKeys.value = added.map(item => item.key)
    previousKnowledgeKeys = currentKeys
  },
)

watch(
  () => [
    game.value.turnNumber,
    game.value.pendingAction?.action,
    game.value.waiting?.kind,
    game.value.pendingShot?.targetPlayerId,
    game.value.pendingShot?.scannerActivated,
  ],
  () => {
    actionKind.value = null
    actionTargetSeat.value = null
    actionCardIndex.value = null
    choiceTargetSeat.value = null
    flashbangOrder.value = [null, null, null]
    if (selfBoard.value?.aimPlayerId) {
      endAimSeat.value = game.value.players.find(board => board.playerId === selfBoard.value?.aimPlayerId)?.seat ?? null
    }
  },
)

function playerName(playerId: string | null | undefined): string {
  if (!playerId) return '未知玩家'
  return playerById.value.get(playerId)?.name ?? '未知玩家'
}

function teamLabel(team: 'honest' | 'crooked' | null): string {
  return team === 'honest' ? '正直阵营' : team === 'crooked' ? '腐败阵营' : '身份未明'
}

function chooseAction(kind: ActionKind) {
  actionKind.value = kind
  actionTargetSeat.value = null
  actionCardIndex.value = null
}

async function submitAction() {
  const kind = actionKind.value
  if (!kind || !actionReady.value) return
  if (kind === 'shoot') {
    await arcade.action('shoot')
    return
  }
  if (kind === 'equip') {
    const cardIndex = actionCardIndex.value
    await arcade.action('equip', cardIndex === null ? {} : { cardIndex })
    return
  }
  if (kind === 'arm') {
    const targetSeat = actionTargetSeat.value
    if (targetSeat === null) return
    const cardIndex = actionCardIndex.value
    await arcade.action(
      'arm',
      cardIndex === null ? { targetSeat } : { targetSeat, cardIndex },
    )
    return
  }
  const targetSeat = actionTargetSeat.value
  const cardIndex = actionCardIndex.value
  if (targetSeat === null || cardIndex === null) return
  await arcade.action(kind, {
    targetSeat,
    cardIndex,
  })
}

async function endTurn() {
  await arcade.action('end_turn', {
    ...(endAimSeat.value === null ? {} : { aimSeat: endAimSeat.value }),
  })
}

function openEquipment(card: EquipmentView) {
  equipmentCard.value = card
  const option = game.value.legal.equipmentOptions.find(item => item.cardId === card.id)
  equipmentValues.value = Object.fromEntries(
    (option?.fields ?? []).map(field => [field.key, field.default ?? null]),
  )
}

function closeEquipment() {
  equipmentCard.value = null
}

function fieldVisible(field: EquipmentFieldView): boolean {
  if (!field.visibleWhen) return true
  return equipmentValues.value[field.visibleWhen.field] === field.visibleWhen.equals
}

function fieldOptions(field: EquipmentFieldView) {
  const dependentValue = field.dependsOn ? equipmentValues.value[field.dependsOn] : null
  let options = field.dependsOn
    ? field.optionsByValue?.[String(dependentValue)] ?? []
    : field.options ?? []
  if (field.distinctFrom) {
    options = options.filter(option => option.value !== equipmentValues.value[field.distinctFrom!])
  }
  if (field.distinctLocationFrom) {
    const relation = field.distinctLocationFrom
    if (equipmentValues.value[relation.ownSeatField] === equipmentValues.value[relation.seatField]) {
      options = options.filter(option => option.value !== equipmentValues.value[relation.cardField])
    }
  }
  return options
}

function equipmentReady(): boolean {
  const option = equipmentOption.value
  if (!option) return false
  return option.fields.every((field) => {
    if (!fieldVisible(field) || !field.required) return true
    const value = equipmentValues.value[field.key]
    if (value === null || value === undefined) return false
    return field.kind === 'boolean' || fieldOptions(field).some(item => item.value === value)
  })
}

function equipmentPayload(card: EquipmentView): Record<string, unknown> {
  const payload: Record<string, unknown> = { cardId: card.id }
  for (const field of equipmentOption.value?.fields ?? []) {
    if (!fieldVisible(field)) continue
    const value = equipmentValues.value[field.key]
    if (value === null || value === undefined) continue
    const [root, child] = field.key.split('.', 2)
    if (child === undefined) {
      payload[root] = value
    } else {
      const nested = (payload[root] as Record<string, unknown> | undefined) ?? {}
      nested[child] = value
      payload[root] = nested
    }
  }
  return payload
}

async function playSelectedEquipment() {
  const card = equipmentCard.value
  if (!card || !equipmentReady()) return
  const succeeded = await arcade.actionWithResult('play_equipment', equipmentPayload(card))
  if (succeeded) closeEquipment()
}

async function chooseReveal(index: number) {
  await arcade.action('choose_reveal', { cardIndex: index })
}

async function chooseEquipment(cardId: string) {
  await arcade.action('choose_equipment', { cardId })
}

async function reorderIntegrity() {
  if (!flashbangReady.value) return
  await arcade.action('reorder_integrity', {
    cardOrder: [...flashbangOrder.value],
  })
}

async function chooseRedirect() {
  if (choiceTargetSeat.value === null) return
  await arcade.action('choose_redirect', { targetSeat: choiceTargetSeat.value })
}

async function passGrenade() {
  if (choiceTargetSeat.value === null) return
  await arcade.action('pass_grenade', { targetSeat: choiceTargetSeat.value })
}

async function useMobileDetonator() {
  if (choiceTargetSeat.value === null) return
  await arcade.action('use_mobile_detonator', { targetSeat: choiceTargetSeat.value })
}

async function useScanner() {
  await arcade.action('use_scanner')
}

async function resolveScanner(exchange: boolean) {
  if (!exchange) {
    await arcade.action('resolve_scanner')
    return
  }
  if (scannerOwnCardIndex.value === null || scannerTargetCardIndex.value === null) return
  await arcade.action('resolve_scanner', {
    ownCardIndex: scannerOwnCardIndex.value,
    targetCardIndex: scannerTargetCardIndex.value,
  })
}
</script>

<template>
  <section class="suspicion-table">
    <header class="suspicion-status surface">
      <div>
        <span class="status-kicker">第 {{ game.turnNumber }} 回合 · {{ game.direction === 'clockwise' ? '顺时针' : '逆时针' }}</span>
        <strong>{{ playerName(game.turnPlayerId) }}的回合</strong>
        <small v-if="game.currentPrompt">{{ game.currentPrompt.title }}</small>
        <small v-else>{{ game.actionDone ? '正常行动已完成，可使用装备或结束回合' : '请选择调查、获取装备、武装或射击' }}</small>
      </div>
      <div class="status-resources">
        <span><Target :size="16" />中央枪械 <b>{{ game.centralGuns }}</b></span>
        <button
          type="button"
          class="private-team-trigger"
          aria-label="按住查看我的阵营"
          @pointerdown.prevent="showSelfTeam = true"
          @pointerup.prevent="showSelfTeam = false"
          @pointercancel="showSelfTeam = false"
          @pointerleave="showSelfTeam = false"
          @keydown.space.prevent="showSelfTeam = true"
          @keyup.space.prevent="showSelfTeam = false"
          @keydown.enter.prevent="showSelfTeam = true"
          @keyup.enter.prevent="showSelfTeam = false"
          @contextmenu.prevent
        ><Eye :size="15" />{{ showSelfTeam || snapshot.phase === 'finished' ? teamLabel(game.selfTeam) : '按住查看阵营' }}</button>
      </div>
    </header>

    <section v-if="game.currentPrompt" class="current-prompt surface" :class="{ urgent: game.currentPrompt.isMyDecision }" aria-live="polite">
      <span class="panel-icon"><ArrowLeftRight :size="20" /></span>
      <div>
        <strong>{{ game.currentPrompt.title }}</strong>
        <small>{{ game.currentPrompt.detail }}</small>
      </div>
      <em>{{ game.currentPrompt.isMyDecision ? '轮到你处理' : `等待${playerName(game.currentPrompt.decisionPlayerId)}` }}</em>
    </section>

    <section v-if="freshKnowledge.length" class="private-result-notice surface" aria-live="polite">
      <Eye :size="20" />
      <div>
        <strong>获得 {{ freshKnowledge.length }} 条新底细</strong>
        <small>对应牌位已标记“已掌握”，按住那张牌即可私看。</small>
        <span v-for="item in freshKnowledge" :key="item.key">{{ playerName(item.board.playerId) }} · 第{{ item.card.index + 1 }}张</span>
      </div>
      <button type="button" aria-label="关闭新底细提示" @click="freshKnowledgeKeys = []"><X :size="17" /></button>
    </section>

    <section v-if="game.pendingAction?.isMyResponse" class="decision-panel surface urgent-panel">
      <div>
        <span class="panel-icon"><Crosshair :size="20" /></span>
        <div>
          <strong>装备响应</strong>
          <small>{{ game.currentPrompt?.title }}</small>
        </div>
      </div>
      <p>现在轮到你响应。装备会逐张完整结算；也可以直接放弃响应。</p>
      <div class="equipment-actions">
        <button v-for="card in responseCards" :key="card.id" type="button" @click="openEquipment(card)">{{ card.name }}</button>
        <UiButton compact @click="arcade.action('pass_response')"><SkipForward :size="16" />不响应</UiButton>
      </div>
    </section>

    <section v-if="game.pendingShot?.isMyDecision" class="decision-panel surface urgent-panel">
      <div><span class="panel-icon"><Eye :size="20" /></span><div><strong>指纹扫描器响应</strong><small>{{ playerName(game.pendingShot.targetPlayerId) }}的全部底细尚未公开，伤害尚未结算</small></div></div>
      <template v-if="game.pendingShot.scannerActivated">
        <label>用自己的底细交换
          <select v-model="scannerOwnCardIndex">
            <option :value="null">选择底细</option>
            <option v-for="card in selfBoard?.cards" :key="card.index" :value="card.index">第{{ card.index + 1 }}张</option>
          </select>
        </label>
        <label>取得目标的普通底细
          <select v-model="scannerTargetCardIndex">
            <option :value="null">选择正直/腐败底细</option>
            <option v-for="card in pendingTargetBoard?.cards.filter(item => item.kind === 'honest' || item.kind === 'crooked')" :key="card.index" :value="card.index">第{{ card.index + 1 }}张 · {{ card.label }}</option>
          </select>
        </label>
        <div class="decision-actions"><UiButton variant="primary" :disabled="scannerOwnCardIndex === null || scannerTargetCardIndex === null" @click="resolveScanner(true)">交换并继续结算</UiButton><button type="button" @click="resolveScanner(false)">不交换，继续结算</button></div>
      </template>
      <div v-else class="decision-actions"><UiButton variant="primary" @click="useScanner">使用并私看</UiButton><button type="button" @click="arcade.action('pass_scanner')">不使用</button></div>
    </section>

    <section v-if="game.choice?.isMyDecision" class="decision-panel surface">
      <div><span class="panel-icon"><ArrowLeftRight :size="20" /></span><div><strong>{{ game.currentPrompt?.title ?? '需要你的选择' }}</strong><small>{{ game.currentPrompt?.detail ?? '完成后对局会自动继续' }}</small></div></div>
      <div v-if="game.choice.kind === 'equipment_limit'" class="equipment-actions">
        <button v-for="card in game.choice.cards" :key="card.id" type="button" @click="chooseEquipment(card.id)">保留{{ card.name }}</button>
      </div>
      <div v-else-if="game.choice.kind === 'report_audit' || game.choice.kind === 'truth_serum'" class="card-choice-list">
        <button v-for="card in selfBoard?.cards.filter(item => !item.revealed)" :key="card.index" type="button" @click="chooseReveal(card.index)">公开第{{ card.index + 1 }}张</button>
      </div>
      <div v-else-if="game.choice.kind === 'flashbang'" class="decision-actions">
        <label v-for="position in 3" :key="position">新位置 {{ position }}
          <select v-model="flashbangOrder[position - 1]">
            <option :value="null">选择底细</option>
            <option v-for="card in game.choice.integrityCards" :key="card.index" :value="card.index">原第{{ card.index + 1 }}张 · {{ card.label }}{{ card.revealed ? '（公开）' : '（暗置）' }}</option>
          </select>
        </label>
        <UiButton variant="primary" :disabled="arcade.busy || !flashbangReady" @click="reorderIntegrity">确认新顺序</UiButton>
      </div>
      <div v-else-if="game.choice.kind === 'inspection_gloves'" class="decision-actions">
        <button v-if="selfBoard?.equipmentCount" type="button" @click="arcade.action('inspection_choice', { choice: 'discard_equipment' })">弃掉装备</button>
        <button v-if="selfBoard?.cards.some(card => !card.revealed)" type="button" @click="arcade.action('inspection_choice', { choice: 'show_integrity' })">向所有人展示暗牌</button>
      </div>
      <template v-else-if="game.choice.kind === 'classified_redirect' || game.choice.kind === 'grenade_pass'">
        <label>选择玩家
          <select v-model="choiceTargetSeat"><option :value="null">请选择</option><option v-for="board in livingBoards.filter(item => choiceTargetPlayerIds.has(item.playerId))" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select>
        </label>
        <UiButton v-if="game.choice.kind === 'classified_redirect'" variant="primary" @click="chooseRedirect">确认射击目标</UiButton>
        <UiButton v-else variant="primary" @click="passGrenade">传递手榴弹</UiButton>
      </template>
    </section>

    <section v-if="game.postShot?.isMyDecision" class="decision-panel surface urgent-panel">
      <div><span class="panel-icon"><Target :size="20" /></span><div><strong>移动引爆器</strong><small>本次中枪尚未产生胜者，你可以令另一人也中枪</small></div></div>
      <label>连锁目标
        <select v-model="choiceTargetSeat"><option :value="null">请选择</option><option v-for="board in livingBoards.filter(item => postShotTargetPlayerIds.has(item.playerId))" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select>
      </label>
      <div class="decision-actions"><UiButton variant="primary" @click="useMobileDetonator">引爆</UiButton><button type="button" @click="arcade.action('pass_mobile_detonator')">不引爆</button></div>
    </section>

    <section v-if="game.legal.canTakeNormalAction || game.legal.canTakeExtraInvestigation || game.legal.canEndTurn" class="turn-console surface">
      <header><div><strong>行动台</strong><small>{{ game.actionDone ? '可以结束回合' : selfBoard?.restrictedToEquip ? '拐杖复活限制：此后只能获取装备' : '行动声明后，系统按座位顺序询问装备响应' }}</small></div></header>
      <div v-if="game.legal.canTakeNormalAction" class="action-grid" :class="{ restricted: normalActionIds.length === 1 }">
        <button v-if="normalActionIds.includes('investigate')" type="button" :class="{ active: actionKind === 'investigate' }" @click="chooseAction('investigate')"><Search :size="18" /><span><strong>调查</strong><small>私看一张暗置底细</small></span></button>
        <button v-if="normalActionIds.includes('equip')" type="button" :class="{ active: actionKind === 'equip' }" @click="chooseAction('equip')"><PackageOpen :size="18" /><span><strong>获取装备</strong><small>抽一张装备；若有暗牌则公开一张</small></span></button>
        <button v-if="normalActionIds.includes('arm')" type="button" :class="{ active: actionKind === 'arm' }" @click="chooseAction('arm')"><Crosshair :size="18" /><span><strong>武装</strong><small>拿枪瞄准；若有暗牌则公开一张</small></span></button>
        <button v-if="normalActionIds.includes('shoot')" type="button" :class="{ active: actionKind === 'shoot' }" @click="chooseAction('shoot')"><Target :size="18" /><span><strong>射击</strong><small>只能射向当前瞄准目标</small></span></button>
      </div>
      <button v-if="game.legal.canTakeExtraInvestigation" type="button" class="extra-action" :class="{ active: actionKind === 'extra_investigate' }" @click="chooseAction('extra_investigate')"><Search :size="16" />钥匙 · 额外调查</button>

      <div v-if="actionKind" class="action-form">
        <label v-if="actionKind === 'investigate' || actionKind === 'extra_investigate' || actionKind === 'arm'">目标玩家
          <select v-model="actionTargetSeat"><option :value="null">请选择</option><option v-for="board in actionTargetBoards" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select>
        </label>
        <label v-if="actionKind === 'investigate' || actionKind === 'extra_investigate'">目标底细
          <select v-model="actionCardIndex"><option :value="null">选择暗置底细</option><option v-for="card in targetBoard?.cards.filter(item => !item.revealed)" :key="card.index" :value="card.index">第{{ card.index + 1 }}张</option></select>
        </label>
        <label v-if="(actionKind === 'equip' || actionKind === 'arm') && selfHiddenCards.length">公开自己的底细
          <select v-model="actionCardIndex"><option :value="null">选择暗置底细</option><option v-for="card in selfHiddenCards" :key="card.index" :value="card.index">第{{ card.index + 1 }}张</option></select>
        </label>
        <UiButton variant="primary" :disabled="!canOperate || !actionReady" @click="submitAction">声明{{ actionKind === 'extra_investigate' ? '额外调查' : actionKind === 'investigate' ? '调查' : actionKind === 'equip' ? '获取装备' : actionKind === 'arm' ? '武装' : '射击' }}</UiButton>
      </div>

      <div v-if="game.legal.canEndTurn" class="end-turn-row">
        <label v-if="selfBoard?.gun">回合末瞄准
          <select v-model="endAimSeat"><option v-for="board in livingBoards.filter(item => item.playerId !== snapshot.self.id)" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select>
        </label>
        <UiButton variant="primary" @click="endTurn">结束回合</UiButton>
      </div>
    </section>

    <section v-if="game.equipmentHand.length" class="equipment-hand surface">
      <header><div><strong>我的装备</strong><small>手牌上限1张 · 可用时机会由服务端校验</small></div><button type="button" @click="showCatalog = true">查看33张资料库</button></header>
      <article v-for="card in game.equipmentHand" :key="card.id">
        <span>{{ String(card.number).padStart(2, '0') }}</span>
        <div><strong>{{ card.name }}</strong><small>{{ card.englishName }} · {{ card.description }}</small></div>
        <button type="button" :disabled="!game.legal.playableEquipmentIds.includes(card.id)" @click="openEquipment(card)">使用</button>
      </article>
    </section>
    <button v-else type="button" class="catalog-trigger" @click="showCatalog = true"><BriefcaseBusiness :size="15" />查看33张装备资料库</button>

    <div class="investigation-board">
      <article
        v-for="board in game.players"
        :key="board.playerId"
        class="suspect-board surface"
        :class="{
          self: board.playerId === snapshot.self.id,
          eliminated: !board.alive,
          active: board.playerId === game.turnPlayerId,
        }"
      >
        <header>
          <span class="seat-badge">{{ board.seat + 1 }}</span>
          <div>
            <strong>{{ playerName(board.playerId) }}</strong>
            <small>{{ board.playerId === snapshot.self.id ? '你 · 按住底细私看' : board.alive ? '仍在调查中' : '已经出局' }}</small>
          </div>
          <span v-if="board.gun" class="gun-badge"><Crosshair :size="14" />瞄准{{ playerName(board.aimPlayerId) }}</span>
        </header>

        <div class="integrity-row">
          <IntegrityCardButton
            v-for="card in board.cards"
            :key="card.index"
            :card="card"
            :owner-name="playerName(board.playerId)"
            :finished="snapshot.phase === 'finished'"
          />
        </div>

        <footer>
          <span v-if="board.equipmentCount"><BriefcaseBusiness :size="13" />装备 {{ board.equipmentCount }}</span>
          <span v-for="effect in board.effects" :key="effect.id">{{ effect.name }}<template v-if="effect.grenadeStage"> · 第{{ effect.grenadeStage }}段</template></span>
          <span v-if="board.restrictedToEquip">仅可获取装备</span>
        </footer>
      </article>
    </div>

    <GameHistoryPanel
      class="history-panel surface"
      title="公开行动记录"
      :entries="historyEntries"
    />

    <div v-if="equipmentCard" class="suspicion-modal" @click.self="closeEquipment">
      <section class="surface" role="dialog" aria-modal="true">
        <UiIconButton compact class="suspicion-dialog-close" aria-label="关闭装备使用弹窗" @click="closeEquipment"><X :size="18" /></UiIconButton>
        <span class="equipment-number">{{ String(equipmentCard.number).padStart(2, '0') }}</span>
        <h2>{{ equipmentCard.name }}</h2>
        <p>{{ equipmentCard.englishName }} · {{ equipmentCard.description }}</p>

        <div v-if="equipmentOption?.fields.length" class="equipment-fields">
          <template v-for="field in equipmentOption.fields" :key="field.key">
            <label v-if="fieldVisible(field) && field.kind === 'boolean'" class="check-row">
              <input v-model="equipmentValues[field.key]" type="checkbox" />{{ field.label }}
            </label>
            <label v-else-if="fieldVisible(field)">{{ field.label }}
              <select v-model="equipmentValues[field.key]">
                <option :value="null">{{ field.required ? '请选择' : '不选择' }}</option>
                <option v-for="option in fieldOptions(field)" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
            </label>
          </template>
        </div>
        <p v-else>这张装备不需要额外选择，确认后立即结算。</p>
        <UiButton variant="primary" block :disabled="!equipmentReady()" @click="playSelectedEquipment">确认使用</UiButton>
      </section>
    </div>

    <div v-if="showCatalog" class="suspicion-modal" @click.self="showCatalog = false">
      <section class="surface catalog-modal" role="dialog" aria-modal="true">
        <UiIconButton compact class="suspicion-dialog-close" aria-label="关闭装备资料库" @click="showCatalog = false"><X :size="18" /></UiIconButton>
        <h2>33张装备资料库</h2>
        <p>{{ game.rulesNotice }}</p>
        <div class="catalog-list">
          <article v-for="card in game.equipmentCatalog" :key="card.id" :class="{ unavailable: card.available === false }">
            <span>{{ String(card.number).padStart(2, '0') }}</span><div><strong>{{ card.name }} <small>{{ card.englishName }}</small></strong><p>{{ card.description }}</p></div><em>{{ card.available === false ? card.expansion === 'undercover' ? '待完整卧底模式' : '未加入本局牌堆' : card.expansion === 'base' ? '基础' : '炸弹客/叛徒' }}</em>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.suspicion-table { width: 100%; display: grid; gap: 14px; --case-gold: #d2a65f; --case-red: #bb655e; --case-blue: #69a2b7; }
.suspicion-status { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 16px 18px; border-color: color-mix(in srgb, var(--case-gold) 28%, var(--line)); background: linear-gradient(110deg, color-mix(in srgb, var(--case-gold) 8%, var(--surface)), var(--surface)); }
.suspicion-status > div:first-child { min-width: 0; display: grid; gap: 3px; }.status-kicker { color: var(--case-gold); font-size: 9px; font-weight: 900; letter-spacing: .12em; }.suspicion-status strong { font-size: 20px; }.suspicion-status small { color: var(--muted); }
.status-resources { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 7px; }.status-resources span,.private-team-trigger { min-height: 34px; display: flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 999px; padding: 7px 10px; color: var(--text-soft); background: var(--surface-inset); font-size: 11px; font-weight: 800; }.status-resources b { color: var(--case-gold); }.private-team-trigger { color: var(--case-gold); cursor: pointer; touch-action: none; -webkit-user-select: none; user-select: none; }
.current-prompt { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; padding: 14px 15px; border-color: color-mix(in srgb, var(--case-gold) 34%, var(--line)); }.current-prompt.urgent { border-color: color-mix(in srgb, var(--case-red) 48%, var(--line)); background: linear-gradient(120deg, color-mix(in srgb, var(--case-red) 8%, var(--surface)), var(--surface)); }.current-prompt > div { min-width: 0; display: grid; gap: 3px; }.current-prompt small { color: var(--muted); }.current-prompt em { border-radius: 999px; padding: 6px 9px; color: var(--case-gold); background: color-mix(in srgb, var(--case-gold) 10%, var(--surface-inset)); font-size: 9px; font-style: normal; font-weight: 850; white-space: nowrap; }
.private-result-notice { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; padding: 13px 15px; border-color: color-mix(in srgb, var(--case-blue) 42%, var(--line)); background: linear-gradient(120deg, color-mix(in srgb, var(--case-blue) 8%, var(--surface)), var(--surface)); }.private-result-notice > svg { color: var(--case-blue); }.private-result-notice > div { min-width: 0; display: flex; align-items: center; flex-wrap: wrap; gap: 4px 8px; }.private-result-notice strong,.private-result-notice small { width: 100%; }.private-result-notice small { color: var(--muted); }.private-result-notice span { border-radius: 999px; padding: 4px 7px; color: var(--case-blue); background: color-mix(in srgb, var(--case-blue) 10%, var(--surface-inset)); font-size: 8px; font-weight: 800; }.private-result-notice button { width: 32px; aspect-ratio: 1; display: grid; place-items: center; border: 0; color: var(--muted); background: transparent; cursor: pointer; }
.investigation-board { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.suspect-board { min-width: 0; display: grid; gap: 11px; padding: 13px; transition: border-color .2s, opacity .2s; }.suspect-board.self { border-color: color-mix(in srgb, var(--case-gold) 42%, var(--line)); }.suspect-board.active { box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--case-gold) 23%, transparent); }.suspect-board.eliminated { opacity: .58; filter: grayscale(.35); }
.suspect-board > header { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 9px; }.seat-badge { width: 30px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 9px; color: var(--case-gold); background: color-mix(in srgb, var(--case-gold) 11%, var(--surface-inset)); font-size: 12px; font-weight: 900; }.suspect-board header div { min-width: 0; display: grid; }.suspect-board header strong,.suspect-board header small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.suspect-board header small { color: var(--muted); font-size: 9px; }.gun-badge { max-width: 120px; display: flex; align-items: center; gap: 4px; border-radius: 999px; padding: 5px 7px; color: #e58e86; background: color-mix(in srgb, var(--case-red) 13%, transparent); font-size: 8px; font-weight: 850; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.integrity-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }
.suspect-board > footer { min-height: 21px; display: flex; flex-wrap: wrap; gap: 5px; }.suspect-board > footer span { border-radius: 999px; padding: 4px 7px; color: var(--muted); background: var(--surface-inset); font-size: 8px; font-weight: 750; }
.decision-panel,.turn-console,.equipment-hand,.history-panel { padding: 15px; }.decision-panel { display: grid; gap: 12px; border-color: color-mix(in srgb, var(--case-gold) 30%, var(--line)); }.urgent-panel { border-color: color-mix(in srgb, var(--case-red) 40%, var(--line)); background: linear-gradient(120deg, color-mix(in srgb, var(--case-red) 6%, var(--surface)), var(--surface)); }.decision-panel > div:first-child { display: flex; align-items: center; gap: 10px; }.decision-panel > div:first-child > div { display: grid; }.decision-panel small,.decision-panel p { color: var(--muted); }.panel-icon { width: 38px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 11px; color: var(--case-gold); background: color-mix(in srgb, var(--case-gold) 12%, var(--surface-inset)); }.urgent-panel .panel-icon { color: #e18880; background: color-mix(in srgb, var(--case-red) 14%, var(--surface-inset)); }
.equipment-actions,.decision-actions,.card-choice-list { display: flex; flex-wrap: wrap; gap: 8px; }.equipment-actions button,.decision-actions button,.card-choice-list button,.catalog-trigger,.extra-action { min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid var(--line); border-radius: 9px; padding: 8px 11px; color: var(--text); background: var(--surface-inset); cursor: pointer; }
.turn-console { display: grid; gap: 12px; }.turn-console > header,.equipment-hand > header { display: flex; justify-content: space-between; gap: 10px; }.turn-console header div,.equipment-hand header div { min-width: 0; display: grid; }.turn-console small,.equipment-hand small { color: var(--muted); }.action-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; }.action-grid.restricted { grid-template-columns: 1fr; }.action-grid button { min-width: 0; min-height: 68px; display: flex; align-items: center; gap: 9px; border: 1px solid var(--line); border-radius: 10px; padding: 10px; color: var(--text-soft); background: var(--surface-inset); text-align: left; cursor: pointer; }.action-grid button.active,.extra-action.active { border-color: color-mix(in srgb, var(--case-gold) 55%, var(--line)); color: var(--case-gold); background: color-mix(in srgb, var(--case-gold) 9%, var(--surface-inset)); }.action-grid button span { min-width: 0; display: grid; }.action-grid button small { font-size: 8px; line-height: 1.35; }.extra-action { justify-self: start; }
.action-form,.end-turn-row { display: flex; align-items: end; flex-wrap: wrap; gap: 9px; border-top: 1px solid var(--line); padding-top: 12px; }.end-turn-row { justify-content: flex-end; }.action-form label,.end-turn-row label,.decision-panel label,.suspicion-modal label { min-width: 150px; display: grid; gap: 5px; color: var(--muted); font-size: 9px; font-weight: 800; }.action-form select,.end-turn-row select,.decision-panel select,.suspicion-modal select { min-height: 39px; border: 1px solid var(--line); border-radius: 8px; padding: 0 9px; color: var(--text); background: var(--surface-inset); }
.equipment-hand { display: grid; gap: 10px; }.equipment-hand > header button { border: 0; color: var(--case-gold); background: none; cursor: pointer; }.equipment-hand > article { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 10px; border: 1px solid var(--line); border-radius: 10px; padding: 10px; background: var(--surface-inset); }.equipment-hand article > span,.equipment-number { color: var(--case-gold); font-family: Georgia, serif; font-size: 18px; }.equipment-hand article div { min-width: 0; display: grid; }.equipment-hand article small { line-height: 1.45; overflow-wrap: anywhere; }.equipment-hand article button { border: 1px solid color-mix(in srgb, var(--case-gold) 35%, var(--line)); border-radius: 8px; padding: 7px 10px; color: var(--case-gold); background: transparent; cursor: pointer; }.equipment-hand article button:disabled { opacity: .35; cursor: not-allowed; }.catalog-trigger { justify-self: center; color: var(--case-gold); }
.history-panel { --game-history-accent: var(--case-gold); --game-history-max-height: 190px; }
.suspicion-modal { position: fixed; z-index: 120; inset: 0; display: grid; place-items: center; padding: 18px; background: rgba(2,7,6,.76); backdrop-filter: blur(10px); }.suspicion-modal > section { position: relative; width: min(100%, 510px); max-height: min(88vh, 760px); display: grid; gap: 12px; padding: 22px; overflow: auto; }.suspicion-modal h2 { margin: 0; }.suspicion-modal p { margin: 0; color: var(--muted); line-height: 1.55; }.suspicion-dialog-close { position: absolute; top: 10px; right: 10px; }.equipment-fields { display: grid; gap: 9px; }.check-row { display: flex !important; align-items: center; }.check-row input { accent-color: var(--case-gold); }.catalog-modal { width: min(100%, 760px) !important; }.catalog-list { display: grid; gap: 7px; }.catalog-list article { display: grid; grid-template-columns: 34px minmax(0, 1fr) auto; gap: 9px; border: 1px solid var(--line); border-radius: 9px; padding: 9px; background: var(--surface-inset); }.catalog-list article > span { color: var(--case-gold); font-family: Georgia, serif; }.catalog-list strong small { color: var(--muted); font-weight: 500; }.catalog-list p { margin-top: 3px; font-size: 9px; }.catalog-list em { color: var(--muted); font-size: 8px; font-style: normal; }.catalog-list .unavailable { opacity: .5; }
@media (max-width: 760px) {
  .suspicion-status { align-items: flex-start; flex-direction: column; }.status-resources { justify-content: flex-start; }
  .investigation-board { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; }.action-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .suspect-board { gap: 7px; padding: 9px; }.suspect-board > header { grid-template-columns: auto minmax(0, 1fr); gap: 6px; }.seat-badge { width: 25px; border-radius: 7px; font-size: 10px; }.gun-badge { grid-column: 1 / -1; max-width: 100%; justify-self: start; }.integrity-row { gap: 3px; }.suspect-board > footer { min-height: 17px; gap: 3px; }.suspect-board > footer span { padding: 3px 5px; font-size: 7px; }
}
@media (max-width: 480px) {
  .suspicion-table { gap: 10px; }.suspicion-status,.decision-panel,.turn-console,.equipment-hand,.history-panel { padding: 11px; }
  .current-prompt { grid-template-columns: auto minmax(0, 1fr); padding: 11px; }.current-prompt em { grid-column: 2; justify-self: start; }
  .status-resources { width: 100%; }.private-team-trigger { flex: 1; justify-content: center; }
  .action-grid button { min-height: 62px; padding: 8px; }.action-form,.end-turn-row { align-items: stretch; flex-direction: column; }.action-form label,.end-turn-row label,.action-form button,.end-turn-row button { width: 100%; }
  .suspicion-modal { padding: 8px; }.suspicion-modal > section { padding: 18px 14px; }
  .catalog-list article { grid-template-columns: 27px minmax(0, 1fr); }.catalog-list em { grid-column: 2; }
}
</style>
