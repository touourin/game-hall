<script setup lang="ts">
import { computed } from 'vue'
import {
  Building2,
  CircleDollarSign,
  Clock3,
  Crown,
  Dices,
  History,
  Landmark,
  MapPin,
} from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

interface MonopolyCell {
  index: number
  name: string
  type: 'start' | 'property' | 'chance' | 'tax' | 'jail' | 'bonus' | 'rest' | 'go_to_jail'
  icon?: string
  group?: string
  groupLabel?: string
  color?: string
  price?: number
  amount?: number
  baseRent?: number
  upgradeCost?: number
  ownerId: string | null
  ownerName: string | null
  ownerColor: string | null
  houses: number
  rent?: number
  groupComplete: boolean
}

interface MonopolyPlayer {
  id: string
  name: string
  seat: number
  color: string
  position: number
  cash: number
  netWorth: number
  propertyCount: number
  bankrupt: boolean
  jailedTurns: number
  isCurrent: boolean
}

interface MonopolyView {
  board: MonopolyCell[]
  players: MonopolyPlayer[]
  currentPlayerId: string | null
  turnStage: 'await_roll' | 'await_purchase' | 'await_upgrade'
  lastRoll: number[] | null
  currentRound: number
  maxRounds: number
  turnNumber: number
  passStartBonus: number
  lastEvent: string
  history: string[]
  currentCell: MonopolyCell | null
  standings: Array<{
    playerId: string
    name: string
    netWorth: number
    bankrupt: boolean
  }>
  legalActions: {
    canRoll: boolean
    canBuy: boolean
    canDecline: boolean
    canUpgrade: boolean
    canDeclineUpgrade: boolean
  }
}

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const game = computed(() => props.snapshot.game as unknown as MonopolyView)
const currentPlayer = computed(() => game.value.players.find(
  (player) => player.id === game.value.currentPlayerId,
) ?? null)
const selfPlayer = computed(() => game.value.players.find(
  (player) => player.id === props.snapshot.self.id,
) ?? null)
const isMyTurn = computed(() => game.value.currentPlayerId === props.snapshot.self.id)
const selfProperties = computed(() => game.value.board.filter(
  (cell) => cell.ownerId === props.snapshot.self.id,
))
const rollLabel = computed(() => (
  selfPlayer.value?.jailedTurns
    ? '服刑一回合'
    : '掷两颗骰子'
))
const turnPrompt = computed(() => {
  if (props.snapshot.phase === 'finished') return props.snapshot.winReason ?? '本局结束'
  if (!isMyTurn.value) return `等待 ${currentPlayer.value?.name ?? '其他玩家'} 行动`
  if (game.value.turnStage === 'await_purchase') return '发现一块无主地产'
  if (game.value.turnStage === 'await_upgrade') return '你的街区可以继续升级'
  if (selfPlayer.value?.jailedTurns) return '本回合需要在看守所停留'
  return '轮到你探索城市'
})

function formatMoney(value: number | undefined | null) {
  return `¥${new Intl.NumberFormat('zh-CN').format(value ?? 0)}`
}

function boardPosition(index: number) {
  if (index <= 6) return { gridRow: '7', gridColumn: String(7 - index) }
  if (index <= 12) return { gridRow: String(13 - index), gridColumn: '1' }
  if (index <= 18) return { gridRow: '1', gridColumn: String(index - 11) }
  return { gridRow: String(index - 17), gridColumn: '7' }
}

function tokensAt(position: number) {
  return game.value.players.filter(
    (player) => !player.bankrupt && player.position === position,
  )
}

