<script setup lang="ts">
import { computed } from 'vue'
import { Flag } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const game = computed(() => props.snapshot.game as {
  boardSize: number
  board: number[][]
  turnPlayerId: string | null
  colors: Record<string, 'black' | 'white'>
  captures: { black: number; white: number }
  komi: number
  lastMove: { row?: number; column?: number; pass: boolean } | null
  score: { black: number; white: number } | null
})
const isMyTurn = computed(
  () => game.value.turnPlayerId === props.snapshot.self.id,
)

function place(row: number, column: number) {
  if (!isMyTurn.value || game.value.board[row]?.[column]) return
  void arcade.action('place', { row, column })
}
</script>

<template>
  <section class="go-panel">
    <div class="go-status">
      <strong>{{ isMyTurn ? '轮到你落子' : '等待对手落子' }}</strong>
      <span>你执{{ game.colors[snapshot.self.id] === 'black' ? '黑' : '白' }}</span>
      <span>提子 黑 {{ game.captures.black }} · 白 {{ game.captures.white }}</span>
      <span>贴目 {{ game.komi }}</span>
    </div>
    <div
      class="go-board"
      :style="{ '--board-size': game.boardSize }"
      aria-label="十九路围棋棋盘"
    >
      <template v-for="(row, rowIndex) in game.board" :key="rowIndex">
        <button
          v-for="(cell, columnIndex) in row"
          :key="`${rowIndex}-${columnIndex}`"
          type="button"
          class="go-point"
          :disabled="!isMyTurn || cell !== 0"
          @click="place(rowIndex, columnIndex)"
        >
          <span
            v-if="cell"
            class="go-stone"
            :class="[
              cell === 1 ? 'black' : 'white',
              {
                latest:
                  !game.lastMove?.pass &&
                  game.lastMove?.row === rowIndex &&
                  game.lastMove?.column === columnIndex,
              },
            ]"
          />
        </button>
      </template>
    </div>
    <div v-if="snapshot.phase === 'playing'" class="inline-actions">
      <button type="button" :disabled="!isMyTurn" @click="arcade.action('pass')">
        停一手
      </button>
      <button type="button" class="arcade-danger-button" @click="arcade.action('resign')">
        <Flag :size="17" />认输
      </button>
    </div>
    <p v-if="game.score" class="score-line">
      终局数子：黑 {{ game.score.black }} · 白 {{ game.score.white }}
    </p>
  </section>
</template>

<style scoped>
.go-panel { display: grid; gap: 14px; justify-items: center; }
.go-status { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 16px; color: var(--muted); }
.go-status strong { color: var(--gold); }
.go-board {
  --board-size: 19;
  width: min(94vw, 700px);
  aspect-ratio: 1;
  padding: 11px;
  display: grid;
  grid-template-columns: repeat(var(--board-size), 1fr);
  border: 2px solid #7c4e25;
  border-radius: 8px;
  background: #d5a45d;
  box-shadow: 0 20px 50px #0006, 0 0 0 1px color-mix(in srgb, var(--gold) 24%, transparent);
}
.go-point {
  position: relative;
  min-width: 0;
  padding: 0;
  border: 0;
  background:
    linear-gradient(#654321, #654321) center / 100% 1px no-repeat,
    linear-gradient(90deg, #654321, #654321) center / 1px 100% no-repeat;
}
.go-point:disabled { opacity: 1; }
.go-stone { position: absolute; inset: 3%; z-index: 2; border-radius: 50%; box-shadow: inset -2px -3px 4px #0005, 0 1px 3px #0008; }
.go-stone.black { background: radial-gradient(circle at 35% 30%, #555, #050505 68%); }
.go-stone.white { background: radial-gradient(circle at 35% 30%, white, #d7d2c8 72%); }
.go-stone.latest::after { content: ''; position: absolute; inset: 37%; border-radius: 50%; background: var(--gold); }
.inline-actions { display: flex; gap: 10px; }
.inline-actions button:not(.arcade-danger-button) { border: 1px solid var(--line); border-radius: 12px; padding: 10px 18px; color: var(--text); background: var(--surface); }
.score-line { color: var(--gold); }
</style>
