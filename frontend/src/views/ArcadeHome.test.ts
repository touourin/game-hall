import { createPinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { useArcadeStore } from '../stores/arcade'
import ArcadeHome from './ArcadeHome.vue'

describe('ArcadeHome', () => {
  beforeEach(() => localStorage.clear())

  it('submits the selected room rules when creating a game', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const createRoom = vi.spyOn(arcade, 'createRoom').mockResolvedValue(false)
    const wrapper = mount(ArcadeHome, {
      props: {
        game: {
          key: 'gomoku',
          name: '五子棋',
          players: '2 人',
          description: '测试',
        },
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          nextRenameAt: null,
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [pinia] },
    })
    const renju = wrapper
      .findAll('.game-rule-settings button')
      .find((button) => button.text().includes('有禁手连珠'))

    await renju?.trigger('click')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createRoom).toHaveBeenCalledWith(
      'gomoku',
      expect.objectContaining({
        winRule: 'renju',
        firstPlayer: 'random',
        openingRule: 'swap2',
        timeLimitSeconds: 0,
      }),
    )
    expect(createRoom.mock.calls[0]?.[1]).not.toHaveProperty('boardSize')
  })

  it('starts a solo Hanoi challenge with the selected difficulty', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const createRoom = vi.spyOn(arcade, 'createRoom').mockResolvedValue(true)
    const startGame = vi.spyOn(arcade, 'startGame').mockResolvedValue()
    const wrapper = mount(ArcadeHome, {
      props: {
        game: {
          key: 'hanoi',
          name: '汉诺塔',
          players: '1 人',
          description: '测试',
        },
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          nextRenameAt: null,
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [pinia] },
    })
    const sixDiscs = wrapper
      .findAll('.game-rule-settings button')
      .find((button) => button.text().includes('6 层'))

    await sixDiscs?.trigger('click')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createRoom).toHaveBeenCalledWith('hanoi', { discCount: 6 })
    expect(startGame).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('把整座圆盘移到最右侧')
  })
})
