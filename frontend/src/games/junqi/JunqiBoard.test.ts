import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
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
      terrain: { camps: [], headquarters: [] },
    },
  }
}

describe('JunqiBoard', () => {
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
})
