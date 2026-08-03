import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import type { RoleSkinLoadoutRoleOption } from './uiTypes'
import RoleSkinLoadoutPicker from './RoleSkinLoadoutPicker.vue'

function roles(): RoleSkinLoadoutRoleOption[] {
  return [
    '梅林',
    '派西维尔',
    '亚瑟的忠臣',
    '刺客',
    '莫甘娜',
    '莫德雷德',
    '奥伯伦',
    '莫德雷德的爪牙',
  ].map((name, index) => ({
    code: [
      'merlin',
      'percival',
      'loyal_servant',
      'assassin',
      'morgana',
      'mordred',
      'oberon',
      'minion',
    ][index]!,
    name,
    group: index < 3 ? '亚瑟阵营' : '莫德雷德阵营',
    wins: index === 0 ? 2 : 0,
    currentSkinName: '经典桌游',
    currentArtwork: '/classic.webp',
    currentFraming: { scale: 1, originXPercent: 50, originYPercent: 50 },
    legacyAllUnlocked: false,
    upgradeWinsRequired: 2,
    ultimateWinsRequired: 5,
    choices: [
      {
        id: 'classic-tabletop',
        name: '经典桌游',
        description: '基础画风',
        tier: '基础',
        artwork: '/classic.webp',
        framing: { scale: 1, originXPercent: 50, originYPercent: 50 },
        unlocked: true,
        remainingWins: 0,
      },
      {
        id: 'dark-chronicle',
        name: '暗夜史诗',
        description: '升级画风',
        tier: '升级',
        artwork: '/dark.webp',
        framing: { scale: 1, originXPercent: 50, originYPercent: 50 },
        unlocked: index === 0,
        remainingWins: index === 0 ? 0 : 2,
      },
      {
        id: 'grail-myth',
        name: '圣杯神话',
        description: '终极画风',
        tier: '终极',
        artwork: '/grail.webp',
        framing: { scale: 1, originXPercent: 50, originYPercent: 50 },
        unlocked: false,
        remainingWins: 3,
      },
    ],
  }))
}

describe('RoleSkinLoadoutPicker', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('shows all eight independently configurable roles', () => {
    const wrapper = mount(RoleSkinLoadoutPicker, { props: { roles: roles() } })

    expect(wrapper.findAll('[data-role-skin-role]')).toHaveLength(8)
    expect(wrapper.text()).toContain('心怀异念之臣与忠臣共享')
    expect(wrapper.get('[data-role-skin-role="merlin"]').text()).toContain(
      '升级 2/2',
    )
  })

  it('selects an unlocked style for only the active role', async () => {
    const wrapper = mount(RoleSkinLoadoutPicker, { props: { roles: roles() } })
    await wrapper.get('[data-role-skin-role="merlin"]').trigger('click')

    expect(document.body.querySelector('.role-skin-picker-modal')?.classList.contains('adaptive-dialog')).toBe(true)
    expect(document.body.querySelector('.role-skin-choice-grid')?.classList.contains('adaptive-scroll-region')).toBe(true)

    const upgrade = document.body.querySelector<HTMLButtonElement>(
      '[data-role-skin-choice="dark-chronicle"]',
    )
    upgrade?.click()
    await nextTick()

    expect(wrapper.emitted('select')).toEqual([['merlin', 'dark-chronicle']])
    expect(document.body.querySelector('.role-skin-picker-modal')).toBeNull()
  })

  it('does not select a style before its win requirement is met', async () => {
    const wrapper = mount(RoleSkinLoadoutPicker, { props: { roles: roles() } })
    await wrapper.get('[data-role-skin-role="percival"]').trigger('click')

    const upgrade = document.body.querySelector<HTMLButtonElement>(
      '[data-role-skin-choice="dark-chronicle"]',
    )
    expect(upgrade?.disabled).toBe(true)
    upgrade?.click()
    await nextTick()

    expect(wrapper.emitted('select')).toBeUndefined()
    expect(document.body.textContent).toContain('再用该角色赢 2 局')
  })
})
