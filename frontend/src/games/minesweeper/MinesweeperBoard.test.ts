import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import MinesweeperBoard from './MinesweeperBoard.vue'

function snapshot(
  phase: ArcadeSnapshot['phase'] = 'playing',
  overrides: Record<string, unknown> = {},
): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'MINE',
    gameKey: 'minesweeper' as ArcadeSnapshot['gameKey'],
    gameName: '扫雷',
    options: { difficulty: 'beginner' },
    phase,
    hostId: 'p1',
    self: { id: 'p1', name: '排雷员', seat: 0 },
    players: [
      { id: 'p1', name: '排雷员', seat: 0, connected: true, isHost: true },
    ],
    requiredPlayers: 1,
    roundNumber: 1,
    winner: phase === 'finished' ? 'completed' : null,
    winnerPlayerIds: phase === 'finished' ? ['p1'] : [],
    winReason: phase === 'finished' ? '初级扫雷完成，用时 12.3 秒' : null,
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
      difficulty: 'beginner',
      difficultyLabel: '初级',
      rows: 9,
      columns: 9,
      mineCount: 10,
      cells: Array.from({ length: 81 }, () => ({ state: 'hidden', adjacent: null })),
      started: false,
      revealedCount: 0,
      safeCellCount: 71,
      flaggedCount: 0,
      remainingMines: 10,
      elapsedMs: 0,
      explodedIndex: null,
      firstMoveSafe: true,
      ...overrides,
    },
  }
}

describe('MinesweeperBoard', () => {
  it('renders the classic beginner board and opens a cell', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const rapidAction = vi.spyOn(arcade, 'rapidAction').mockResolvedValue(true)
    const wrapper = mount(MinesweeperBoard, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    expect(wrapper.findAll('.mine-cell')).toHaveLength(81)
    expect(wrapper.text()).toContain('第一次翻开一定安全')
    await wrapper.get('[aria-label="第 1 行第 1 列，未翻开"]').trigger('click')

    expect(rapidAction).toHaveBeenCalledWith('open', { index: 0 })
  })

  it('supports explicit flag mode for touch devices', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const rapidAction = vi.spyOn(arcade, 'rapidAction').mockResolvedValue(true)
    const wrapper = mount(MinesweeperBoard, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    await wrapper.findAll('.minesweeper-mode button')[1]!.trigger('click')
    await wrapper.get('[aria-label="第 1 行第 2 列，未翻开"]').trigger('click')

    expect(rapidAction).toHaveBeenCalledWith('toggle_flag', { index: 1 })
  })

  it('renders the completed challenge result', () => {
    const wrapper = mount(MinesweeperBoard, {
      props: {
        snapshot: snapshot('finished', {
          started: true,
          revealedCount: 71,
          flaggedCount: 10,
          remainingMines: 0,
          elapsedMs: 12_300,
          cells: Array.from({ length: 81 }, () => ({ state: 'open', adjacent: 0 })),
        }),
      },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.minesweeper-result').text()).toContain('初级通关')
    expect(wrapper.get('.minesweeper-result').text()).toContain('12.3')
    expect(wrapper.find('.minesweeper-result .primary-button').exists()).toBe(true)
  })
})
