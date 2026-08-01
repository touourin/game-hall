import { createPinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'
import HanoiGame from './HanoiGame.vue'

function snapshot(phase: ArcadeSnapshot['phase'] = 'playing'): ArcadeSnapshot {
  return {
    revision: 1,
    roomCode: 'SOLO',
    gameKey: 'hanoi',
    gameName: '汉诺塔',
    options: { discCount: 3 },
    phase,
    hostId: 'p1',
    self: { id: 'p1', name: '解谜者', seat: 0 },
    players: [
      { id: 'p1', name: '解谜者', seat: 0, connected: true, isHost: true },
    ],
    requiredPlayers: 1,
    roundNumber: 1,
    winner: phase === 'finished' ? 'completed' : null,
    winnerPlayerIds: phase === 'finished' ? ['p1'] : [],
    winReason: phase === 'finished' ? '用 7 步完成 3 层汉诺塔，耗时 5.2 秒' : null,
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
      discCount: 3,
      towers: phase === 'finished' ? [[], [], [3, 2, 1]] : [[3, 2, 1], [], []],
      moves: phase === 'finished' ? 7 : 0,
      optimalMoves: 7,
      elapsedMs: phase === 'finished' ? 5_200 : 0,
      isOptimal: phase === 'finished',
      lastMove: phase === 'finished' ? { fromTower: 0, toTower: 2, disc: 1 } : null,
    },
  }
}

describe('HanoiGame', () => {
  it('moves the selected top disc using tap controls', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(HanoiGame, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })
    const towers = wrapper.findAll('.hanoi-tower')

    await towers[0]?.trigger('click')
    expect(towers[0]?.classes()).toContain('selected')
    await towers[2]?.trigger('click')
    await flushPromises()

    expect(action).toHaveBeenCalledWith('move', { fromTower: 0, toTower: 2 })
    expect(wrapper.text()).toContain('已移动 1 号圆盘')
    wrapper.unmount()
  })

  it('resets the active puzzle and reports optimal completion', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const action = vi.spyOn(arcade, 'action').mockResolvedValue()
    const wrapper = mount(HanoiGame, {
      props: { snapshot: snapshot() },
      global: { plugins: [pinia] },
    })

    await wrapper.get('.hanoi-guide button').trigger('click')
    expect(action).toHaveBeenCalledWith('reset')

    const completed = snapshot('finished')
    await wrapper.setProps({ snapshot: completed })
    expect(wrapper.get('.hanoi-result').text()).toContain('完美解法')
    expect(wrapper.get('.hanoi-result').text()).toContain('7')
    expect(wrapper.get('.hanoi-result').text()).toContain('5.2 秒')
    wrapper.unmount()
  })

  it('starts a fresh challenge from the completion card', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const restart = vi.spyOn(arcade, 'restartGame').mockResolvedValue(true)
    const wrapper = mount(HanoiGame, {
      props: { snapshot: snapshot('finished') },
      global: { plugins: [pinia] },
    })

    await wrapper.get('.hanoi-result .primary-button').trigger('click')
    await flushPromises()

    expect(restart).toHaveBeenCalledOnce()
    wrapper.unmount()
  })
})
