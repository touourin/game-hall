import { flushPromises, mount } from '@vue/test-utils'
import ArcadeChatPanel from './ArcadeChatPanel.vue'

describe('ArcadeChatPanel', () => {
  it('counts unread messages and sends a trimmed message', async () => {
    const send = vi.fn().mockResolvedValue(true)
    const wrapper = mount(ArcadeChatPanel, {
      props: {
        messages: [],
        maxLength: 300,
        selfId: 'self',
        busy: false,
        send,
      },
    })

    await wrapper.setProps({
      messages: [
        {
          id: 'message-1',
          senderId: 'other',
          senderName: '对手',
          content: '准备好了吗',
          createdAt: '2026-08-01T04:00:00+00:00',
        },
      ],
    })

    expect(wrapper.get('.arcade-chat-dock b').text()).toBe('1')
    await wrapper.get('.arcade-chat-dock').trigger('click')
    expect(wrapper.text()).toContain('准备好了吗')

    await wrapper.get('input').setValue('  开始吧  ')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(send).toHaveBeenCalledWith('开始吧')
    expect(wrapper.get('input').element.value).toBe('')
  })
})