function cellKind(cell: MonopolyCell) {
  if (cell.type === 'property') {
    if (cell.ownerId) return `租 ${formatMoney(cell.rent)}`
    return formatMoney(cell.price)
  }
  if (cell.type === 'tax') return `-${formatMoney(cell.amount)}`
  if (cell.type === 'bonus') return `+${formatMoney(cell.amount)}`
  if (cell.type === 'chance') return '抽取事件'
  if (cell.type === 'start') return `经过 +${formatMoney(game.value.passStartBonus)}`
  if (cell.type === 'go_to_jail') return '停留一回合'
  if (cell.type === 'jail') return '仅探访'
  return '安全停留'
}

function submit(action: string) {
  if (arcade.busy) return
  void arcade.action(action)
}
</script>

<template>
  <section class="monopoly-shell" aria-label="大富翁城市棋盘">
    <header class="fortune-player-bar">
      <article
        v-for="player in game.players"
        :key="player.id"
        :class="{
          active: player.isCurrent && snapshot.phase === 'playing',
          self: player.id === snapshot.self.id,
          bankrupt: player.bankrupt,
        }"
        :style="{ '--player-color': player.color }"
      >
        <span class="fortune-player-token">{{ player.seat + 1 }}</span>
        <div>
          <span><strong>{{ player.name }}</strong><small v-if="player.id === snapshot.self.id">你</small></span>
          <b>{{ formatMoney(player.cash) }}</b>
          <small>净资产 {{ formatMoney(player.netWorth) }} · {{ player.propertyCount }} 处地产</small>
        </div>
        <em v-if="player.bankrupt">已破产</em>
        <em v-else-if="player.jailedTurns">看守所</em>
        <em v-else-if="player.isCurrent">行动中</em>
      </article>
    </header>

    <div class="fortune-layout">
      <div class="fortune-board-wrap">
        <div class="fortune-board">
          <article
            v-for="cell in game.board"
            :key="cell.index"
            class="fortune-cell"
            :class="[
              `cell-${cell.type}`,
              {
                owned: Boolean(cell.ownerId),
                complete: cell.groupComplete,
                occupied: tokensAt(cell.index).length,
              },
            ]"
            :style="boardPosition(cell.index)"
            :aria-label="`${cell.name}，${cellKind(cell)}`"
          >
            <i
              v-if="cell.type === 'property'"
              class="property-band"
              :style="{ background: cell.color }"
            />
            <span v-if="cell.ownerColor" class="owner-mark" :style="{ background: cell.ownerColor }" />
            <span v-if="cell.icon" class="cell-icon">{{ cell.icon }}</span>
            <strong>{{ cell.name }}</strong>
            <small>{{ cellKind(cell) }}</small>
            <span v-if="cell.houses" class="house-row" :aria-label="`${cell.houses} 级地产`">
              <Building2 v-for="house in cell.houses" :key="house" :size="10" />
            </span>
            <div v-if="tokensAt(cell.index).length" class="cell-tokens">
              <b
                v-for="player in tokensAt(cell.index)"
                :key="player.id"
                :style="{ background: player.color }"
                :title="player.name"
              >{{ player.seat + 1 }}</b>
            </div>
          </article>

          <section class="fortune-center">
            <div class="fortune-round-meter">
              <span><Clock3 :size="13" /> 第 {{ game.currentRound }} / {{ game.maxRounds }} 回合</span>
              <i><b :style="{ width: `${Math.min(100, game.currentRound / game.maxRounds * 100)}%` }" /></i>
            </div>

            <div class="fortune-brand" aria-hidden="true">
              <small>CITY FORTUNE</small>
              <h2>大富翁</h2>
              <span><Landmark :size="13" /> 环城资产竞赛</span>
            </div>

            <div v-if="game.lastRoll" :key="`${game.turnNumber}-${game.lastRoll.join('-')}`" class="fortune-dice" aria-label="上一次骰子点数">
              <b>{{ game.lastRoll[0] }}</b>
              <i>+</i>
              <b>{{ game.lastRoll[1] }}</b>
              <em>= {{ (game.lastRoll[0] ?? 0) + (game.lastRoll[1] ?? 0) }}</em>
            </div>
            <div v-else class="fortune-dice waiting" aria-hidden="true">
              <b>·</b><i>+</i><b>·</b>
            </div>

            <div class="fortune-turn-copy" :class="{ mine: isMyTurn }">
              <small>{{ currentPlayer?.name ?? '本局' }}</small>
              <strong>{{ turnPrompt }}</strong>
              <p>{{ game.lastEvent }}</p>
            </div>

            <div v-if="snapshot.phase === 'playing'" class="fortune-actions">
              <button
                v-if="game.legalActions.canRoll"
                type="button"
                class="fortune-primary"
                :disabled="arcade.busy"
                @click="submit('roll')"
              >
                <Dices :size="18" /> {{ rollLabel }}
              </button>
              <template v-else-if="game.legalActions.canBuy && game.currentCell">
                <button type="button" class="fortune-primary" :disabled="arcade.busy" @click="submit('buy_property')">
                  <CircleDollarSign :size="17" /> 购买 {{ formatMoney(game.currentCell.price) }}
                </button>
                <button type="button" :disabled="arcade.busy" @click="submit('decline_property')">暂不购买</button>
              </template>
              <template v-else-if="game.legalActions.canUpgrade && game.currentCell">
                <button type="button" class="fortune-primary" :disabled="arcade.busy" @click="submit('upgrade_property')">
                  <Building2 :size="17" /> 升级 {{ formatMoney(game.currentCell.upgradeCost) }}
                </button>
                <button type="button" :disabled="arcade.busy" @click="submit('decline_upgrade')">保持现状</button>
              </template>
              <span v-else-if="snapshot.phase === 'playing'">
                <MapPin :size="14" /> {{ currentPlayer?.name }} 正在行动
              </span>
            </div>
          </section>
        </div>
      </div>

      <aside class="fortune-sidebar">
        <section class="fortune-ranking surface-inset">
          <header><span><Crown :size="16" />资产排名</span><small>实时净资产</small></header>
          <ol>
            <li
              v-for="(standing, index) in game.standings"
              :key="standing.playerId"
              :class="{ self: standing.playerId === snapshot.self.id, bankrupt: standing.bankrupt }"
            >
              <b>{{ index + 1 }}</b>
              <span><strong>{{ standing.name }}</strong><small>{{ standing.bankrupt ? '已破产' : '现金 + 地产 + 建设' }}</small></span>
              <em>{{ formatMoney(standing.netWorth) }}</em>
            </li>
          </ol>
        </section>

        <section class="fortune-ledger surface-inset">
          <header><span><Landmark :size="16" />我的产权</span><small>{{ selfProperties.length }} 处</small></header>
          <div v-if="selfProperties.length">
            <article v-for="cell in selfProperties" :key="cell.index">
              <i :style="{ background: cell.color }" />
              <span><strong>{{ cell.name }}</strong><small>{{ cell.groupLabel }} · {{ cell.houses ? `${cell.houses} 级` : cell.groupComplete ? '已成套' : '未建设' }}</small></span>
              <em>租 {{ formatMoney(cell.rent) }}</em>
            </article>
          </div>
          <p v-else>还没有地产。掷骰抵达无主街区后即可购买。</p>
        </section>

        <details class="fortune-history surface-inset" open>
          <summary><span><History :size="16" />城市动态</span><small>最近 {{ game.history.length }} 条</small></summary>
          <ol>
            <li v-for="(message, index) in game.history" :key="`${index}-${message}`">{{ message }}</li>
          </ol>
        </details>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.monopoly-shell { --fortune-gold: #e0b65e; --fortune-ink: #081714; display: grid; gap: 14px; }
.fortune-player-bar { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 8px; }
.fortune-player-bar article { --player-color: var(--fortune-gold); position: relative; min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 10px; border: 1px solid var(--line); border-radius: 14px; padding: 10px 11px; background: var(--surface-elevated); overflow: hidden; }
.fortune-player-bar article::before { position: absolute; top: 0; right: 0; left: 0; height: 2px; background: var(--player-color); content: ''; opacity: .58; }
.fortune-player-bar article.active { border-color: color-mix(in srgb, var(--player-color) 65%, var(--line)); box-shadow: 0 8px 25px color-mix(in srgb, var(--player-color) 12%, transparent); transform: translateY(-1px); }
.fortune-player-bar article.self { background: color-mix(in srgb, var(--player-color) 6%, var(--surface-elevated)); }
.fortune-player-bar article.bankrupt { filter: grayscale(.65); opacity: .55; }
.fortune-player-token { width: 34px; aspect-ratio: 1; display: grid; place-items: center; border: 2px solid color-mix(in srgb, var(--player-color) 70%, white); border-radius: 50%; color: #07110f; background: var(--player-color); box-shadow: 0 5px 12px color-mix(in srgb, var(--player-color) 23%, transparent); font-size: 12px; font-weight: 950; }
.fortune-player-bar article > div { min-width: 0; display: grid; gap: 2px; }.fortune-player-bar article > div > span { min-width: 0; display: flex; align-items: center; gap: 5px; }.fortune-player-bar article strong { overflow: hidden; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }.fortune-player-bar article > div > span small { border-radius: 999px; padding: 1px 4px; color: var(--player-color); background: color-mix(in srgb, var(--player-color) 12%, transparent); font-size: 7px; font-weight: 900; }.fortune-player-bar article > div > b { color: var(--player-color); font-size: 15px; }.fortune-player-bar article > div > small { overflow: hidden; color: var(--muted); font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }.fortune-player-bar article > em { border-radius: 999px; padding: 4px 6px; color: var(--player-color); background: color-mix(in srgb, var(--player-color) 10%, transparent); font-size: 8px; font-style: normal; font-weight: 850; white-space: nowrap; }

.fortune-layout { min-width: 0; display: grid; grid-template-columns: minmax(0, 1fr) 278px; align-items: start; gap: 13px; }
.fortune-board-wrap { min-width: 0; border: 1px solid color-mix(in srgb, var(--fortune-gold) 28%, var(--line)); border-radius: 20px; padding: clamp(5px, 1vw, 10px); background: radial-gradient(circle at 50% 48%, rgba(224,182,94,.12), transparent 43%), #07110f; box-shadow: inset 0 0 0 1px rgba(255,255,255,.025), 0 24px 50px rgba(0,0,0,.22); }
.fortune-board { position: relative; width: 100%; aspect-ratio: 1; display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); grid-template-rows: repeat(7, minmax(0, 1fr)); gap: 2px; border: 1px solid rgba(224,182,94,.2); border-radius: 13px; padding: 2px; background: rgba(224,182,94,.13); overflow: hidden; }
.fortune-cell { position: relative; min-width: 0; min-height: 0; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 2px; border: 1px solid rgba(255,255,255,.055); border-radius: 5px; padding: clamp(5px, .8vw, 9px) 3px 3px; color: #e9e6dc; background: linear-gradient(145deg, #12221e, #0b1714); text-align: center; overflow: hidden; }
.fortune-cell.complete { box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--fortune-gold) 35%, transparent); }.fortune-cell.occupied { background: linear-gradient(145deg, #1a302a, #0e1e1a); }
.property-band { position: absolute; top: 0; right: 0; left: 0; height: clamp(4px, .75vw, 8px); opacity: .92; }.owner-mark { position: absolute; z-index: 2; top: clamp(5px, .8vw, 9px); right: 3px; width: clamp(4px, .7vw, 7px); aspect-ratio: 1; border: 1px solid rgba(255,255,255,.72); border-radius: 50%; box-shadow: 0 0 5px currentColor; }
.fortune-cell > strong { width: 100%; overflow: hidden; font-size: clamp(6px, 1.05vw, 10px); line-height: 1.18; text-overflow: ellipsis; white-space: nowrap; }.fortune-cell > small { width: 100%; overflow: hidden; color: #9bac9f; font-size: clamp(4.5px, .78vw, 7px); line-height: 1.15; text-overflow: ellipsis; white-space: nowrap; }.cell-icon { color: var(--fortune-gold); font-family: Georgia, serif; font-size: clamp(11px, 2.1vw, 22px); font-weight: 850; line-height: .9; }.cell-chance { background: radial-gradient(circle at 50% 25%, rgba(92,185,159,.17), transparent 50%), #0b1815; }.cell-tax { background: radial-gradient(circle at 50% 25%, rgba(215,90,94,.14), transparent 50%), #171314; }.cell-bonus { background: radial-gradient(circle at 50% 25%, rgba(224,182,94,.18), transparent 50%), #17170f; }.cell-start { background: radial-gradient(circle at 50% 25%, rgba(98,196,150,.18), transparent 55%), #0b1913; }.cell-go_to_jail { background: radial-gradient(circle at 50% 25%, rgba(223,108,98,.18), transparent 55%), #1a1111; }
.house-row { display: flex; min-height: 10px; color: var(--fortune-gold); }.cell-tokens { position: absolute; z-index: 3; right: 2px; bottom: 2px; left: 2px; display: flex; justify-content: center; gap: 1px; }.cell-tokens b { width: clamp(10px, 1.55vw, 16px); aspect-ratio: 1; display: grid; place-items: center; border: 1px solid rgba(255,255,255,.76); border-radius: 50%; color: #06100d; box-shadow: 0 2px 6px rgba(0,0,0,.48); font-size: clamp(5px, .75vw, 7px); font-weight: 950; }

.fortune-center { grid-area: 2 / 2 / 7 / 7; min-width: 0; display: grid; justify-items: center; align-content: center; gap: clamp(5px, 1.1vw, 12px); border: 1px solid rgba(224,182,94,.22); border-radius: 12px; padding: clamp(8px, 2vw, 24px); background: radial-gradient(circle at 50% 36%, rgba(224,182,94,.14), transparent 37%), linear-gradient(145deg, #0c211c, #07130f); text-align: center; overflow: hidden; }
.fortune-round-meter { width: min(86%, 320px); display: grid; gap: 4px; }.fortune-round-meter > span { display: flex; align-items: center; justify-content: center; gap: 5px; color: #b8c5bd; font-size: clamp(7px, 1vw, 10px); font-weight: 800; letter-spacing: .05em; }.fortune-round-meter > i { height: 3px; border-radius: 999px; background: rgba(255,255,255,.08); overflow: hidden; }.fortune-round-meter > i b { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #7bcba4, var(--fortune-gold)); transition: width .3s ease; }
.fortune-brand { display: grid; justify-items: center; gap: 1px; }.fortune-brand small { color: var(--fortune-gold); font-size: clamp(6px, .85vw, 9px); font-weight: 900; letter-spacing: .24em; text-indent: .24em; }.fortune-brand h2 { margin: 0; color: #f2ead5; font-family: "Songti SC", "STSong", serif; font-size: clamp(22px, 4.8vw, 54px); font-weight: 650; letter-spacing: .1em; line-height: 1.05; text-indent: .1em; text-shadow: 0 8px 22px rgba(0,0,0,.4); }.fortune-brand span { display: flex; align-items: center; gap: 4px; color: #9eaea4; font-size: clamp(6px, .9vw, 9px); }
.fortune-dice { display: flex; align-items: center; gap: clamp(4px, .7vw, 8px); animation: dice-arrive .4s cubic-bezier(.2,.9,.2,1); }.fortune-dice b { width: clamp(24px, 4.1vw, 44px); aspect-ratio: 1; display: grid; place-items: center; border: 1px solid rgba(224,182,94,.55); border-radius: clamp(6px, 1vw, 10px); color: #172017; background: linear-gradient(145deg, #fff5d9, #d9b760); box-shadow: 0 7px 15px rgba(0,0,0,.35); font-family: Georgia, serif; font-size: clamp(13px, 2.3vw, 25px); }.fortune-dice i { color: #778a7e; font-size: clamp(8px, 1.4vw, 14px); font-style: normal; }.fortune-dice em { color: var(--fortune-gold); font-size: clamp(8px, 1.4vw, 14px); font-style: normal; font-weight: 900; }.fortune-dice.waiting { opacity: .35; animation: none; }.fortune-dice.waiting b { color: #c6b476; background: #17231e; }
.fortune-turn-copy { width: min(92%, 410px); display: grid; gap: 3px; }.fortune-turn-copy > small { color: var(--fortune-gold); font-size: clamp(6px, .9vw, 9px); font-weight: 850; }.fortune-turn-copy > strong { font-size: clamp(9px, 1.55vw, 16px); }.fortune-turn-copy > p { min-height: 2.6em; margin: 1px 0 0; color: #9eada4; font-size: clamp(6px, 1vw, 10px); line-height: 1.35; }.fortune-turn-copy.mine > strong { color: #f0d391; }
.fortune-actions { min-height: clamp(29px, 4.4vw, 45px); display: flex; align-items: center; justify-content: center; gap: 6px; }.fortune-actions button { min-height: clamp(28px, 4vw, 42px); display: inline-flex; align-items: center; justify-content: center; gap: 5px; border: 1px solid rgba(224,182,94,.3); border-radius: 10px; padding: 0 clamp(7px, 1.3vw, 14px); color: #d8ded9; background: rgba(255,255,255,.045); font-size: clamp(7px, 1vw, 10px); font-weight: 850; cursor: pointer; }.fortune-actions .fortune-primary { border-color: #dab258; color: #172016; background: linear-gradient(145deg, #f2d183, #c89539); box-shadow: 0 7px 18px rgba(203,151,55,.2); }.fortune-actions button:disabled { cursor: not-allowed; opacity: .55; }.fortune-actions > span { display: flex; align-items: center; gap: 5px; color: #94a69b; font-size: clamp(7px, 1vw, 10px); }

.fortune-sidebar { display: grid; gap: 10px; }.surface-inset { border: 1px solid var(--line); border-radius: 14px; padding: 12px; background: var(--surface-inset); }.fortune-sidebar section > header,.fortune-history summary { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; list-style: none; }.fortune-sidebar header > span,.fortune-history summary > span { display: flex; align-items: center; gap: 6px; color: var(--fortune-gold); font-size: 11px; font-weight: 850; }.fortune-sidebar header > small,.fortune-history summary > small { color: var(--muted); font-size: 8px; }
.fortune-ranking ol,.fortune-history ol { display: grid; gap: 5px; margin: 0; padding: 0; list-style: none; }.fortune-ranking li { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 8px; border-radius: 9px; padding: 7px; background: color-mix(in srgb, var(--surface-elevated) 68%, transparent); }.fortune-ranking li.self { box-shadow: inset 0 0 0 1px rgba(224,182,94,.26); }.fortune-ranking li.bankrupt { opacity: .48; }.fortune-ranking li > b { width: 23px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 50%; color: var(--fortune-gold); background: rgba(224,182,94,.1); font-size: 9px; }.fortune-ranking li > span { min-width: 0; display: grid; gap: 1px; }.fortune-ranking li strong { overflow: hidden; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }.fortune-ranking li small { color: var(--muted); font-size: 7px; }.fortune-ranking li em { color: var(--text-soft); font-size: 9px; font-style: normal; font-weight: 850; }
.fortune-ledger > div { max-height: 190px; display: grid; gap: 5px; overflow-y: auto; }.fortune-ledger article { min-width: 0; display: grid; grid-template-columns: 4px minmax(0, 1fr) auto; align-items: center; gap: 7px; border-radius: 8px; padding: 7px; background: color-mix(in srgb, var(--surface-elevated) 68%, transparent); }.fortune-ledger article > i { width: 4px; height: 100%; min-height: 27px; border-radius: 4px; }.fortune-ledger article > span { min-width: 0; display: grid; gap: 2px; }.fortune-ledger article strong { font-size: 9px; }.fortune-ledger article small { color: var(--muted); font-size: 7px; }.fortune-ledger article em { color: var(--fortune-gold); font-size: 8px; font-style: normal; }.fortune-ledger > p { margin: 0; color: var(--muted); font-size: 9px; line-height: 1.55; }
.fortune-history summary { margin: 0; cursor: pointer; }.fortune-history summary::-webkit-details-marker { display: none; }.fortune-history[open] summary { margin-bottom: 9px; }.fortune-history ol { max-height: 214px; overflow-y: auto; counter-reset: event; }.fortune-history li { position: relative; border-left: 1px solid rgba(224,182,94,.22); padding: 3px 0 3px 10px; color: var(--text-soft); font-size: 8px; line-height: 1.45; }.fortune-history li::before { position: absolute; top: 7px; left: -3px; width: 5px; aspect-ratio: 1; border-radius: 50%; background: var(--fortune-gold); content: ''; }

@keyframes dice-arrive { from { opacity: 0; transform: translateY(-8px) rotate(-4deg) scale(.85); } to { opacity: 1; transform: none; } }
@media (hover: hover) { .fortune-actions button:hover:not(:disabled) { border-color: var(--fortune-gold); transform: translateY(-1px); } }
@media (max-width: 900px) {
  .fortune-layout { grid-template-columns: 1fr; }.fortune-sidebar { grid-template-columns: repeat(2, minmax(0, 1fr)); }.fortune-history { grid-column: 1 / -1; }.fortune-ledger > div,.fortune-history ol { max-height: 150px; }
}
@media (max-width: 600px) {
  .monopoly-shell { gap: 9px; }.fortune-player-bar { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 5px; }.fortune-player-bar article { grid-template-columns: auto minmax(0, 1fr); gap: 6px; border-radius: 10px; padding: 7px; }.fortune-player-token { width: 26px; }.fortune-player-bar article > em { position: absolute; top: 5px; right: 5px; padding: 2px 4px; font-size: 6px; }.fortune-player-bar article > div > b { font-size: 11px; }.fortune-player-bar article > div > small { font-size: 6px; }
  .fortune-board-wrap { margin-right: -7px; margin-left: -7px; border-radius: 12px; padding: 3px; }.fortune-board { gap: 1px; border-radius: 8px; padding: 1px; }.fortune-cell { gap: 1px; border-radius: 3px; padding-right: 1px; padding-left: 1px; }.fortune-cell > strong { font-size: clamp(5px, 1.7vw, 7px); }.fortune-cell > small { font-size: clamp(4px, 1.35vw, 5.5px); }.cell-icon { font-size: clamp(9px, 3.4vw, 14px); }.house-row svg { width: 6px; }.owner-mark { right: 1px; }.fortune-center { gap: 4px; border-radius: 6px; padding: 5px; }.fortune-brand span { display: none; }.fortune-turn-copy > p { min-height: 0; display: -webkit-box; overflow: hidden; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }.fortune-actions button { border-radius: 7px; }.fortune-round-meter > i { height: 2px; }
  .fortune-sidebar { grid-template-columns: 1fr; }.fortune-history { grid-column: auto; }.fortune-ranking ol { grid-template-columns: repeat(2, minmax(0, 1fr)); }.fortune-ranking li { gap: 5px; }.fortune-ranking li em { display: none; }
}
@media (prefers-reduced-motion: reduce) { .fortune-dice { animation: none; } }
</style>
