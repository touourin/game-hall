import { mount } from '@vue/test-utils'
import { defineComponent, nextTick, ref } from 'vue'
import { applyTheme } from '../theme'
import {
  formatPluginDuration,
  formatPluginScore,
  pluginThemeMaterials,
  usePluginFullscreen,
  usePluginTheme,
} from './index'

describe('public plugin SDK utilities', () => {
  it('formats durations without rounding an in-progress timer forward', () => {
    expect(formatPluginDuration(65_299)).toBe('1:05.2')
    expect(formatPluginDuration(9_999, { fractionDigits: 0 })).toBe('9 秒')
    expect(formatPluginDuration(65_200, { style: 'readable' })).toBe('1 分 05.2 秒')
    expect(formatPluginDuration(Number.NaN)).toBe('—')
  })

  it('formats numeric and textual scores with a unit', () => {
    expect(formatPluginScore(12_345.678, { unit: '分' })).toBe('12,345.68 分')
    expect(formatPluginScore('S', { unit: '级' })).toBe('S 级')
    expect(formatPluginScore(null)).toBe('—')
    expect(formatPluginScore(1.234, {
      minimumFractionDigits: -1,
      maximumFractionDigits: Number.NaN,
    })).toBe('1.23')
  })

  it('exposes read-only theme state and immutable material tokens', async () => {
    applyTheme('midnight')
    const wrapper = mount(defineComponent({
      setup() {
        return usePluginTheme()
      },
      template: '<span>{{ theme }}:{{ materials.stage.edge }}</span>',
    }))

    expect(wrapper.text()).toContain('midnight:')
    expect(Object.isFrozen(pluginThemeMaterials('midnight'))).toBe(true)
    expect(Object.isFrozen(pluginThemeMaterials('midnight').stage)).toBe(true)

    applyTheme('royal')
    await nextTick()
    expect(wrapper.text()).toContain('royal:')

    applyTheme('amber')
    await nextTick()
    expect(wrapper.text()).toContain('amber:')
    expect(pluginThemeMaterials('amber').stage.edge).toBe('#f26a13')
    wrapper.unmount()
  })

  it('owns fullscreen state and cleans up native browser integration', async () => {
    const fullscreenDescriptor = Object.getOwnPropertyDescriptor(document, 'fullscreenElement')
    const exitDescriptor = Object.getOwnPropertyDescriptor(document, 'exitFullscreen')
    let fullscreenElement: Element | null = null

    Object.defineProperty(document, 'fullscreenElement', {
      configurable: true,
      get: () => fullscreenElement,
    })
    Object.defineProperty(document, 'exitFullscreen', {
      configurable: true,
      value: vi.fn(async () => {
        fullscreenElement = null
        document.dispatchEvent(new Event('fullscreenchange'))
      }),
    })

    const wrapper = mount(defineComponent({
      setup() {
        const target = ref<HTMLElement | null>(null)
        const fullscreen = usePluginFullscreen(target)
        return { target, ...fullscreen }
      },
      template: '<div ref="target" />',
    }))
    const target = wrapper.element as HTMLElement
    const requestFullscreen = vi.fn(async () => {
      fullscreenElement = target
      document.dispatchEvent(new Event('fullscreenchange'))
    })
    Object.defineProperty(target, 'requestFullscreen', {
      configurable: true,
      value: requestFullscreen,
    })

    expect(wrapper.vm.isSupported).toBe(true)
    expect(await wrapper.vm.enter()).toBe(true)
    expect(wrapper.vm.isFullscreen).toBe(true)
    expect(await wrapper.vm.toggle()).toBe(true)
    expect(wrapper.vm.isFullscreen).toBe(false)
    wrapper.unmount()

    if (fullscreenDescriptor) {
      Object.defineProperty(document, 'fullscreenElement', fullscreenDescriptor)
    } else {
      Reflect.deleteProperty(document, 'fullscreenElement')
    }
    if (exitDescriptor) {
      Object.defineProperty(document, 'exitFullscreen', exitDescriptor)
    } else {
      Reflect.deleteProperty(document, 'exitFullscreen')
    }
  })
})
