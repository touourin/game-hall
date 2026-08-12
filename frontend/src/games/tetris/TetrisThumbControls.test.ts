import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import TetrisThumbControls from './TetrisThumbControls.vue'

function dispatchPointer(element: Element | Window, type: string, pointerId: number) {
  const event = new Event(type, { bubbles: true, cancelable: true })
  Object.defineProperties(event, {
    pointerId: { value: pointerId },
    pointerType: { value: 'touch' },
    button: { value: 0 },
  })
  element.dispatchEvent(event)
}

describe('TetrisThumbControls', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
  })

  it('keeps two held pointers repeating independently', async () => {
    const wrapper = mount(TetrisThumbControls, {
      global: { plugins: [createPinia()] },
    })

    dispatchPointer(wrapper.get('[aria-label="向左移动"]').element, 'pointerdown', 1)
    dispatchPointer(wrapper.get('[aria-label="向下软降"]').element, 'pointerdown', 2)
    await vi.advanceTimersByTimeAsync(280)

    expect(wrapper.emitted('move')?.length).toBeGreaterThan(1)
    expect(wrapper.emitted('softDrop')?.length).toBeGreaterThan(1)

    const movesBeforeSecondRelease = wrapper.emitted('move')!.length
    const dropsBeforeSecondRelease = wrapper.emitted('softDrop')!.length
    dispatchPointer(window, 'pointerup', 2)
    await vi.advanceTimersByTimeAsync(100)

    expect(wrapper.emitted('move')!.length).toBeGreaterThan(movesBeforeSecondRelease)
    expect(wrapper.emitted('softDrop')!.length).toBe(dropsBeforeSecondRelease)
    wrapper.unmount()
  })

  it('stops every held action when controls become disabled', async () => {
    const wrapper = mount(TetrisThumbControls)
    dispatchPointer(wrapper.get('[aria-label="向右移动"]').element, 'pointerdown', 3)
    await vi.advanceTimersByTimeAsync(280)
    const moveCount = wrapper.emitted('move')!.length

    await wrapper.setProps({ disabled: true })
    await vi.advanceTimersByTimeAsync(200)

    expect(wrapper.emitted('move')!.length).toBe(moveCount)
    expect(wrapper.get('[aria-label="向右移动"]').attributes()).toHaveProperty('disabled')
    expect(wrapper.get('header button').attributes()).toHaveProperty('disabled')
    wrapper.unmount()
  })
})
