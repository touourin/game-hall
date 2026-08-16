import { mount } from '@vue/test-utils'
import {
  PluginButton,
  PluginConfirmDialog,
  PluginEmptyState,
  PluginErrorState,
  PluginIconButton,
  PluginLoadingState,
  PluginMetricGrid,
  PluginModal,
  PluginNumberField,
  PluginPlayingCard,
  PluginResultCard,
  PluginRevealCard,
  PluginRuleGuide,
  PluginSelect,
  PluginTextField,
  type PluginRuleGuideContent,
} from './index'

describe('public plugin SDK components', () => {
  it('exposes a themed button without hiding native attributes', () => {
    const wrapper = mount(PluginButton, {
      props: {
        variant: 'primary',
        block: true,
        disabled: true,
      },
      slots: { default: '确认行动' },
    })

    expect(wrapper.element.tagName).toBe('BUTTON')
    expect(wrapper.text()).toBe('确认行动')
    expect(wrapper.classes()).toEqual(expect.arrayContaining([
      'plugin-button',
      'ui-button--primary',
      'ui-button--block',
    ]))
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('forwards native button events through the public wrapper', async () => {
    const click = vi.fn()
    const wrapper = mount(PluginButton, {
      attrs: { onClick: click },
      slots: { default: '提交' },
    })

    await wrapper.trigger('click')

    expect(click).toHaveBeenCalledOnce()
  })

  it('requires an accessible label for icon-only actions', () => {
    const wrapper = mount(PluginIconButton, {
      props: { label: '关闭帮助' },
      slots: { default: '×' },
    })

    expect(wrapper.element.tagName).toBe('BUTTON')
    expect(wrapper.attributes('aria-label')).toBe('关闭帮助')
  })

  it('keeps the playing-card selection contract stable', async () => {
    const wrapper = mount(PluginPlayingCard, {
      props: {
        rank: 'A',
        suit: '♥',
        red: true,
        interactive: true,
        ariaLabel: '红桃 A',
      },
    })

    await wrapper.trigger('click')

    expect(wrapper.text()).toContain('A')
    expect(wrapper.classes()).toContain('red')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })

  it('renders common result metrics and forwards restart', async () => {
    const wrapper = mount(PluginResultCard, {
      props: {
        eyebrow: '挑战完成',
        title: '完美解法',
        score: 31,
        scoreUnit: '步',
        metrics: [{ label: '最佳纪录', value: '28 步', tone: 'success' }],
        canRestart: true,
      },
    })

    await wrapper.get('.solo-result-restart').trigger('click')

    expect(wrapper.text()).toContain('最佳纪录')
    expect(wrapper.emitted('restart')).toHaveLength(1)
  })

  it('forwards private-information reveal events and content', async () => {
    const wrapper = mount(PluginRevealCard, {
      props: { title: '隐藏身份' },
      slots: { default: '仅自己可见' },
    })

    await wrapper.get('.press-reveal-card').trigger('pointerdown')

    expect(wrapper.text()).toContain('仅自己可见')
    expect(wrapper.emitted('seen')).toHaveLength(1)
  })

  it('keeps modal sizing and close events behind a public contract', async () => {
    const wrapper = mount(PluginModal, {
      props: { title: '回合说明', size: 'medium', inline: true },
      slots: {
        default: '本回合只能执行一次行动',
        footer: '<button class="done">知道了</button>',
      },
    })

    expect(wrapper.get('[role="dialog"]').classes()).toContain('plugin-modal-card--medium')
    expect(wrapper.text()).toContain('本回合只能执行一次行动')
    await wrapper.get('.dialog-close').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
    wrapper.unmount()
  })

  it('exposes a confirmation dialog without leaking internal class props', async () => {
    const wrapper = mount(PluginConfirmDialog, {
      props: {
        title: '重新开始？',
        description: '当前进度不会保留。',
        confirmLabel: '重新开始',
        tone: 'danger',
        inline: true,
      },
    })

    await wrapper.get('.confirm').trigger('click')
    expect(wrapper.emitted('confirm')).toHaveLength(1)
    expect(wrapper.get('.confirm').classes()).toContain('ui-button--danger')
    wrapper.unmount()
  })

  it('renders public metrics with stable tones and ordering', () => {
    const wrapper = mount(PluginMetricGrid, {
      props: {
        valueFirst: true,
        columns: 2,
        items: [
          { label: '得分', value: 120, tone: 'success' },
          { label: '失误', value: 2, tone: 'danger' },
        ],
      },
    })

    expect(wrapper.findAll('.solo-metric-card')).toHaveLength(2)
    expect(wrapper.get('.tone-success').text()).toContain('120')
  })

  it('renders a complete rule guide from public data only', () => {
    const content: PluginRuleGuideContent = {
      ariaLabel: '示例规则',
      eyebrow: 'RULES',
      title: '计数竞速',
      story: '轮流计数。',
      quickStart: {
        label: '快速开始',
        title: '一分钟上手',
        description: '按顺序行动。',
        steps: [{ title: '点击', text: '数字加一。' }],
      },
      feature: {
        label: '关键机制',
        title: '轮流行动',
        description: '不能连续行动。',
        details: [{ label: '终点', text: '率先达到目标。' }],
      },
      flowTitle: '流程',
      steps: [{ title: '开局', text: '随机先手。' }],
      ruleSections: [{
        title: '胜负',
        bullets: [{ text: '达到目标即获胜。' }],
      }],
      background: {
        label: '背景',
        title: '设计说明',
        paragraphs: ['这是一个最小示例。'],
      },
      footer: '以服务端判定为准。',
    }
    const wrapper = mount(PluginRuleGuide, { props: { content } })

    expect(wrapper.get('[aria-label="示例规则"]').text()).toContain('达到目标即获胜')
  })

  it('provides accessible text, number and select fields', async () => {
    const text = mount(PluginTextField, {
      props: {
        id: 'nickname',
        modelValue: '',
        label: '昵称',
        description: '最多十个字',
      },
    })
    await text.get('input').setValue('玩家一号')
    expect(text.emitted('update:modelValue')?.at(-1)).toEqual(['玩家一号'])
    expect(text.get('input').attributes('aria-describedby')).toBe('nickname-description')

    const number = mount(PluginNumberField, {
      props: { id: 'score', modelValue: null, label: '得分', min: 0 },
    })
    await number.get('input').setValue('42')
    expect(number.emitted('update:modelValue')?.at(-1)).toEqual([42])

    const select = mount(PluginSelect, {
      props: {
        id: 'difficulty',
        modelValue: 'normal',
        label: '难度',
        options: [
          { value: 'normal', label: '普通' },
          { value: 'hard', label: '困难' },
        ],
      },
    })
    await select.get('select').setValue('hard')
    expect(select.emitted('update:modelValue')?.at(-1)).toEqual(['hard'])
  })

  it('provides consistent loading, empty and error states', async () => {
    const loading = mount(PluginLoadingState)
    expect(loading.get('[role="status"]').attributes('aria-busy')).toBe('true')

    const empty = mount(PluginEmptyState, {
      props: { title: '没有记录', actionLabel: '刷新' },
    })
    await empty.get('button').trigger('click')
    expect(empty.emitted('action')).toHaveLength(1)

    const error = mount(PluginErrorState)
    expect(error.get('[role="alert"]').text()).toContain('加载失败')
  })
})
