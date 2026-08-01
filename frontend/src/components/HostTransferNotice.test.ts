import { mount } from '@vue/test-utils'
import HostTransferNotice from './HostTransferNotice.vue'

describe('HostTransferNotice', () => {
  afterEach(() => vi.useRealTimers())

  it('counts down the twenty-second host transfer grace period', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-01T00:00:00Z'))
    const wrapper = mount(HostTransferNotice, {
      props: { transferAt: '2026-08-01T00:00:20+00:00' },
    })

    expect(wrapper.text()).toContain('20 秒后')
    await vi.advanceTimersByTimeAsync(5000)
    expect(wrapper.text()).toContain('15 秒后')
  })
})
