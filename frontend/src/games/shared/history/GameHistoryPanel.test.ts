import { mount } from '@vue/test-utils'
import GameHistoryPanel from './GameHistoryPanel.vue'

describe('GameHistoryPanel', () => {
  it('renders a shared count and text history', () => {
    const wrapper = mount(GameHistoryPanel, {
      props: { title: '完整记录', entries: ['玩家一出牌', '玩家二不出'], open: true },
    })

    expect(wrapper.get('summary').text()).toContain('完整记录')
    expect(wrapper.get('summary').text()).toContain('2 条')
    expect(wrapper.findAll('li').map((item) => item.text())).toEqual(['玩家一出牌', '玩家二不出'])
    expect(wrapper.get('details').attributes()).toHaveProperty('open')
  })

  it('shows the empty state without an empty list', () => {
    const wrapper = mount(GameHistoryPanel, {
      props: { title: '城市动态', entries: [], emptyText: '尚未发生事件' },
    })

    expect(wrapper.find('ol').exists()).toBe(false)
    expect(wrapper.text()).toContain('尚未发生事件')
  })
})
