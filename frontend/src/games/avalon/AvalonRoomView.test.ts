import { createPinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import type { RoomSnapshot } from '../../types/avalon'
import AvalonTable from './AvalonTable.vue'
import AvalonRoomView from './AvalonRoomView.vue'

describe('AvalonRoomView', () => {
  it('forwards the role skin and chat event through the module adapter', async () => {
    const wrapper = mount(AvalonRoomView, {
      props: {
        snapshot: {
          players: [],
          game: {},
        } as unknown as RoomSnapshot,
        roleSkin: 'dark-chronicle',
      },
      global: {
        plugins: [createPinia()],
        stubs: { AvalonTable: true },
      },
    })
    await flushPromises()

    const table = wrapper.getComponent(AvalonTable)
    expect(table.props('roleSkin')).toBe('dark-chronicle')
    table.vm.$emit('openChat')
    expect(wrapper.emitted('openChat')).toHaveLength(1)
  })
})
