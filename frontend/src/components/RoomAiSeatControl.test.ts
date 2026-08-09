import { mount } from '@vue/test-utils'
import RoomAiSeatControl from './RoomAiSeatControl.vue'

describe('RoomAiSeatControl', () => {
  it('adds one AI seat with the selected shared difficulty', async () => {
    const wrapper = mount(RoomAiSeatControl, {
      props: {
        availableSeats: 2,
        config: {
          defaultDifficulty: 'normal',
          difficulties: [
            { key: 'easy', label: '简单' },
            { key: 'normal', label: '普通' },
            { key: 'hard', label: '困难' },
          ],
        },
      },
    })

    expect(wrapper.text()).toContain('还可加入 2 名')
    expect(wrapper.find('.sr-only').exists()).toBe(false)
    expect(wrapper.get('.room-ai-seat-actions').findAll('button, select')).toHaveLength(2)
    await wrapper.get('[aria-label="AI 难度"]').setValue('hard')
    await wrapper.get('.room-ai-add-button').trigger('click')

    expect(wrapper.emitted('add')).toEqual([['hard']])
  })

  it('keeps the Avalon-compatible normal fallback without a selector', async () => {
    const wrapper = mount(RoomAiSeatControl, {
      props: { availableSeats: 9 },
    })

    expect(wrapper.find('[aria-label="AI 难度"]').exists()).toBe(false)
    await wrapper.get('.room-ai-add-button').trigger('click')

    expect(wrapper.emitted('add')).toEqual([['normal']])
  })

  it('disables adding while a previous request is pending', () => {
    const wrapper = mount(RoomAiSeatControl, {
      props: { availableSeats: 1, busy: true },
    })

    expect(wrapper.get('.room-ai-add-button').attributes('disabled')).toBeDefined()
  })
})
