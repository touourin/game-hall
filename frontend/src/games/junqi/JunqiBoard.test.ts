import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { vi } from 'vitest'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import JunqiBoard from './JunqiBoard.vue'

function snapshot(turnPlayerId: string): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'TEST',
    gameKey: 'junqi',
    gameName: '军旗',
    options: { mode: 'dark' },
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', name: '玩家一', seat: 0 },
    players: [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '玩家二', seat: 1, connected: true, isHost: false },
    ],
    requiredPlayers: 2,
    roundNumber: 1,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: {
      canStart: false,
      canRestart: false,
      canAct: true,
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
      mode: 'dark',
      modeLabel: '暗军旗',
      board: Array.from({ length: 12 }, () => Array(5).fill(null)),
      turnPlayerId,
      colors: { p1: 'red', p2: 'blue' },
      viewerSide: 'red',
      setupReady: { p1: true, p2: true },
      lastAction: null,
      moveCount: 0,
      terrain: {
        camps: [[1, 1], [1, 3], [2, 2], [3, 1], [3, 3], [8, 1], [8, 3], [9, 2], [10, 1], [10, 3]],
        headquarters: [[0, 1], [0, 3], [11, 1], [11, 3]],
      },
    },
  }
}

describe('JunqiBoard', () => {
  it('renders a dedicated military board with roads, railways, and battlefield landmarks', () => {
    const wrapper = mount(JunqiBoard, {
      props: { snapshot: snapshot('p1') },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.find('.junqi-route-map').exists()).toBe(true)
    expect(wrapper.findAll('.rail-network')).toHaveLength(2)
    expect(wrapper.findAll('.junqi-special-space.frontline')).toHaveLength(3)
    expect(wrapper.findAll('.junqi-special-space.mountain')).toHaveLength(2)
    expect(wrapper.findAll('.junqi-cell.camp')).toHaveLength(10)
    expect(wrapper.findAll('.junqi-cell.headquarters')).toHaveLength(4)
    expect(wrapper.get('.terrain-legend').text()).toContain('铁路线')
    expect(wrapper.get('.territory-label.enemy').text()).toContain('敌方阵地')
    expect(wrapper.get('.territory-label.self').text()).toContain('我方阵地')
  })

  it('disables the whole board while waiting for the opponent', async () => {
    const wrapper = mount(JunqiBoard, {
      props: { snapshot: snapshot('p2') },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.junqi-cell')).toHaveLength(60)
    expect(
      wrapper.findAll('.junqi-cell').every((cell) => cell.attributes('disabled') !== undefined),
    ).toBe(true)

    await wrapper.setProps({ snapshot: snapshot('p1') })
    expect(
      wrapper.findAll('.junqi-cell').every((cell) => cell.attributes('disabled') === undefined),
    ).toBe(true)
  })

  it('previews a touch move before submitting it on the second target tap', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const current = snapshot('p1')
    const game = current.game as {
      board: Array<Array<Record<string, unknown> | null>>
    }
    game.board[11][0] = {
      id: 'red-engineer',
      side: 'red',
      kind: 'engineer',
      label: '工兵',
      revealed: true,
    }
    const wrapper = mount(JunqiBoard, {
      props: { snapshot: current },
      global: { plugins: [pinia] },
    })
    const cells = wrapper.findAll('.junqi-cell')
    const source = cells[11 * 5]
    const target = cells[10 * 5]
    const touchTarget = () => {
      const event = new MouseEvent('click', { bubbles: true, cancelable: true })
      Object.defineProperty(event, 'pointerType', { value: 'touch' })
      target?.element.dispatchEvent(event)
    }

    await source?.trigger('click')
    touchTarget()
    await nextTick()

    expect(action).not.toHaveBeenCalled()
    expect(target?.classes()).toContain('confirming')
    expect(wrapper.text()).toContain('再点一次确认')

    touchTarget()
    await nextTick()

    expect(action).toHaveBeenCalledWith('move', {
      fromRow: 11,
      fromColumn: 0,
      toRow: 10,
      toColumn: 0,
    })
  })
})
