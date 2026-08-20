import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import HallClockWidget from './HallClockWidget.vue'

describe('HallClockWidget', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-20T15:42:30+08:00'))
  })

  afterEach(() => vi.useRealTimers())

  it('shows local time and refreshes at the next minute boundary', async () => {
    const wrapper = mount(HallClockWidget)

    expect(wrapper.get('time').text()).toBe('15:42')
    expect(wrapper.text()).toContain('8月20日')
    expect(wrapper.text()).toContain('星期四')

    vi.advanceTimersByTime(30_020)
    await nextTick()

    expect(wrapper.get('time').text()).toBe('15:43')
  })

  it('prioritizes the active-room return action over the clock', async () => {
    const wrapper = mount(HallClockWidget, {
      props: {
        activeGameName: '围棋',
        activeRoomCode: 'R8H2',
      },
    })

    expect(wrapper.find('time').exists()).toBe(false)
    expect(wrapper.text()).toContain('对局进行中')
    expect(wrapper.text()).toContain('围棋')
    expect(wrapper.text()).toContain('房间 R8H2')

    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('resume')).toHaveLength(1)
  })
})
