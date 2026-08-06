<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  ArrowLeftRight,
  BriefcaseBusiness,
  Crosshair,
  Eye,
  PackageOpen,
  Search,
  ShieldCheck,
  SkipForward,
  Target,
  X,
} from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

interface IntegrityView {
  index: number
  kind: 'honest' | 'crooked' | 'agent' | 'kingpin' | null
  label: string
  revealed: boolean
  knowledge: 'own' | 'public' | 'investigated' | 'hidden'
  wounded: boolean
}

interface EffectView {
  id: string
  name: string
  grenadeStage?: number | null
}

interface PlayerBoardView {
  playerId: string
  seat: number
  alive: boolean
  gun: boolean
  aimPlayerId: string | null
  equipmentCount: number
  effects: EffectView[]
  restrictedToEquip: boolean
  cards: IntegrityView[]
  team: 'honest' | 'crooked' | null
}

interface EquipmentView {
  id: string
  number: number
  name: string
  englishName: string
  expansion: string
  timing: string
  description: string
  persistent: boolean
  requiresCover: boolean
  available?: boolean
}

interface SuspicionGameView {
  turnPlayerId: string | null
  turnNumber: number
  direction: 'clockwise' | 'counterclockwise'
  centralGuns: number
  actionDone: boolean
  extraInvestigationDone: boolean
  players: PlayerBoardView[]
  selfTeam: 'honest' | 'crooked' | null
  equipmentHand: EquipmentView[]
  equipmentCatalog: EquipmentView[]
  pendingAction: null | {
    actorPlayerId: string
    action: string
    actionLabel: string
    targetPlayerId: string | null
    responsePlayerId: string | null
    isMyResponse: boolean
  }
  pendingShot: null | {
    targetPlayerId: string
    source: string
    scannerPlayerId: string | null
    isMyDecision: boolean
  }
  choice: null | {
    kind: string
    isMyDecision: boolean
    cards?: EquipmentView[]
    shooterPlayerId?: string
  }
  postShot: null | { kind: string; isMyDecision: boolean }
  waiting: null | { kind: string; playerId: string }
  legal: {
    canTakeNormalAction: boolean
    normalActionIds?: Array<'investigate' | 'equip' | 'arm' | 'shoot'>
    canTakeExtraInvestigation: boolean
    canEndTurn: boolean
    canRespond: boolean
    responseEquipmentIds: string[]
    playableEquipmentIds: string[]
  }
  history: Array<{ event: string; text: string }>
  rulesNotice: string
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const game = computed(() => props.snapshot.game as unknown as SuspicionGameView)
const actionKind = ref<'investigate' | 'equip' | 'arm' | 'shoot' | 'extra_investigate' | null>(null)
const actionTargetSeat = ref<number | null>(null)
const actionCardIndex = ref<number | null>(null)
const endAimSeat = ref<number | null>(null)
const equipmentCard = ref<EquipmentView | null>(null)
const equipmentTargetSeat = ref<number | null>(null)
const equipmentSecondSeat = ref<number | null>(null)
const equipmentCardIndex = ref<number | null>(null)
const equipmentSecondCardIndex = ref<number | null>(null)
const equipmentAimSeat = ref<number | null>(null)
const equipmentOwnCardIndex = ref<number | null>(null)
const returnFingerprint = ref(false)
const choiceTargetSeat = ref<number | null>(null)
const scannerOwnCardIndex = ref<number | null>(null)
const scannerTargetCardIndex = ref<number | null>(null)
const showCatalog = ref(false)

const playerById = computed(() => new Map(props.snapshot.players.map(player => [player.id, player])))
const selfBoard = computed(() => game.value.players.find(board => board.playerId === props.snapshot.self.id) ?? null)
const selfHiddenCards = computed(() => selfBoard.value?.cards.filter(card => !card.revealed) ?? [])
const livingBoards = computed(() => game.value.players.filter(board => board.alive))
const normalActionIds = computed(() => game.value.legal.normalActionIds
  ?? (selfBoard.value?.restrictedToEquip ? ['equip'] : ['investigate', 'equip', 'arm', 'shoot']))
const targetBoard = computed(() => game.value.players.find(board => board.seat === actionTargetSeat.value) ?? null)
const actionTargetBoards = computed(() => {
  const candidates = livingBoards.value.filter(board => board.playerId !== props.snapshot.self.id)
  if (actionKind.value === 'investigate' || actionKind.value === 'extra_investigate') {
    return candidates.filter(board =>
      board.cards.some(card => !card.revealed)
      && !board.effects.some(effect => effect.id === 'disguise'),
    )
  }
  return candidates
})
const equipmentTargetBoard = computed(() => game.value.players.find(board => board.seat === equipmentTargetSeat.value) ?? null)
const equipmentSecondBoard = computed(() => game.value.players.find(board => board.seat === equipmentSecondSeat.value) ?? null)
const pendingTargetBoard = computed(() => game.value.players.find(board => board.playerId === game.value.pendingShot?.targetPlayerId) ?? null)
const canOperate = computed(() => !arcade.busy && !game.value.waiting)
const responseCards = computed(() => game.value.equipmentHand.filter(card => game.value.legal.responseEquipmentIds.includes(card.id)))
const playableCards = computed(() => game.value.equipmentHand.filter(card => game.value.legal.playableEquipmentIds.includes(card.id)))
const singleTargetIds = new Set([
  'defibrillator', 'flashbang', 'k9_unit', 'planted_evidence', 'polygraph',
  'truth_serum', 'grenade', 'crutches', 'disguise', 'inspection_gloves', 'key',
  'med_kit', 'restraining_order', 'holster',
])
const targetCardIds = new Set(['fingerprint_kit', 'security_wand'])
const twoCardIds = new Set(['blackmail', 'fake_id', 'wiretap', 'sunglasses'])
const noInputIds = new Set([
  'coffee', 'report_audit', 'smoke_grenade', 'surveillance_camera',
  'concussion_grenade', 'helmet',
])

watch(
  () => [game.value.turnNumber, game.value.pendingAction?.action, game.value.waiting?.kind],
  () => {
    actionKind.value = null
    actionTargetSeat.value = null
    actionCardIndex.value = null
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

function cardClass(card: IntegrityView): string[] {
  return [
    card.kind ? `kind-${card.kind}` : 'kind-hidden',
    card.revealed ? 'revealed' : 'face-down',
    `knowledge-${card.knowledge}`,
  ]
}

function chooseAction(kind: typeof actionKind.value) {
  actionKind.value = kind
  actionTargetSeat.value = null
  actionCardIndex.value = null
}

async function submitAction() {
  const kind = actionKind.value
  if (!kind) return
  if (kind === 'shoot') {
    await arcade.action('shoot')
    return
  }
  if (kind === 'equip') {
    if (selfHiddenCards.value.length && actionCardIndex.value === null) return
    await arcade.action('equip', actionCardIndex.value === null ? {} : { cardIndex: actionCardIndex.value })
    return
  }
  if (kind === 'arm') {
    if (actionTargetSeat.value === null) return
    if (selfHiddenCards.value.length && actionCardIndex.value === null) return
    await arcade.action('arm', {
      ...(actionCardIndex.value === null ? {} : { cardIndex: actionCardIndex.value }),
      targetSeat: actionTargetSeat.value,
    })
    return
  }
  if (actionTargetSeat.value === null || actionCardIndex.value === null) return
  await arcade.action(kind, {
    targetSeat: actionTargetSeat.value,
    cardIndex: actionCardIndex.value,
  })
}

async function endTurn() {
  await arcade.action('end_turn', {
    ...(endAimSeat.value === null ? {} : { aimSeat: endAimSeat.value }),
  })
}

function openEquipment(card: EquipmentView) {
  equipmentCard.value = card
  equipmentTargetSeat.value = null
  equipmentSecondSeat.value = null
  equipmentCardIndex.value = null
  equipmentSecondCardIndex.value = null
  equipmentAimSeat.value = null
  equipmentOwnCardIndex.value = null
  returnFingerprint.value = false
}

function closeEquipment() {
  equipmentCard.value = null
}

function equipmentPayload(card: EquipmentView): Record<string, unknown> {
  const payload: Record<string, unknown> = { cardId: card.id }
  if (singleTargetIds.has(card.id)) payload.targetSeat = equipmentTargetSeat.value
  if (card.id === 'evidence_bag') {
    payload.ownerSeat = equipmentTargetSeat.value
    payload.recipientSeat = equipmentSecondSeat.value
  }
  if (card.id === 'taser') {
    payload.targetSeat = equipmentTargetSeat.value
    payload.aimSeat = equipmentAimSeat.value
  }
  if (card.id === 'classified_orders') payload.deciderSeat = equipmentTargetSeat.value
  if (twoCardIds.has(card.id)) {
    payload.firstSeat = equipmentTargetSeat.value
    payload.secondSeat = equipmentSecondSeat.value
    payload.firstCardIndex = equipmentCardIndex.value
    payload.secondCardIndex = equipmentSecondCardIndex.value
  }
  if (targetCardIds.has(card.id)) {
    payload.targetSeat = equipmentTargetSeat.value
    payload.cardIndex = equipmentCardIndex.value
  }
  if (card.id === 'fingerprint_kit') {
    payload.returnToHand = returnFingerprint.value
    if (returnFingerprint.value) payload.ownCardIndex = equipmentOwnCardIndex.value
  }
  if (card.id === 'security_wand' && equipmentOwnCardIndex.value !== null) {
    payload.ownCardIndex = equipmentOwnCardIndex.value
  }
  return payload
}

function equipmentReady(card: EquipmentView): boolean {
  if (noInputIds.has(card.id) || card.id === 'metal_detector') return true
  if (singleTargetIds.has(card.id)) return equipmentTargetSeat.value !== null
  if (card.id === 'evidence_bag') return equipmentTargetSeat.value !== null && equipmentSecondSeat.value !== null
  if (card.id === 'taser') return equipmentTargetSeat.value !== null && equipmentAimSeat.value !== null
  if (card.id === 'classified_orders') return equipmentTargetSeat.value !== null
  if (twoCardIds.has(card.id)) {
    return equipmentTargetSeat.value !== null
      && equipmentSecondSeat.value !== null
      && equipmentCardIndex.value !== null
      && equipmentSecondCardIndex.value !== null
  }
  if (targetCardIds.has(card.id)) {
    if (equipmentTargetSeat.value === null || equipmentCardIndex.value === null) return false
    if (card.id === 'fingerprint_kit' && returnFingerprint.value) return equipmentOwnCardIndex.value !== null
    return true
  }
  return true
}

async function playSelectedEquipment() {
  const card = equipmentCard.value
  if (!card || !equipmentReady(card)) return
  const succeeded = await arcade.actionWithResult('play_equipment', equipmentPayload(card))
  if (succeeded) closeEquipment()
}

async function chooseReveal(index: number) {
  await arcade.action('choose_reveal', { cardIndex: index })
}

async function chooseEquipment(cardId: string) {
  await arcade.action('choose_equipment', { cardId })
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
  if (scannerOwnCardIndex.value === null || scannerTargetCardIndex.value === null) return
  await arcade.action('use_scanner', {
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
        <small v-if="game.waiting">等待{{ playerName(game.waiting.playerId) }}处理{{ game.waiting.kind === 'equipment_response' ? '装备响应' : '当前选择' }}</small>
        <small v-else>{{ game.actionDone ? '正常行动已完成，可使用装备或结束回合' : '请选择调查、获取装备、武装或射击' }}</small>
      </div>
      <div class="status-resources">
        <span><Target :size="16" />中央枪械 <b>{{ game.centralGuns }}</b></span>
        <span :class="`team-${game.selfTeam}`"><ShieldCheck :size="16" />{{ teamLabel(game.selfTeam) }}</span>
      </div>
    </header>

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
            <small>{{ board.playerId === snapshot.self.id ? `${teamLabel(board.team)} · 你` : board.alive ? '仍在调查中' : '已经出局' }}</small>
          </div>
          <span v-if="board.gun" class="gun-badge"><Crosshair :size="14" />瞄准{{ playerName(board.aimPlayerId) }}</span>
        </header>

        <div class="integrity-row">
          <button
            v-for="card in board.cards"
            :key="card.index"
            type="button"
            class="integrity-card"
            :class="cardClass(card)"
            disabled
          >
            <span>{{ card.kind ? card.label : '?' }}</span>
            <small v-if="card.wounded">受伤</small>
            <small v-else-if="card.revealed">公开</small>
            <small v-else-if="card.knowledge === 'own'">仅你可见</small>
            <small v-else-if="card.knowledge === 'investigated'">你已调查</small>
            <small v-else>暗置</small>
          </button>
        </div>

        <footer>
          <span v-if="board.equipmentCount"><BriefcaseBusiness :size="13" />装备 {{ board.equipmentCount }}</span>
          <span v-for="effect in board.effects" :key="effect.id">{{ effect.name }}<template v-if="effect.grenadeStage"> · 第{{ effect.grenadeStage }}段</template></span>
          <span v-if="board.restrictedToEquip">仅可获取装备</span>
        </footer>
      </article>
    </div>

    <section v-if="game.pendingAction" class="decision-panel surface urgent-panel">
      <div>
        <span class="panel-icon"><Crosshair :size="20" /></span>
        <div>
          <strong>{{ playerName(game.pendingAction.actorPlayerId) }}宣布{{ game.pendingAction.actionLabel }}</strong>
          <small v-if="game.pendingAction.targetPlayerId">目标：{{ playerName(game.pendingAction.targetPlayerId) }}</small>
          <small v-else>等待装备响应后结算</small>
        </div>
      </div>
      <template v-if="game.pendingAction.isMyResponse">
        <p>现在轮到你响应。装备会逐张完整结算；也可以直接放弃响应。</p>
        <div class="equipment-actions">
          <button v-for="card in responseCards" :key="card.id" type="button" @click="openEquipment(card)">{{ card.name }}</button>
          <button type="button" class="secondary-button" @click="arcade.action('pass_response')"><SkipForward :size="16" />不响应</button>
        </div>
      </template>
      <p v-else>等待{{ playerName(game.pendingAction.responsePlayerId) }}决定是否使用装备。</p>
    </section>

    <section v-if="game.pendingShot?.isMyDecision" class="decision-panel surface urgent-panel">
      <div><span class="panel-icon"><Eye :size="20" /></span><div><strong>指纹扫描器响应</strong><small>{{ playerName(game.pendingShot.targetPlayerId) }}已公开全部底细，伤害尚未结算</small></div></div>
      <label>用自己的底细交换
        <select v-model="scannerOwnCardIndex">
          <option :value="null">选择底细</option>
          <option v-for="card in selfBoard?.cards" :key="card.index" :value="card.index">第{{ card.index + 1 }}张 · {{ card.label }}</option>
        </select>
      </label>
      <label>取得目标的普通底细
        <select v-model="scannerTargetCardIndex">
          <option :value="null">选择正直/腐败底细</option>
          <option v-for="card in pendingTargetBoard?.cards.filter(item => item.kind === 'honest' || item.kind === 'crooked')" :key="card.index" :value="card.index">第{{ card.index + 1 }}张 · {{ card.label }}</option>
        </select>
      </label>
      <div class="decision-actions"><button type="button" class="primary-button" @click="useScanner">交换并继续结算</button><button type="button" @click="arcade.action('pass_scanner')">不使用</button></div>
    </section>

    <section v-if="game.choice?.isMyDecision" class="decision-panel surface">
      <div><span class="panel-icon"><ArrowLeftRight :size="20" /></span><div><strong>需要你的选择</strong><small>完成后对局会自动继续</small></div></div>
      <div v-if="game.choice.kind === 'equipment_limit'" class="equipment-actions">
        <button v-for="card in game.choice.cards" :key="card.id" type="button" @click="chooseEquipment(card.id)">保留{{ card.name }}</button>
      </div>
      <div v-else-if="game.choice.kind === 'report_audit' || game.choice.kind === 'truth_serum'" class="card-choice-list">
        <button v-for="card in selfBoard?.cards.filter(item => !item.revealed)" :key="card.index" type="button" @click="chooseReveal(card.index)">公开第{{ card.index + 1 }}张 · {{ card.label }}</button>
      </div>
      <div v-else-if="game.choice.kind === 'inspection_gloves'" class="decision-actions">
        <button v-if="selfBoard?.equipmentCount" type="button" @click="arcade.action('inspection_choice', { choice: 'discard_equipment' })">弃掉装备</button>
        <button v-if="selfBoard?.cards.some(card => !card.revealed)" type="button" @click="arcade.action('inspection_choice', { choice: 'show_integrity' })">向所有人展示暗牌</button>
      </div>
      <template v-else-if="game.choice.kind === 'classified_redirect' || game.choice.kind === 'grenade_pass'">
        <label>选择玩家
          <select v-model="choiceTargetSeat"><option :value="null">请选择</option><option v-for="board in livingBoards.filter(item => game.choice?.kind === 'classified_redirect' ? item.playerId !== game.choice.shooterPlayerId : item.playerId !== snapshot.self.id)" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select>
        </label>
        <button v-if="game.choice.kind === 'classified_redirect'" type="button" class="primary-button" @click="chooseRedirect">确认射击目标</button>
        <button v-else type="button" class="primary-button" @click="passGrenade">传递手榴弹</button>
      </template>
    </section>

    <section v-if="game.postShot?.isMyDecision" class="decision-panel surface urgent-panel">
      <div><span class="panel-icon"><Target :size="20" /></span><div><strong>移动引爆器</strong><small>本次中枪尚未产生胜者，你可以令另一人也中枪</small></div></div>
      <label>连锁目标
        <select v-model="choiceTargetSeat"><option :value="null">请选择</option><option v-for="board in livingBoards.filter(item => item.playerId !== snapshot.self.id)" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select>
      </label>
      <div class="decision-actions"><button type="button" class="primary-button" @click="useMobileDetonator">引爆</button><button type="button" @click="arcade.action('pass_mobile_detonator')">保留不用</button></div>
    </section>

    <section v-if="game.legal.canTakeNormalAction || game.legal.canTakeExtraInvestigation || game.legal.canEndTurn" class="turn-console surface">
      <header><div><strong>行动台</strong><small>{{ game.actionDone ? '可以结束回合' : selfBoard?.restrictedToEquip ? '拐杖复活限制：此后只能获取装备' : '行动声明后，系统按座位顺序询问装备响应' }}</small></div></header>
      <div v-if="game.legal.canTakeNormalAction" class="action-grid" :class="{ restricted: normalActionIds.length === 1 }">
        <button v-if="normalActionIds.includes('investigate')" type="button" :class="{ active: actionKind === 'investigate' }" @click="chooseAction('investigate')"><Search :size="18" /><span><strong>调查</strong><small>私看一张暗置底细</small></span></button>
        <button v-if="normalActionIds.includes('equip')" type="button" :class="{ active: actionKind === 'equip' }" @click="chooseAction('equip')"><PackageOpen :size="18" /><span><strong>获取装备</strong><small>若有暗牌，公开一张后抽装备</small></span></button>
        <button v-if="normalActionIds.includes('arm')" type="button" :class="{ active: actionKind === 'arm' }" @click="chooseAction('arm')"><Crosshair :size="18" /><span><strong>武装</strong><small>若有暗牌先公开，再拿枪瞄准</small></span></button>
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
          <select v-model="actionCardIndex"><option :value="null">选择暗置底细</option><option v-for="card in selfHiddenCards" :key="card.index" :value="card.index">第{{ card.index + 1 }}张 · {{ card.label }}</option></select>
        </label>
        <p v-else-if="actionKind === 'equip' || actionKind === 'arm'" class="action-cost-note">底细已全部公开，本次无需再公开底细。</p>
        <button type="button" class="primary-button" :disabled="!canOperate" @click="submitAction">声明{{ actionKind === 'extra_investigate' ? '额外调查' : actionKind === 'investigate' ? '调查' : actionKind === 'equip' ? '获取装备' : actionKind === 'arm' ? '武装' : '射击' }}</button>
      </div>

      <div v-if="game.legal.canEndTurn" class="end-turn-row">
        <label v-if="selfBoard?.gun">回合末瞄准
          <select v-model="endAimSeat"><option v-for="board in livingBoards.filter(item => item.playerId !== snapshot.self.id)" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select>
        </label>
        <button type="button" class="primary-button" @click="endTurn">结束回合</button>
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

    <details class="history-panel surface">
      <summary>公开行动记录 · {{ game.history.length }}条</summary>
      <ol><li v-for="(entry, index) in [...game.history].reverse()" :key="`${entry.event}-${index}`">{{ entry.text }}</li></ol>
    </details>

    <div v-if="equipmentCard" class="suspicion-modal" @click.self="closeEquipment">
      <section class="surface" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭装备使用弹窗" @click="closeEquipment"><X :size="18" /></button>
        <span class="equipment-number">{{ String(equipmentCard.number).padStart(2, '0') }}</span>
        <h2>{{ equipmentCard.name }}</h2>
        <p>{{ equipmentCard.englishName }} · {{ equipmentCard.description }}</p>

        <label v-if="singleTargetIds.has(equipmentCard.id) || targetCardIds.has(equipmentCard.id) || equipmentCard.id === 'taser' || equipmentCard.id === 'classified_orders' || equipmentCard.id === 'evidence_bag'">{{ equipmentCard.id === 'classified_orders' ? '决定新目标的玩家' : equipmentCard.id === 'evidence_bag' ? '装备持有者' : '目标玩家' }}
          <select v-model="equipmentTargetSeat"><option :value="null">请选择</option><option v-for="board in game.players" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}{{ board.alive ? '' : ' · 已出局' }}</option></select>
        </label>
        <label v-if="equipmentCard.id === 'evidence_bag'">装备接收者
          <select v-model="equipmentSecondSeat"><option :value="null">请选择</option><option v-for="board in livingBoards" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select>
        </label>
        <label v-if="equipmentCard.id === 'taser'">新的瞄准目标
          <select v-model="equipmentAimSeat"><option :value="null">请选择</option><option v-for="board in livingBoards.filter(item => item.playerId !== snapshot.self.id)" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select>
        </label>

        <template v-if="twoCardIds.has(equipmentCard.id)">
          <div class="two-column-fields">
            <label>第一名玩家<select v-model="equipmentTargetSeat"><option :value="null">请选择</option><option v-for="board in game.players" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select></label>
            <label>第二名玩家<select v-model="equipmentSecondSeat"><option :value="null">请选择</option><option v-for="board in game.players" :key="board.seat" :value="board.seat">{{ playerName(board.playerId) }}</option></select></label>
            <label>第一张底细<select v-model="equipmentCardIndex"><option :value="null">请选择</option><option v-for="card in equipmentTargetBoard?.cards" :key="card.index" :value="card.index">第{{ card.index + 1 }}张 · {{ card.label }}</option></select></label>
            <label>第二张底细<select v-model="equipmentSecondCardIndex"><option :value="null">请选择</option><option v-for="card in equipmentSecondBoard?.cards" :key="card.index" :value="card.index">第{{ card.index + 1 }}张 · {{ card.label }}</option></select></label>
          </div>
        </template>
        <label v-if="targetCardIds.has(equipmentCard.id)">目标暗置底细
          <select v-model="equipmentCardIndex"><option :value="null">请选择</option><option v-for="card in equipmentTargetBoard?.cards.filter(item => !item.revealed)" :key="card.index" :value="card.index">第{{ card.index + 1 }}张</option></select>
        </label>
        <template v-if="equipmentCard.id === 'fingerprint_kit'">
          <label class="check-row"><input v-model="returnFingerprint" type="checkbox" />公开自己一张暗牌，让指纹工具回到手中</label>
          <label v-if="returnFingerprint">公开自己的底细<select v-model="equipmentOwnCardIndex"><option :value="null">请选择</option><option v-for="card in selfBoard?.cards.filter(item => !item.revealed)" :key="card.index" :value="card.index">第{{ card.index + 1 }}张 · {{ card.label }}</option></select></label>
        </template>
        <label v-if="equipmentCard.id === 'security_wand'">可选：重新暗置自己的公开底细
          <select v-model="equipmentOwnCardIndex"><option :value="null">不隐藏</option><option v-for="card in selfBoard?.cards.filter(item => item.revealed)" :key="card.index" :value="card.index">第{{ card.index + 1 }}张 · {{ card.label }}</option></select>
        </label>
        <button type="button" class="primary-button wide-button" :disabled="!equipmentReady(equipmentCard)" @click="playSelectedEquipment">确认使用</button>
      </section>
    </div>

    <div v-if="showCatalog" class="suspicion-modal" @click.self="showCatalog = false">
      <section class="surface catalog-modal" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="关闭装备资料库" @click="showCatalog = false"><X :size="18" /></button>
        <h2>33张装备资料库</h2>
        <p>{{ game.rulesNotice }}</p>
        <div class="catalog-list">
          <article v-for="card in game.equipmentCatalog" :key="card.id" :class="{ unavailable: card.available === false }">
            <span>{{ String(card.number).padStart(2, '0') }}</span><div><strong>{{ card.name }} <small>{{ card.englishName }}</small></strong><p>{{ card.description }}</p></div><em>{{ card.available === false ? '待卧底牌' : card.expansion === 'base' ? '基础' : card.expansion === 'bombers' ? '炸弹客/叛徒' : '卧底装备' }}</em>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.suspicion-table { width: 100%; display: grid; gap: 14px; --case-gold: #d2a65f; --case-red: #bb655e; --case-blue: #69a2b7; }
.suspicion-status { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 16px 18px; border-color: color-mix(in srgb, var(--case-gold) 28%, var(--line)); background: linear-gradient(110deg, color-mix(in srgb, var(--case-gold) 8%, var(--surface)), var(--surface)); }
.suspicion-status > div:first-child { display: grid; gap: 3px; }.status-kicker { color: var(--case-gold); font-size: 9px; font-weight: 900; letter-spacing: .12em; }.suspicion-status strong { font-size: 20px; }.suspicion-status small { color: var(--muted); }
.status-resources { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 7px; }.status-resources span { display: flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 999px; padding: 7px 10px; color: var(--text-soft); background: var(--surface-inset); font-size: 11px; font-weight: 800; }.status-resources b { color: var(--case-gold); }.status-resources .team-honest { color: #8cc1d1; }.status-resources .team-crooked { color: #dc8b83; }
.investigation-board { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.suspect-board { min-width: 0; display: grid; gap: 11px; padding: 13px; transition: border-color .2s, opacity .2s; }.suspect-board.self { border-color: color-mix(in srgb, var(--case-gold) 42%, var(--line)); }.suspect-board.active { box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--case-gold) 23%, transparent); }.suspect-board.eliminated { opacity: .58; filter: grayscale(.35); }
.suspect-board > header { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 9px; }.seat-badge { width: 30px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 9px; color: var(--case-gold); background: color-mix(in srgb, var(--case-gold) 11%, var(--surface-inset)); font-size: 12px; font-weight: 900; }.suspect-board header div { min-width: 0; display: grid; }.suspect-board header strong,.suspect-board header small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.suspect-board header small { color: var(--muted); font-size: 9px; }.gun-badge { max-width: 120px; display: flex; align-items: center; gap: 4px; border-radius: 999px; padding: 5px 7px; color: #e58e86; background: color-mix(in srgb, var(--case-red) 13%, transparent); font-size: 8px; font-weight: 850; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.integrity-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }.integrity-card { position: relative; min-width: 0; min-height: 94px; display: grid; place-items: center; align-content: center; gap: 8px; border: 1px solid var(--line); border-radius: 10px; color: var(--text); background: linear-gradient(145deg, var(--surface-elevated), var(--surface-inset)); overflow: hidden; opacity: 1; }.integrity-card::before { position: absolute; inset: 4px; border: 1px solid currentColor; border-radius: 7px; content: ''; opacity: .16; }.integrity-card span { position: relative; z-index: 1; font-family: "Songti SC", serif; font-size: 18px; font-weight: 900; }.integrity-card small { position: relative; z-index: 1; color: var(--muted); font-size: 8px; }.integrity-card.kind-honest { color: #8cc8d8; }.integrity-card.kind-crooked { color: #de8a82; }.integrity-card.kind-agent { color: #ddbc72; background: radial-gradient(circle at 50% 20%, rgba(221,188,114,.13), transparent 55%), var(--surface-inset); }.integrity-card.kind-kingpin { color: #d56d66; background: radial-gradient(circle at 50% 20%, rgba(213,109,102,.14), transparent 55%), var(--surface-inset); }.integrity-card.kind-hidden { color: #777d7a; background: repeating-linear-gradient(135deg, rgba(255,255,255,.025) 0 7px, transparent 7px 14px), var(--surface-inset); }.integrity-card.knowledge-investigated { border-style: dashed; }.integrity-card.revealed { box-shadow: inset 0 -3px 0 color-mix(in srgb, currentColor 40%, transparent); }
.suspect-board > footer { min-height: 21px; display: flex; flex-wrap: wrap; gap: 5px; }.suspect-board > footer span { border-radius: 999px; padding: 4px 7px; color: var(--muted); background: var(--surface-inset); font-size: 8px; font-weight: 750; }
.decision-panel,.turn-console,.equipment-hand,.history-panel { padding: 15px; }.decision-panel { display: grid; gap: 12px; border-color: color-mix(in srgb, var(--case-gold) 30%, var(--line)); }.urgent-panel { border-color: color-mix(in srgb, var(--case-red) 40%, var(--line)); background: linear-gradient(120deg, color-mix(in srgb, var(--case-red) 6%, var(--surface)), var(--surface)); }.decision-panel > div:first-child { display: flex; align-items: center; gap: 10px; }.decision-panel > div:first-child > div { display: grid; }.decision-panel small,.decision-panel p { color: var(--muted); }.panel-icon { width: 38px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 11px; color: var(--case-gold); background: color-mix(in srgb, var(--case-gold) 12%, var(--surface-inset)); }.urgent-panel .panel-icon { color: #e18880; background: color-mix(in srgb, var(--case-red) 14%, var(--surface-inset)); }
.equipment-actions,.decision-actions,.card-choice-list { display: flex; flex-wrap: wrap; gap: 8px; }.equipment-actions button,.decision-actions button,.card-choice-list button,.catalog-trigger,.extra-action { min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: 1px solid var(--line); border-radius: 9px; padding: 8px 11px; color: var(--text); background: var(--surface-inset); cursor: pointer; }
.turn-console { display: grid; gap: 12px; }.turn-console > header,.equipment-hand > header { display: flex; justify-content: space-between; gap: 10px; }.turn-console header div,.equipment-hand header div { display: grid; }.turn-console small,.equipment-hand small { color: var(--muted); }.action-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; }.action-grid.restricted { grid-template-columns: 1fr; }.action-grid button { min-width: 0; min-height: 68px; display: flex; align-items: center; gap: 9px; border: 1px solid var(--line); border-radius: 10px; padding: 10px; color: var(--text-soft); background: var(--surface-inset); text-align: left; cursor: pointer; }.action-grid button.active,.extra-action.active { border-color: color-mix(in srgb, var(--case-gold) 55%, var(--line)); color: var(--case-gold); background: color-mix(in srgb, var(--case-gold) 9%, var(--surface-inset)); }.action-grid button span { min-width: 0; display: grid; }.action-grid button small { font-size: 8px; line-height: 1.35; }.extra-action { justify-self: start; }
.action-form,.end-turn-row { display: flex; align-items: end; flex-wrap: wrap; gap: 9px; border-top: 1px solid var(--line); padding-top: 12px; }.end-turn-row { justify-content: flex-end; }.action-form label,.end-turn-row label,.decision-panel label,.suspicion-modal label { min-width: 150px; display: grid; gap: 5px; color: var(--muted); font-size: 9px; font-weight: 800; }.action-form select,.end-turn-row select,.decision-panel select,.suspicion-modal select { min-height: 39px; border: 1px solid var(--line); border-radius: 8px; padding: 0 9px; color: var(--text); background: var(--surface-inset); }
.action-cost-note { align-self: center; max-width: 250px; margin: 0; color: var(--muted); font-size: 10px; }
.equipment-hand { display: grid; gap: 10px; }.equipment-hand > header button { border: 0; color: var(--case-gold); background: none; cursor: pointer; }.equipment-hand > article { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 10px; border: 1px solid var(--line); border-radius: 10px; padding: 10px; background: var(--surface-inset); }.equipment-hand article > span,.equipment-number { color: var(--case-gold); font-family: Georgia, serif; font-size: 18px; }.equipment-hand article div { min-width: 0; display: grid; }.equipment-hand article small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.equipment-hand article button { border: 1px solid color-mix(in srgb, var(--case-gold) 35%, var(--line)); border-radius: 8px; padding: 7px 10px; color: var(--case-gold); background: transparent; cursor: pointer; }.equipment-hand article button:disabled { opacity: .35; cursor: not-allowed; }.catalog-trigger { justify-self: center; color: var(--case-gold); }
.history-panel summary { color: var(--muted); font-size: 10px; font-weight: 800; cursor: pointer; }.history-panel ol { max-height: 190px; margin: 12px 0 0; padding-left: 21px; overflow: auto; color: var(--text-soft); font-size: 10px; line-height: 1.8; }
.suspicion-modal { position: fixed; z-index: 120; inset: 0; display: grid; place-items: center; padding: 18px; background: rgba(2,7,6,.76); backdrop-filter: blur(10px); }.suspicion-modal > section { position: relative; width: min(100%, 510px); max-height: min(88vh, 760px); display: grid; gap: 12px; padding: 22px; overflow: auto; }.suspicion-modal h2 { margin: 0; }.suspicion-modal p { margin: 0; color: var(--muted); line-height: 1.55; }.modal-close { position: absolute; top: 10px; right: 10px; width: 34px; aspect-ratio: 1; display: grid; place-items: center; border: 0; color: var(--muted); background: transparent; cursor: pointer; }.two-column-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }.check-row { display: flex !important; align-items: center; }.check-row input { accent-color: var(--case-gold); }.catalog-modal { width: min(100%, 760px) !important; }.catalog-list { display: grid; gap: 7px; }.catalog-list article { display: grid; grid-template-columns: 34px minmax(0, 1fr) auto; gap: 9px; border: 1px solid var(--line); border-radius: 9px; padding: 9px; background: var(--surface-inset); }.catalog-list article > span { color: var(--case-gold); font-family: Georgia, serif; }.catalog-list strong small { color: var(--muted); font-weight: 500; }.catalog-list p { margin-top: 3px; font-size: 9px; }.catalog-list em { color: var(--muted); font-size: 8px; font-style: normal; }.catalog-list .unavailable { opacity: .5; }
@media (max-width: 760px) {
  .suspicion-status { align-items: flex-start; flex-direction: column; }.status-resources { justify-content: flex-start; }
  .investigation-board { grid-template-columns: 1fr; }.action-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 480px) {
  .suspicion-table { gap: 10px; }.suspicion-status,.suspect-board,.decision-panel,.turn-console,.equipment-hand,.history-panel { padding: 11px; }
  .integrity-card { min-height: 78px; }.integrity-card span { font-size: 15px; }.gun-badge { max-width: 90px; }
  .action-grid button { min-height: 62px; padding: 8px; }.action-form,.end-turn-row { align-items: stretch; flex-direction: column; }.action-form label,.end-turn-row label,.action-form button,.end-turn-row button { width: 100%; }
  .two-column-fields { grid-template-columns: 1fr; }.suspicion-modal { padding: 8px; }.suspicion-modal > section { padding: 18px 14px; }
  .catalog-list article { grid-template-columns: 27px minmax(0, 1fr); }.catalog-list em { grid-column: 2; }
}
</style>
