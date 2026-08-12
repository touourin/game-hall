import { mount } from '@vue/test-utils'
import BackNavigationButton from './BackNavigationButton.vue'
import GameHomeHeader from './GameHomeHeader.vue'

describe('GameHomeHeader', () => {
  it('uses the shared top-left navigation button', async () => {
    const wrapper = mount(GameHomeHeader, {
      props: {
        gameKey: 'gomoku',
        eyebrow: '2 人',
        title: '五子棋',
        description: '一子定势，五子连珠',
      },
    })

    const back = wrapper.getComponent(BackNavigationButton)
    expect(back.props('label')).toBe('返回游戏大厅')

    await back.trigger('click')
    expect(wrapper.emitted('back')).toHaveLength(1)
  })
})
