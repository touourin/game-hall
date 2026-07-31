import { mount } from '@vue/test-utils'
import MissionTrack from './MissionTrack.vue'

describe('MissionTrack', () => {
  it('renders all five missions and completed outcomes', () => {
    const wrapper = mount(MissionTrack, {
      props: {
        currentMission: 2,
        playerCount: 7,
        history: [
          { number: 1, teamIds: ['p1', 'p2'], success: true, failCount: 0 },
        ],
      },
    })

    expect(wrapper.findAll('.mission-node')).toHaveLength(5)
    expect(wrapper.findAll('.mission-node')[0].classes()).toContain('success')
    expect(wrapper.findAll('.mission-node')[1].classes()).toContain('current')
    expect(wrapper.text()).toContain('双败')
  })
})

