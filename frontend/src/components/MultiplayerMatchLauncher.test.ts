import { mount } from '@vue/test-utils'
import MultiplayerMatchLauncher from './MultiplayerMatchLauncher.vue'

const game = {
  key: 'xiangqi' as const,
  name: '中国象棋',
  players: '2 人',
  description: '隔河列阵，步步攻守',
}

describe('MultiplayerMatchLauncher', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('renders the premium game identity and rule summary', () => {
    const wrapper = mount(MultiplayerMatchLauncher, {
      props: {
        game,
        gameKey: 'xiangqi',
        rooms: [],
        modelValue: {
          firstPlayer: 'random',
          allowUndo: true,
          allowDraw: true,
          allowGuests: true,
        },
        mode: 'create',
        roomCode: '',
      },
    })

    expect(wrapper.text()).toContain('布下楚汉战局')
    expect(wrapper.text()).toContain('对局控制台')
    expect(wrapper.text()).toContain('随机先手')
    expect(wrapper.text()).toContain('掉线保护 10 分钟')
    expect(wrapper.find('.room-browser').exists()).toBe(false)
  })

  it('selects a public room and moves the console into join mode', async () => {
    const wrapper = mount(MultiplayerMatchLauncher, {
      props: {
        game,
        gameKey: 'xiangqi',
        rooms: [{
          roomCode: 'A1B2',
          gameKey: 'xiangqi',
          gameName: '中国象棋',
          hostName: '棋友',
          playerCount: 1,
          maxPlayers: 2,
          options: {},
        }],
        modelValue: {},
        mode: 'create',
        roomCode: '',
      },
    })

    await wrapper.get('.match-room-item').trigger('click')

    expect(wrapper.emitted('update:mode')).toEqual([['join']])
    expect(wrapper.emitted('update:roomCode')).toEqual([['A1B2']])
  })

  it('edits room rules in a focused modal and saves them explicitly', async () => {
    const wrapper = mount(MultiplayerMatchLauncher, {
      attachTo: document.body,
      props: {
        game,
        gameKey: 'xiangqi',
        rooms: [],
        modelValue: {
          firstPlayer: 'random',
          allowUndo: true,
          allowDraw: true,
          allowGuests: true,
        },
        mode: 'create',
        roomCode: '',
      },
    })

    await wrapper.get('.match-rule-summary button').trigger('click')
    const dialog = document.body.querySelector<HTMLElement>('.match-rule-modal')
    expect(dialog?.textContent).toContain('中国象棋房间规则')
    expect(wrapper.element.contains(dialog)).toBe(false)

    const hostFirst = Array.from(
      dialog?.querySelectorAll<HTMLButtonElement>('.game-rule-settings button') ?? [],
    ).find((button) => button.querySelector('strong')?.textContent === '房主')
    hostFirst?.click()
    await wrapper.vm.$nextTick()
    dialog?.querySelector<HTMLButtonElement>('footer button')?.click()
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:modelValue')?.[0]?.[0]).toMatchObject({
      firstPlayer: 'host',
    })
    expect(document.body.querySelector('.match-rule-modal')).toBeNull()
  })
})
