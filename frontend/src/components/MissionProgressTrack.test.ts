import { mount } from '@vue/test-utils'
import MissionProgressTrack from './MissionProgressTrack.vue'
import type { MissionProgressItem } from './uiTypes'

const items: MissionProgressItem[] = [
  { number: 1, requirement: 2, status: 'success', replayable: true, label: '第 1 轮，任务成功' },
  { number: 2, requirement: 3, status: 'current', label: '第 2 轮' },
  { number: 3, requirement: 3, status: 'pending', label: '第 3 轮' },
  { number: 4, requirement: 4, status: 'pending', note: '双败', label: '第 4 轮' },
  { number: 5, requirement: 4, status: 'pending', label: '第 5 轮' },
]

describe('MissionProgressTrack', () => {
  it('renders mission requirements and status', () => {
    const wrapper = mount(MissionProgressTrack, { props: { items } })

    expect(wrapper.findAll('.mission-node')).toHaveLength(5)
    expect(wrapper.findAll('.mission-node')[0]?.classes()).toContain('success')
    expect(wrapper.findAll('.mission-node')[1]?.classes()).toContain('current')
    expect(wrapper.findAll('.mission-requirement').map((item) => item.text())).toEqual([
      '2人', '3人', '3人', '4人', '4人',
    ])
    expect(wrapper.text()).toContain('双败')
  })

  it('only emits for replayable missions', async () => {
    const wrapper = mount(MissionProgressTrack, { props: { items } })
    const missions = wrapper.findAll('.mission-node')

    expect(missions[0]?.attributes('disabled')).toBeUndefined()
    expect(missions[1]?.attributes('disabled')).toBeDefined()
    await missions[0]?.trigger('click')
    expect(wrapper.emitted('select')).toEqual([[1]])
  })
})
