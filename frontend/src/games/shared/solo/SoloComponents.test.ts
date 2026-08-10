import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SoloMetricGrid from './SoloMetricGrid.vue'
import SoloResultCard from './SoloResultCard.vue'

describe('solo game components', () => {
  it('renders a configurable metric grid', () => {
    const wrapper = mount(SoloMetricGrid, {
      props: {
        items: [
          { label: '完成用时', value: '12.3 秒' },
          { label: '点击错误', value: 2, tone: 'warning' },
        ],
        columns: 2,
      },
    })

    expect(wrapper.findAll('.solo-metric-card')).toHaveLength(2)
    expect(wrapper.text()).toContain('12.3 秒')
    expect(wrapper.find('.tone-warning').exists()).toBe(true)
  })

  it('renders the common result action and emits restart', async () => {
    const wrapper = mount(SoloResultCard, {
      props: {
        eyebrow: '挑战完成',
        title: '完美解法',
        score: '31',
        scoreUnit: '步',
        canRestart: true,
      },
    })

    await wrapper.get('.solo-result-restart').trigger('click')
    expect(wrapper.text()).toContain('完美解法')
    expect(wrapper.emitted('restart')).toHaveLength(1)
  })
})
