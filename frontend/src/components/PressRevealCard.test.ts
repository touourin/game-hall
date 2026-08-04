import { mount } from '@vue/test-utils'
import PressRevealCard from './PressRevealCard.vue'

describe('PressRevealCard', () => {
  it('reveals private content only while pressed', async () => {
    const wrapper = mount(PressRevealCard, { props: { title: '梅林', subtitle: '亚瑟阵营' } })
    const card = wrapper.get('.press-reveal-card')

    expect(wrapper.text()).not.toContain('梅林')
    await card.trigger('pointerdown')
    expect(wrapper.text()).toContain('梅林')
    expect(wrapper.emitted('seen')).toHaveLength(1)
    await card.trigger('pointerup')
    expect(wrapper.text()).not.toContain('梅林')
  })

  it('renders caller-provided artwork without knowing game rules', async () => {
    const wrapper = mount(PressRevealCard, {
      props: {
        title: '隐藏身份',
        artwork: '/role.webp',
        artworkLabel: '王庭秘卷',
        artworkFraming: { scale: 1.16, originXPercent: 50, originYPercent: 29, preserveFrame: true, treatment: 'codex-ink-wash' },
      },
    })

    expect(wrapper.get('.press-reveal-art-label').text()).toContain('王庭秘卷')
    await wrapper.get('.press-reveal-card').trigger('pointerdown')
    const artwork = wrapper.get('.press-reveal-art')
    expect(artwork.element.tagName).toBe('SPAN')
    expect(artwork.attributes('style')).toContain('--reveal-art-scale: 1.16')
    expect(artwork.attributes('style')).toContain('background-image: url(')
    expect(artwork.attributes('style')).toContain('/role.webp')
    expect(wrapper.get('.press-reveal-card').attributes('data-artwork-treatment')).toBe('codex-ink-wash')
    expect(wrapper.find('.press-reveal-inner-art').exists()).toBe(true)
    expect(wrapper.find('img').exists()).toBe(false)
  })

  it('prevents the mobile image context menu while revealing', async () => {
    const wrapper = mount(PressRevealCard, {
      props: { title: '梅林', artwork: '/role.webp' },
    })
    const card = wrapper.get('.press-reveal-card')
    await card.trigger('pointerdown')

    const contextMenu = new Event('contextmenu', { bubbles: true, cancelable: true })
    card.element.dispatchEvent(contextMenu)

    expect(contextMenu.defaultPrevented).toBe(true)
    expect(wrapper.find('img').exists()).toBe(false)
  })
})
