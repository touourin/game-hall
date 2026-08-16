import { mount } from '@vue/test-utils'
import {
  PluginButton,
  PluginIconButton,
  PluginPlayingCard,
  PluginResultCard,
  PluginRevealCard,
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
})
