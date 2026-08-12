import { mount } from '@vue/test-utils'
import MatchRequestPanel from './MatchRequestPanel.vue'

describe('MatchRequestPanel', () => {
  it('confirms before requesting a table termination', async () => {
    const wrapper = mount(MatchRequestPanel, {
      props: {
        request: null,
        canRequestEndTable: true,
      },
    })

    await wrapper.get('.end-table-button').trigger('click')
    expect(wrapper.get('.end-table-modal').text()).toContain('当前进度不会计入战绩')
    expect(wrapper.emitted('request')).toBeUndefined()

    await wrapper.get('.end-table-modal .confirm').trigger('click')
    expect(wrapper.emitted('request')).toEqual([['end_table']])
  })

  it('shows unanimous approval progress and lets another player accept', async () => {
    const wrapper = mount(MatchRequestPanel, {
      props: {
        request: {
          kind: 'end_table',
          requesterId: 'p1',
          requesterName: '玩家一',
          isMine: false,
          hasApproved: false,
          approvedPlayerIds: ['p1'],
          approvalCount: 1,
          requiredApprovalCount: 3,
        },
      },
    })

    expect(wrapper.text()).toContain('玩家一申请结束本桌')
    expect(wrapper.text()).toContain('1 / 3 人已同意')
    await wrapper.get('.request-response-actions .accept').trigger('click')
    expect(wrapper.emitted('resolve')).toEqual([[true]])
  })
})
