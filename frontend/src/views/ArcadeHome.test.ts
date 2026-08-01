import { createPinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { useArcadeStore } from '../stores/arcade'
import CleanupRoomButton from '../components/CleanupRoomButton.vue'
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

  it('starts an expert Minesweeper challenge with classic rules', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const createRoom = vi.spyOn(arcade, 'createRoom').mockResolvedValue(true)
    const startGame = vi.spyOn(arcade, 'startGame').mockResolvedValue()
    const wrapper = mount(ArcadeHome, {
      props: {
        game: {
          key: 'minesweeper',
          name: '扫雷',
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
    const expert = wrapper
      .findAll('.game-rule-settings button')
      .find((button) => button.text().includes('16×30'))

    await expert?.trigger('click')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createRoom).toHaveBeenCalledWith('minesweeper', { difficulty: 'expert' })
    expect(startGame).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('清除所有安全方格')
  })

  it('shows and cleans an abandoned room without joining it', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    arcade.availableRooms = [
      {
        roomCode: 'OLD2',
        gameKey: 'gomoku',
        gameName: '五子棋',
        hostName: '离线房主',
        playerCount: 2,
        maxPlayers: 2,
        options: {},
        phase: 'playing',
        cleanupAvailable: true,
        allHumansOffline: true,
      },
    ]
    const cleanupRoom = vi.spyOn(arcade, 'cleanupRoom').mockResolvedValue(true)
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

    expect(wrapper.text()).toContain('待清理的房间')
    expect(wrapper.text()).toContain('未完成对局')
    wrapper.findComponent(CleanupRoomButton).vm.$emit('confirm')
    await wrapper.vm.$nextTick()

    expect(cleanupRoom).toHaveBeenCalledWith('OLD2')
  })
})
