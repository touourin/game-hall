import { mount } from '@vue/test-utils'
import GameLibraryCard from './GameLibraryCard.vue'

describe('GameLibraryCard', () => {
  it('renders the shared game identity and emits selection', async () => {
    const wrapper = mount(GameLibraryCard, {
      props: {
        game: {
          key: 'gomoku',
          name: '五子棋',
          players: '2 人',
          description: '一子定势，五子连珠',
          category: '棋类竞技',
          tone: 'ink',
        },
        index: 2,
        roomCount: 3,
      },
    })

    expect(wrapper.get('.game-library-meta').text()).toContain('03 · 棋类竞技')
    expect(wrapper.get('.game-library-meta').text()).toContain('3 个房间')
    expect(wrapper.find('.game-card-art').exists()).toBe(true)

    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })

  it('uses the shared premium artwork treatment for Avalon', () => {
    const wrapper = mount(GameLibraryCard, {
      props: {
        game: {
          key: 'avalon',
          name: '阿瓦隆',
          players: '5–10 人',
          description: '谎言上桌，忠诚接受考验',
          category: '社交推理',
          tone: 'gold',
        },
        index: 0,
      },
    })

    expect(wrapper.find('.game-card-art').exists()).toBe(true)
    expect(wrapper.find('.art-avalon img').attributes('src')).toContain('avalon')
  })
})
