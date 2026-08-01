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
  lastMove: { row: number; column: number } | null
  colors: Record<string, 'black' | 'white'>
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
  <section class="board-game-panel">
    <div class="turn-banner" :class="{ active: isMyTurn }">
      {{ isMyTurn ? '轮到你落子' : '等待对手落子' }}
      <small>你执{{ game.colors[snapshot.self.id] === 'black' ? '黑' : '白' }}</small>
    </div>
    <div
      class="gomoku-board"
      :style="{ '--board-size': game.boardSize }"
      aria-label="五子棋棋盘"
    >
      <template v-for="(row, rowIndex) in game.board" :key="rowIndex">
        <button
          v-for="(cell, columnIndex) in row"
          :key="`${rowIndex}-${columnIndex}`"
          type="button"
          class="board-point"
          :disabled="!isMyTurn || cell !== 0"
          :aria-label="`第 ${rowIndex + 1} 行第 ${columnIndex + 1} 列`"
          @click="place(rowIndex, columnIndex)"
        >
          <span
            v-if="cell"
            class="stone"
            :class="[
              cell === 1 ? 'black' : 'white',
              {
                latest:
                  game.lastMove?.row === rowIndex &&
                  game.lastMove?.column === columnIndex,
              },
            ]"
          />
        </button>
      </template>
    </div>
    <button
      v-if="snapshot.phase === 'playing'"
      type="button"
      class="arcade-danger-button"
      @click="arcade.action('resign')"
    >
      <Flag :size="17" />认输
    </button>
  </section>
</template>

<style scoped>
.board-game-panel { display: grid; gap: 16px; justify-items: center; }
.turn-banner { color: var(--muted); text-align: center; font-weight: 700; }
.turn-banner.active { color: var(--gold); }
.turn-banner small { display: block; margin-top: 3px; font-weight: 500; }
.gomoku-board {
  --board-size: 15;
  width: min(92vw, 650px);
  aspect-ratio: 1;
  padding: 14px;
  display: grid;
  grid-template-columns: repeat(var(--board-size), 1fr);
  border: 2px solid #8a5a2d;
  border-radius: 12px;
  background: #d3a35f;
  box-shadow: 0 20px 50px #0006, 0 0 0 1px color-mix(in srgb, var(--gold) 24%, transparent);
}
.board-point {
  position: relative;
  min-width: 0;
  padding: 0;
  border: 0;
  background:
    linear-gradient(#76502e, #76502e) center / 100% 1px no-repeat,
    linear-gradient(90deg, #76502e, #76502e) center / 1px 100% no-repeat;
}
.board-point:disabled { opacity: 1; }
.stone {
  position: absolute;
  inset: 8%;
  z-index: 2;
  border-radius: 50%;
  box-shadow: inset -2px -3px 5px #0005, 0 2px 4px #0007;
}
.stone.black { background: radial-gradient(circle at 35% 30%, #555, #080808 68%); }
.stone.white { background: radial-gradient(circle at 35% 30%, #fff, #d7d2c8 70%); }
.stone.latest::after {
  content: '';
  position: absolute;
  inset: 35%;
  border-radius: 50%;
  background: var(--gold);
}
</style>
