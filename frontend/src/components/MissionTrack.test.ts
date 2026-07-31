import { mount } from '@vue/test-utils'
import MissionTrack from './MissionTrack.vue'

describe('MissionTrack', () => {
  it('renders all five missions and completed outcomes', () => {
    const wrapper = mount(MissionTrack, {
      props: {
        currentMission: 2,
        playerCount: 7,
        replayableMissions: [1],
        history: [
          { number: 1, teamIds: ['p1', 'p2'], success: true, failCount: 0 },
        ],
      },
    })

    expect(wrapper.findAll('.mission-node')).toHaveLength(5)
    expect(wrapper.findAll('.mission-node')[0].classes()).toContain('success')
    expect(wrapper.findAll('.mission-node')[1].classes()).toContain('current')
    expect(wrapper.findAll('.mission-requirement').map((item) => item.text())).toEqual([
      '2人',
      '3人',
      '3人',
      '4人',
      '4人',
    ])
    expect(wrapper.text()).toContain('双败')
  })

  it('opens replay only for a mission with voting history', async () => {
    const wrapper = mount(MissionTrack, {
      props: {
        currentMission: 2,
        playerCount: 6,
        replayableMissions: [1],
        history: [],
      },
    })

    const missions = wrapper.findAll('.mission-node')
    expect(missions[0].attributes('disabled')).toBeUndefined()
    expect(missions[1].attributes('disabled')).toBeDefined()

    await missions[0].trigger('click')
    expect(wrapper.emitted('selectMission')).toEqual([[1]])
  })
})
