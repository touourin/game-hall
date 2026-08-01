import { mount } from '@vue/test-utils'
import { defaultGameRules, gameRuleLabels } from '../gameRules'
import GameRuleSettings from './GameRuleSettings.vue'

describe('GameRuleSettings', () => {
  it('offers the configured Gomoku variants', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'gomoku',
        modelValue: defaultGameRules('gomoku'),
      },
    })
    const exactFive = wrapper
      .findAll('button')
      .find((button) => button.text().includes('正好五子'))
    const renju = wrapper
      .findAll('button')
      .find((button) => button.text().includes('有禁手连珠'))
    const standardOpening = wrapper
      .findAll('button')
      .find((button) => button.text().includes('标准开局'))
    const fiveMinutes = wrapper
      .findAll('button')
      .find((button) => button.text().trim() === '5 分钟')

    await exactFive?.trigger('click')
    await renju?.trigger('click')
    await standardOpening?.trigger('click')
    await fiveMinutes?.trigger('click')

    expect(wrapper.emitted('update:modelValue')?.[0]?.[0]).toMatchObject({
      winRule: 'exact_five',
    })
    expect(wrapper.emitted('update:modelValue')?.[1]?.[0]).toMatchObject({
      winRule: 'renju',
    })
    expect(wrapper.emitted('update:modelValue')?.[2]?.[0]).toMatchObject({
      openingRule: 'standard',
    })
    expect(wrapper.emitted('update:modelValue')?.[3]?.[0]).toMatchObject({
      timeLimitSeconds: 300,
    })
    expect(wrapper.text()).not.toContain('19 路')
    expect(wrapper.text()).toContain('正好五子')
    expect(wrapper.text()).toContain('有禁手连珠')
    expect(wrapper.text()).toContain('Swap2 公平开局')
    expect(wrapper.text()).toContain('允许悔棋')
  })

  it('builds readable labels with defaults and selected Go rules', () => {
    expect(gameRuleLabels('gomoku', {})).toContain('Swap2 开局')
    expect(gameRuleLabels('gomoku', { timeLimitSeconds: 300 })).toContain(
      '每方 5 分钟',
    )
    expect(gameRuleLabels('xiangqi', {})).toEqual([
      '随机先手',
      '允许悔棋',
      '允许和棋',
    ])
    expect(
      gameRuleLabels('go', {
        boardSize: 9,
        komi: 0,
        firstPlayer: 'host',
        allowUndo: false,
        allowDraw: true,
      }),
    ).toEqual(['9 路棋盘', '房主先手', '禁止悔棋', '允许和棋', '贴目 0'])
  })

  it('offers classic, laizi, and no-shuffle Doudizhu modes', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'doudizhu',
        modelValue: defaultGameRules('doudizhu'),
      },
    })
    const laizi = wrapper.findAll('button').find((button) => button.text().includes('癞子'))
    const noShuffle = wrapper.findAll('button').find((button) => button.text().includes('不洗牌'))

    await laizi?.trigger('click')
    await noShuffle?.trigger('click')

    expect(wrapper.emitted('update:modelValue')?.[0]?.[0]).toMatchObject({ variant: 'laizi' })
    expect(wrapper.emitted('update:modelValue')?.[1]?.[0]).toMatchObject({ variant: 'no_shuffle' })
    expect(gameRuleLabels('doudizhu', { variant: 'laizi' })).toContain('叫地主／抢地主')
    expect(gameRuleLabels('doudizhu', { firstPlayer: 'host' })).toContain('房主首叫')
    expect(wrapper.text()).toContain('随机指定首叫玩家')
  })

  it('offers Hanoi difficulties without multiplayer settings', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'hanoi',
        modelValue: defaultGameRules('hanoi'),
      },
    })
    const eightDiscs = wrapper
      .findAll('button')
      .find((button) => button.text().includes('8 层'))

    await eightDiscs?.trigger('click')

    expect(defaultGameRules('hanoi')).toEqual({ discCount: 5 })
    expect(wrapper.emitted('update:modelValue')?.[0]?.[0]).toEqual({ discCount: 8 })
    expect(gameRuleLabels('hanoi', { discCount: 8 })).toEqual([
      '8 层圆盘',
      '理论最少 255 步',
    ])
    expect(wrapper.text()).not.toContain('首局先手')
  })
})
