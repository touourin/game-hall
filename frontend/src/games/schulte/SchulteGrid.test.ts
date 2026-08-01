import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import SchulteGrid from './SchulteGrid.vue'

const GRID = [
  17, 4, 12, 23, 8,
  2, 19, 6, 15, 25,
  11, 1, 21, 9, 14,
  24, 7, 16, 3, 20,
  10, 22, 5, 18, 13,
]

function snapshot(
  game: Partial<{
    gridSize: number
    cellCount: number
    grid: number[]
    started: boolean
    nextNumber: number
    completedCount: number
    mistakes: number
    elapsedMs: number
    averageCellMs: number | null
    accuracy: number | null
    lastValue: number | null
    lastCorrect: boolean | null
  }> = {},
  phase: ArcadeSnapshot['phase'] = 'playing',
): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'GRID',
    gameKey: 'schulte' as ArcadeSnapshot['gameKey'],
    gameName: '舒尔特方格',
    options: {},
    phase,
    hostId: 'p1',
    self: { id: 'p1', name: '挑战者', seat: 0 },
    players: [
      { id: 'p1', name: '挑战者', seat: 0, connected: true, isHost: true },
    ],
    requiredPlayers: 1,
    roundNumber: 1,
    winner: phase === 'finished' ? 'completed' : null,
    winnerPlayerIds: phase === 'finished' ? ['p1'] : [],
    winReason: phase === 'finished' ? '5×5 舒尔特方格完成' : null,
    actions: {
      canStart: false,
      canRestart: phase === 'finished',
      canAct: phase === 'playing',
      canKickPlayers: false,
      canDissolve: false,
      canEditRules: false,
      canRequestUndo: false,
      canRequestDraw: false,
      canResolveRequest: false,
    },
    rematchReadyPlayerIds: [],
    request: null,
    chat: { maxLength: 300, messages: [] },
    game: {
      gridSize: 5,
      cellCount: 25,
      grid: [],
      started: false,
      nextNumber: 1,
      completedCount: 0,
      mistakes: 0,
      elapsedMs: 0,
      averageCellMs: null,
      accuracy: null,
      lastValue: null,
      lastCorrect: null,
      ...game,
    },
  }
}

describe('SchulteGrid', () => {
  it('keeps the grid hidden until the player explicitly begins', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(SchulteGrid, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    expect(wrapper.find('.schulte-grid').exists()).toBe(false)
    expect(wrapper.text()).toContain('按顺序找到 1–25')
    await wrapper.get('.schulte-intro .primary-button').trigger('click')

    expect(action).toHaveBeenCalledWith('begin')
  })

  it('updates the next number immediately and reports wrong taps', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const store = arcade as unknown as {
      rapidAction?: (
        actionName: string,
        payload?: Record<string, unknown>,
      ) => Promise<boolean>
    }
    store.rapidAction = undefined
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(SchulteGrid, {
      props: {
        snapshot: snapshot({ grid: GRID, started: true }),
      },
      global: { plugins: [pinia] },
    })

    await wrapper.get('[aria-label="数字 17"]').trigger('click')
    expect(wrapper.text()).toContain('应该点击 1')
    expect(action).toHaveBeenLastCalledWith('tap', { value: 17 })

    await wrapper.get('[aria-label="数字 1"]').trigger('click')
    await nextTick()
    expect(wrapper.text()).toContain('请寻找数字 2')
    expect(wrapper.get('[aria-label="数字 1，已完成"]').classes()).toContain('complete')
    expect(action).toHaveBeenLastCalledWith('tap', { value: 1 })
  })

  it('renders the verified result and offers another challenge', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const restartGame = vi.spyOn(arcade, 'restartGame').mockResolvedValue(true)
    const wrapper = mount(SchulteGrid, {
      props: {
        snapshot: snapshot({
          grid: GRID,
          started: true,
          nextNumber: 25,
          completedCount: 25,
          mistakes: 2,
          elapsedMs: 12_340,
          averageCellMs: 494,
          accuracy: 93,
          lastValue: 25,
          lastCorrect: true,
        }, 'finished'),
      },
      global: { plugins: [pinia] },
    })

    expect(wrapper.get('.schulte-result').text()).toContain('12.34')
    expect(wrapper.get('.schulte-result').text()).toContain('2错误点击')
    await wrapper.get('.schulte-result .primary-button').trigger('click')
    expect(restartGame).toHaveBeenCalledOnce()
  })
})
