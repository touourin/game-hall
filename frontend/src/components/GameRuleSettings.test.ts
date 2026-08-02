import { mount } from '@vue/test-utils'
import { defaultGameRules, gameRuleLabels } from '../gameRules'
import GameRuleSettings from './GameRuleSettings.vue'

describe('GameRuleSettings', () => {
  it('keeps the court undercurrent story, role, and rules in one guide', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'avalon',
        modelValue: defaultGameRules('avalon'),
      },
    })
    const courtUndercurrent = wrapper
      .findAll('button')
      .find((button) => button.text().includes('王庭暗流'))

    await courtUndercurrent?.trigger('click')
    const courtRules = wrapper.emitted('update:modelValue')?.[0]?.[0]
    await wrapper.setProps({ modelValue: courtRules as Record<string, unknown> })

    const disclosure = wrapper.get('.avalon-mode-guide-disclosure')
    expect(disclosure.attributes('open')).toBeDefined()
    expect(disclosure.text()).toContain('一分钟导读 · 完整规则 · 完整背景故事')
    expect(disclosure.text()).toContain('胜势已成，暗流未息')
    expect(disclosure.text()).toContain('既没有标准刺杀，也不能提前刺杀')
    expect(disclosure.text()).toContain('刺杀梅林的使命也随之转交')
    expect(disclosure.text()).toContain('一分钟看懂完整玩法')
    expect(disclosure.text()).toContain('人数与身份配置')
    expect(disclosure.text()).toContain('赞成票必须过半才通过')
    expect(disclosure.text()).toContain('5–9 人局为“心怀异念之臣 + 1 名随机好人诱饵”')
    expect(disclosure.text()).toContain('完整胜负结算')
    expect(disclosure.text()).toContain('黑誓之刃与王庭裂痕')
    expect(disclosure.text()).toContain('亚瑟一方才真正赢下这场暗流中的战争')
    expect(disclosure.text()).toContain('开局属于好人阵营')
    expect(disclosure.text()).toContain('新模式终局规则')
    expect(disclosure.text()).toContain('固定关闭湖中仙女与提前刺杀')
  })

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
    const swap2Opening = wrapper
      .findAll('button')
      .find((button) => button.text().includes('Swap2 公平开局'))

    expect(defaultGameRules('gomoku')).toMatchObject({
      winRule: 'exact_five',
      openingRule: 'swap2',
    })
    expect(exactFive?.classes()).toContain('active')
    await renju?.trigger('click')
    const renjuRules = wrapper.emitted('update:modelValue')?.[0]?.[0]
    expect(renjuRules).toMatchObject({
      winRule: 'renju',
      openingRule: 'standard',
    })
    await wrapper.setProps({ modelValue: renjuRules as Record<string, unknown> })
    expect(swap2Opening?.attributes('disabled')).toBeDefined()
    expect(swap2Opening?.text()).toContain('有禁手连珠不适用 Swap2')
    await swap2Opening?.trigger('click')
    expect(wrapper.emitted('update:modelValue')).toHaveLength(1)
    expect(wrapper.text()).not.toContain('19 路')
    expect(wrapper.text()).toContain('正好五子')
    expect(wrapper.text()).toContain('有禁手连珠')
    expect(wrapper.text()).toContain('Swap2 公平开局')
    expect(wrapper.text()).toContain('允许悔棋')
  })

  it('builds readable labels with defaults and selected Go rules', () => {
    expect(gameRuleLabels('gomoku', {})).toContain('Swap2 开局')
    expect(gameRuleLabels('gomoku', {})).toContain('正好五子')
    expect(gameRuleLabels('xiangqi', {})).toEqual([
      '随机先手',
      '允许悔棋',
      '允许和棋',
      '允许游客',
    ])
    expect(
      gameRuleLabels('go', {
        boardSize: 9,
        komi: 0,
        firstPlayer: 'host',
        allowUndo: false,
        allowDraw: true,
      }),
    ).toEqual(['9 路棋盘', '房主先手', '禁止悔棋', '允许和棋', '贴目 0', '允许游客'])
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

  it('offers Texas Holdem stacks and blinds without a first-player setting', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'poker',
        modelValue: defaultGameRules('poker'),
      },
    })
    const deepStack = wrapper.findAll('button').find((button) => button.text().trim() === '2000')
    const highBlind = wrapper.findAll('button').find((button) => button.text().trim() === '20/40')

    await deepStack?.trigger('click')
    await highBlind?.trigger('click')

    expect(wrapper.emitted('update:modelValue')?.[0]?.[0]).toMatchObject({ startingChips: 2000 })
    expect(wrapper.emitted('update:modelValue')?.[1]?.[0]).toMatchObject({ smallBlind: 20 })
    expect(gameRuleLabels('poker', {})).toEqual(['2–8 人', '起始 1000 筹码', '盲注 10/20', '允许游客'])
    expect(wrapper.text()).not.toContain('首局先手')
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

  it('keeps guest-created multiplayer rooms in casual mode', () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'xiangqi',
        modelValue: defaultGameRules('xiangqi'),
        guestMode: true,
      },
    })
    const registeredOnly = wrapper
      .findAll('button')
      .find((button) => button.text().includes('仅登录玩家'))

    expect(registeredOnly?.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('整局不会写入任何玩家的个人战绩')
  })

  it('offers all three classic Minesweeper difficulties', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'minesweeper',
        modelValue: defaultGameRules('minesweeper'),
      },
    })
    const expert = wrapper
      .findAll('button')
      .find((button) => button.text().includes('16×30'))

    await expert?.trigger('click')

    expect(defaultGameRules('minesweeper')).toEqual({ difficulty: 'beginner' })
    expect(wrapper.emitted('update:modelValue')?.[0]?.[0]).toEqual({ difficulty: 'expert' })
    expect(gameRuleLabels('minesweeper', { difficulty: 'expert' })).toEqual([
      '高级',
      '16×30',
      '99 雷',
    ])
    expect(wrapper.text()).not.toContain('首局先手')
  })
})
