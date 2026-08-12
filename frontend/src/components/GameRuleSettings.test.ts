import { mount } from '@vue/test-utils'
import {
  applyGameRuleChange,
  defaultGameRules,
  gameRuleLabels,
  hasGameHandicap,
} from '../gameRules'
import GameRuleSettings from './GameRuleSettings.vue'

describe('GameRuleSettings', () => {
  it('keeps one night werewolf discussion untimed', () => {
    const rules = defaultGameRules('one_night_werewolf')
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'one_night_werewolf',
        modelValue: rules,
      },
    })

    expect(rules).not.toHaveProperty('discussionSeconds')
    expect(gameRuleLabels('one_night_werewolf', rules)).toContain('不限时讨论')
    expect(wrapper.text()).not.toContain('晨间讨论')
    expect(wrapper.text()).not.toContain('3 分钟')
  })

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
    expect(disclosure.attributes('open')).toBeUndefined()
    expect(disclosure.text()).toContain('一分钟导读 · 完整规则 · 完整背景故事')
    expect(disclosure.text()).toContain('光明渐盛，暗流未息')
    expect(disclosure.text()).toContain('本模式不启用湖中仙女、标准刺杀和提前刺杀')
    expect(disclosure.text()).toContain('刺杀权转交给心怀异念之臣')
    expect(disclosure.text()).toContain('一分钟看懂完整玩法')
    expect(disclosure.text()).toContain('人数与身份配置')
    expect(disclosure.text()).toContain('赞成票必须过半才通过')
    expect(disclosure.text()).toContain('当前任务直接失败并计入一次失败任务')
    expect(disclosure.text()).toContain('好人先完成三次成功任务')
    expect(disclosure.text()).toContain('梅林不知道谁是心怀异念之臣')
    expect(disclosure.text()).not.toContain('帮助梅林缩小派西维尔')
    expect(disclosure.text()).toContain('5–7 人局为“心怀异念之臣 + 1 名随机授刃诱饵”')
    expect(disclosure.text()).toContain('8–10 人局增加到 2 名诱饵')
    expect(disclosure.text()).toContain('刺客不认识的奥伯伦')
    expect(disclosure.text()).toContain('奥伯伦不是固定候选')
    expect(disclosure.text()).toContain('授刃成功后，系统会向所有玩家公开持刃者')
    expect(disclosure.text()).toContain('完整胜负结算')
    expect(disclosure.text()).toContain('王庭之内的刀与影')
    expect(disclosure.text()).toContain('真正能够把刀刺向梅林的人，一直就在王庭之内')
    expect(disclosure.text()).toContain('他知道黑誓之刃握在谁的手里')
    expect(disclosure.text()).not.toContain('他不知道匕首落入了谁的手中')
    expect(disclosure.text()).toContain('开局是好人')
    expect(disclosure.text()).toContain('王庭暗流的双终局')
    expect(disclosure.text()).toContain('固定关闭湖中仙女、标准刺杀与提前刺杀')
    expect(disclosure.text()).toContain('可选角色规则：暗影梅林')
    expect(disclosure.text()).toContain('暗影梅林是梅林分离后叛离本体的分身')
    expect(disclosure.text()).toContain('梅林死亡时暗影梅林也必定消亡')
    expect(disclosure.text()).toContain('准确知道梅林，也能准确辨认刺客、莫甘娜、奥伯伦与普通爪牙')
    expect(disclosure.text()).toContain('祓影议庭')
    expect(disclosure.text()).toContain('第二次任务失败强制开启祓影议庭')
    expect(disclosure.text()).not.toContain('是否开启祓影议庭')
    expect(disclosure.text()).not.toContain('暗刃议影')
    expect(disclosure.text()).toContain('祓影票')
    expect(disclosure.text()).not.toContain('裁影')
    expect(disclosure.text()).toContain('暗影梅林必须是唯一最高票')
  })

  it('only offers shadow Merlin inside Court Undercurrent and clears it when leaving', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'avalon',
        modelValue: defaultGameRules('avalon'),
      },
    })
    expect(wrapper.text()).not.toContain('六人及以上可用')

    const court = wrapper
      .findAll('button')
      .find((button) => button.text().includes('心怀异念之臣可能被刺客授刃'))
    await court?.trigger('click')
    const courtRules = wrapper.emitted('update:modelValue')?.at(-1)?.[0]
    await wrapper.setProps({ modelValue: courtRules as Record<string, unknown> })

    const shadow = wrapper
      .findAll('button')
      .find((button) => button.text().includes('六人及以上可用'))
    expect(shadow).toBeDefined()
    await shadow?.trigger('click')
    const shadowRules = wrapper.emitted('update:modelValue')?.at(-1)?.[0]
    expect(shadowRules).toMatchObject({
      mode: 'court_undercurrent',
      shadowMerlinEnabled: true,
    })
    expect(
      gameRuleLabels('avalon', shadowRules as Record<string, unknown>),
    ).toContain('暗影梅林扩展')

    await wrapper.setProps({ modelValue: shadowRules as Record<string, unknown> })
    const standard = wrapper
      .findAll('button')
      .find((button) => button.text().includes('经典任务'))
    await standard?.trigger('click')
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toMatchObject({
      mode: 'standard',
      shadowMerlinEnabled: false,
    })
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
      '吃子提醒',
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

    expect(defaultGameRules('hanoi')).toEqual({ discCount: 5, allowSpectators: true })
    expect(wrapper.emitted('update:modelValue')?.[0]?.[0]).toEqual({ discCount: 8, allowSpectators: true })
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

  it('offers a room-level capture reminder for Xiangqi', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'xiangqi',
        modelValue: defaultGameRules('xiangqi'),
      },
    })
    const captureHints = wrapper
      .findAll('button')
      .find((button) => button.text().includes('当前可以吃到的敌子'))

    expect(captureHints?.classes()).toContain('active')
    await captureHints?.trigger('click')

    expect(wrapper.emitted('update:modelValue')?.[0]?.[0]).toMatchObject({
      captureHintsEnabled: false,
    })
    expect(gameRuleLabels('xiangqi', { captureHintsEnabled: false })).toContain(
      '关闭吃子提醒',
    )
  })

  it('offers Xiangqi handicaps with only host or opponent as giver', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'xiangqi',
        modelValue: defaultGameRules('xiangqi'),
      },
    })
    const nine = wrapper.findAll('button').find((button) => button.text().trim() === '让九子')
    expect(wrapper.text()).not.toContain('房主让子')

    await nine?.trigger('click')
    const rules = wrapper.emitted('update:modelValue')?.[0]?.[0] as Record<string, unknown>
    await wrapper.setProps({ modelValue: rules })

    expect(wrapper.text()).toContain('房主让子')
    expect(wrapper.text()).toContain('对手让子')
    expect(wrapper.text()).not.toContain('随机让子')
    expect(wrapper.text()).not.toContain('首局先手')
    expect(gameRuleLabels('xiangqi', rules)).toContain('让九子')
  })

  it('limits Go handicaps to 19 lines and zero komi', async () => {
    const wrapper = mount(GameRuleSettings, {
      props: {
        gameKey: 'go',
        modelValue: defaultGameRules('go'),
      },
    })
    const six = wrapper.findAll('button').find((button) => button.text().trim() === '让 6 子')
    await six?.trigger('click')
    const rules = wrapper.emitted('update:modelValue')?.[0]?.[0] as Record<string, unknown>
    expect(rules).toMatchObject({ boardSize: 19, komi: 0, handicap: 6 })

    await wrapper.setProps({ modelValue: rules })
    expect(wrapper.findAll('button').find((button) => button.text().trim() === '7.5')?.attributes('disabled')).toBeDefined()
    expect(gameRuleLabels('go', rules)).toContain('让 6 子')

    const thirteen = wrapper.findAll('button').find((button) => button.text().trim() === '13 路')
    await thirteen?.trigger('click')
    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toMatchObject({
      boardSize: 13,
      handicap: 0,
    })
  })

  it('keeps handicap constraints reusable outside the settings component', () => {
    const rules = applyGameRuleChange(
      'go',
      defaultGameRules('go'),
      'handicap',
      9,
    )

    expect(rules).toMatchObject({ boardSize: 19, komi: 0, handicap: 9 })
    expect(hasGameHandicap('go', rules)).toBe(true)
    expect(hasGameHandicap('xiangqi', { handicap: 'none' })).toBe(false)
    expect(hasGameHandicap('xiangqi', { handicap: 'rook' })).toBe(true)
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

    expect(defaultGameRules('minesweeper')).toEqual({ difficulty: 'beginner', allowSpectators: true })
    expect(wrapper.emitted('update:modelValue')?.[0]?.[0]).toEqual({ difficulty: 'expert', allowSpectators: true })
    expect(gameRuleLabels('minesweeper', { difficulty: 'expert' })).toEqual([
      '高级',
      '16×30',
      '99 雷',
    ])
    expect(wrapper.text()).not.toContain('首局先手')
  })

  it('offers timed and endless Tetris challenges', async () => {
    const rules = defaultGameRules('tetris')
    const wrapper = mount(GameRuleSettings, {
      props: { gameKey: 'tetris', modelValue: rules },
    })

    expect(rules).toEqual({
      challengeMode: 'timed',
      durationSeconds: 180,
      allowSpectators: false,
    })
    expect(wrapper.text()).toContain('1 分钟')
    expect(wrapper.text()).toContain('3 分钟')
    expect(wrapper.text()).toContain('5 分钟')
    expect(gameRuleLabels('tetris', rules)[0]).toBe('3 分钟限时')

    const endless = wrapper.findAll('button')
      .find((button) => button.text().includes('直到方块堆到顶部'))
    await endless?.trigger('click')
    const updated = wrapper.emitted('update:modelValue')?.at(-1)?.[0] as Record<string, unknown>

    expect(updated).toMatchObject({ challengeMode: 'endless' })
    expect(gameRuleLabels('tetris', updated)[0]).toBe('无限挑战')
    expect(wrapper.text()).not.toContain('首局先手')
    expect(wrapper.text()).not.toContain('第一人称观战')
  })
})
