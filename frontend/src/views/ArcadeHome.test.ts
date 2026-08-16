import { createPinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { useArcadeStore } from '../stores/arcade'
import CleanupRoomButton from '../components/CleanupRoomButton.vue'
import ArcadeHome from './ArcadeHome.vue'

describe('ArcadeHome', () => {
  beforeEach(() => {
    localStorage.clear()
    document.body.innerHTML = ''
  })
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('keeps account settings available from every game home', async () => {
    const wrapper = mount(ArcadeHome, {
      props: {
        game: {
          key: 'xiangqi',
          name: '中国象棋',
          players: '2 人',
          description: '测试',
        },
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.arcade-home').classes()).toContain('adaptive-layout-root')

    await wrapper.get('[aria-label="打开设置"]').trigger('click')

    expect(wrapper.emitted('settings')).toHaveLength(1)
  })

  it('opens a routed invitation in join mode with its room code', () => {
    const wrapper = mount(ArcadeHome, {
      props: {
        game: {
          key: 'junqi',
          name: '军旗',
          players: '2 人',
          description: '测试',
        },
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          createdAt: '2026-08-01T00:00:00Z',
        },
        invitedRoom: 'a1b2',
      },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.get('.segmented-control .active').text()).toBe('加入房间')
    expect((wrapper.get('.room-code-input').element as HTMLInputElement).value).toBe('A1B2')
  })

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
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [pinia] },
    })
    await wrapper.get('.match-rule-summary button').trigger('click')
    const renju = Array.from(
      document.querySelectorAll<HTMLButtonElement>('.game-rule-settings button'),
    ).find((button) => button.textContent?.includes('有禁手连珠'))

    renju?.click()
    await wrapper.vm.$nextTick()
    document.querySelector<HTMLButtonElement>('.match-rule-modal > footer button')?.click()
    await wrapper.vm.$nextTick()
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createRoom).toHaveBeenCalledWith(
      'gomoku',
      expect.objectContaining({
        winRule: 'renju',
        firstPlayer: 'random',
        openingRule: 'standard',
      }),
    )
    expect(createRoom.mock.calls[0]?.[1]).not.toHaveProperty('boardSize')
  })

  it('creates Avalon with the unchanged mode-specific rule combination', async () => {
    const pinia = createPinia()
    const arcade = useArcadeStore(pinia)
    const createRoom = vi.spyOn(arcade, 'createRoom').mockResolvedValue(false)
    const wrapper = mount(ArcadeHome, {
      props: {
        game: {
          key: 'avalon',
          name: '阿瓦隆',
          players: '5–10 人',
          description: '身份推理与团队博弈',
        },
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [pinia] },
    })
    await wrapper.get('.match-rule-summary button').trigger('click')
    const courtUndercurrent = Array.from(
      document.querySelectorAll<HTMLButtonElement>('.game-rule-settings button'),
    ).find((button) => button.textContent?.includes('王庭暗流'))

    courtUndercurrent?.click()
    await wrapper.vm.$nextTick()
    document.querySelector<HTMLButtonElement>('.match-rule-modal > footer button')?.click()
    await wrapper.vm.$nextTick()
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createRoom).toHaveBeenCalledWith('avalon', {
      mode: 'court_undercurrent',
      shadowMerlinEnabled: false,
      ladyEnabled: false,
      listed: true,
      allowGuests: true,
      allowSpectators: true,
      earlyAssassinationEnabled: false,
    })
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

    expect(createRoom).toHaveBeenCalledWith('hanoi', { discCount: 6, allowSpectators: true })
    expect(startGame).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('把整座圆盘移到最右侧')
    expect(wrapper.find('[data-testid="solo-challenge-icon"] svg').exists()).toBe(true)
    expect(wrapper.find('.solo-game-mark').exists()).toBe(false)
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

    expect(createRoom).toHaveBeenCalledWith('minesweeper', { difficulty: 'expert', allowSpectators: true })
    expect(startGame).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('清除所有安全方格')
    expect(wrapper.find('[data-testid="solo-challenge-icon"] svg').exists()).toBe(true)
    expect(wrapper.find('.solo-game-mark').exists()).toBe(false)
  })

  it('renders the reaction challenge with a vector identity and complete console', () => {
    const wrapper = mount(ArcadeHome, {
      props: {
        game: {
          key: 'reaction',
          name: '反应挑战',
          players: '1 人',
          description: '盯住信号，挑战毫秒反应',
        },
        account: {
          id: 'account-1',
          username: 'tester',
          playerName: '测试玩家',
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.find('[data-testid="solo-challenge-icon"] svg').exists()).toBe(true)
    expect(wrapper.find('.solo-game-mark').exists()).toBe(false)
    expect(wrapper.text()).toContain('挑战你的毫秒反应')
    expect(wrapper.text()).toContain('保持待命')
    expect(wrapper.text()).toContain('三轮平均计榜')
  })

  it.each([
    ['reaction', true],
    ['hanoi', true],
  ] as const)(
    'uses the %s module capability to decide whether spectating is available',
    (gameKey, expected) => {
      const wrapper = mount(ArcadeHome, {
        props: {
          game: {
            key: gameKey,
            name: gameKey === 'reaction' ? '反应挑战' : '汉诺塔',
            players: '1 人',
            description: '测试',
          },
          account: {
            id: 'account-1',
            username: 'tester',
            playerName: '测试玩家',
            createdAt: '2026-08-01T00:00:00Z',
          },
        },
        global: { plugins: [createPinia()] },
      })

      expect(wrapper.find('.spectator-browser').exists()).toBe(expected)
    },
  )

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
