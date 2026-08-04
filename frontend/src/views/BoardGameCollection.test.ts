import { mount } from '@vue/test-utils'
import type { BoardGamePlugin } from '../boardGamePlugins'
import BoardGameCollection from './BoardGameCollection.vue'

const plugins: readonly BoardGamePlugin[] = [
  {
    key: 'test-tiles',
    name: '测试拼版',
    players: '2–4 人',
    description: '用于验证桌游插件选择与房间入口',
    category: '版图策略',
    tone: 'forest',
    mark: '拼',
    entryPath: '/board-games/test-tiles',
  },
  {
    key: 'test-mystery',
    name: '测试谜案',
    players: '4–8 人',
    description: '用于验证多人桌游的人数标注',
    category: '合作推理',
    tone: 'violet',
    mark: '谜',
    entryPath: '/board-games/test-mystery',
  },
]

describe('BoardGameCollection', () => {
  it('stays separate from the existing games while no board-game plugin is installed', () => {
    const wrapper = mount(BoardGameCollection)

    expect(wrapper.find('.empty-plugin-cabinet').exists()).toBe(true)
    expect(wrapper.findAll('.empty-cartridge-row > span')).toHaveLength(3)
    expect(wrapper.findAll('.switch-game-tile')).toHaveLength(0)
    expect(wrapper.text()).toContain('当前还没有安装桌游插件')
    expect(wrapper.text()).toContain('不占用现有 7 款游戏')
    expect(wrapper.text()).not.toContain('阿瓦隆')
    expect(wrapper.text()).not.toContain('五子棋')
  })

  it('renders installed board games as player-count-labelled Switch-style plugins', async () => {
    const wrapper = mount(BoardGameCollection, { props: { plugins } })
    const gameTiles = wrapper.findAll('.switch-game-tile')

    expect(gameTiles).toHaveLength(2)
    expect(wrapper.findAll('.tile-plugin-index')).toHaveLength(2)
    expect(wrapper.get('.selected-game-copy').text()).toContain('测试拼版')
    expect(wrapper.get('.selected-game-copy').text()).toContain('2–4 人')
    expect(gameTiles.every((tile) => tile.text().includes('人'))).toBe(true)

    const mystery = gameTiles.find((tile) => tile.text().includes('测试谜案'))
    expect(mystery).toBeDefined()
    await mystery!.trigger('focus')
    expect(wrapper.get('.selected-game-copy').text()).toContain('用于验证多人桌游的人数标注')
    expect(wrapper.get('.selected-game-copy').text()).toContain('4–8 人')

    await mystery!.trigger('click')
    expect(wrapper.emitted('select')?.[0]?.[0]).toMatchObject({
      key: 'test-mystery',
      players: '4–8 人',
      entryPath: '/board-games/test-mystery',
    })
  })

  it('supports collection navigation and launches the selected plugin', async () => {
    const wrapper = mount(BoardGameCollection, { props: { plugins } })

    await wrapper.get('[aria-label="返回游戏大厅"]').trigger('click')
    await wrapper.get('[aria-label="打开设置"]').trigger('click')
    await wrapper.get('.launch-game-button').trigger('click')

    expect(wrapper.emitted('back')).toHaveLength(1)
    expect(wrapper.emitted('settings')).toHaveLength(1)
    expect(wrapper.emitted('select')?.[0]?.[0]).toMatchObject({ key: 'test-tiles' })
  })
})
