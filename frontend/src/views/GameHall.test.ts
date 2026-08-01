import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import GameHall from './GameHall.vue'

describe('GameHall', () => {
  it('shows six games and selects the requested game', async () => {
    const wrapper = mount(GameHall, {
      props: {
        account: {
          id: 'account-1',
          username: 'tester',
          displayName: '测试玩家',
          createdAt: '2026-08-01T00:00:00Z',
        },
      },
      global: { plugins: [createPinia()] },
    })

    expect(wrapper.findAll('.game-card')).toHaveLength(6)
    expect(wrapper.text()).toContain('军旗')
    const gomoku = wrapper.findAll('.game-card').find((card) => card.text().includes('五子棋'))
    expect(gomoku).toBeDefined()
    await gomoku!.trigger('click')

    expect(wrapper.emitted('select')?.[0]?.[0]).toMatchObject({
      key: 'gomoku',
      name: '五子棋',
    })
  })
})
