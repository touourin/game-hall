import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import type { ArcadeSnapshot } from '../../types/arcade'
import XiangqiBoard from './XiangqiBoard.vue'

function snapshot(turnPlayerId: string): ArcadeSnapshot {
  const board = Array.from({ length: 10 }, () =>
    Array<string | null>(9).fill(null),
  )
  board[9][4] = 'rK'
  return {
    revision: 1,
    roomCode: 'TEST',
    gameKey: 'xiangqi',
    gameName: '中国象棋',
    options: {},
    phase: 'playing',
    hostId: 'p1',
    self: { id: 'p1', name: '玩家一', seat: 0 },
    players: [
      { id: 'p1', name: '玩家一', seat: 0, connected: true, isHost: true },
      { id: 'p2', name: '玩家二', seat: 1, connected: true, isHost: false },
    ],
    requiredPlayers: 2,
    winner: null,
    winnerPlayerIds: [],
    winReason: null,
    actions: { canStart: false, canRestart: false, canAct: true },
    game: {
      board,
      turnPlayerId,
      colors: { p1: 'red', p2: 'black' },
      viewerColor: 'red',
      lastMove: null,
      redInCheck: false,
      blackInCheck: false,
    },
  }
}

describe('XiangqiBoard', () => {
  it('highlights the selected piece and renders palace guides', async () => {
    const wrapper = mount(XiangqiBoard, {
      props: { snapshot: snapshot('p1') },
      global: { plugins: [createPinia()] },
    })

    const general = wrapper.find('[aria-label="第 10 行第 5 列"]')
    await general.trigger('click')

    expect(general.classes()).toContain('selected')
    expect(general.attributes('aria-pressed')).toBe('true')
    expect(wrapper.text()).toContain('已选帅 · 请选择落点')
    expect(wrapper.find('.palace-lines path').attributes('d')).toContain('M3 0 L5 2')

    await general.trigger('click')
    expect(general.classes()).not.toContain('selected')
  })

  it('disables the whole board while waiting for the opponent', async () => {
    const wrapper = mount(XiangqiBoard, {
      props: { snapshot: snapshot('p2') },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.xiangqi-cell')).toHaveLength(90)
    expect(
      wrapper.findAll('.xiangqi-cell').every((cell) => cell.attributes('disabled') !== undefined),
    ).toBe(true)

    await wrapper.setProps({ snapshot: snapshot('p1') })
    expect(
      wrapper.findAll('.xiangqi-cell').every((cell) => cell.attributes('disabled') === undefined),
    ).toBe(true)
  })
})
