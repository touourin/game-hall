import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import AvatarImage from './AvatarImage.vue'

describe('AvatarImage', () => {
  it('shows the supplied fallback when no image is available', () => {
    const wrapper = mount(AvatarImage, {
      props: { name: '玩家甲', fallback: 3 },
    })

    expect(wrapper.text()).toBe('3')
    expect(wrapper.attributes('aria-label')).toBe('玩家甲的头像')
  })

  it('falls back to the first character after an image error', async () => {
    const wrapper = mount(AvatarImage, {
      props: { name: '玩家乙', src: '/missing-avatar.webp' },
    })

    await wrapper.get('img').trigger('error')
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.text()).toBe('玩')
  })
})
