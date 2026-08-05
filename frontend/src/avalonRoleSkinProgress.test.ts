import {
  emptyAvalonRoleSkinProgress,
  isRoleSkinUnlocked,
  loadAvalonRoleSkinProgress,
} from './avalonRoleSkinProgress'
import { rememberAccessToken } from './access'
import { rememberAccountToken } from './account'

describe('Avalon role skin progression', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  afterEach(() => vi.unstubAllGlobals())

  it('always allows base skins and unlocks every upgrade style together', () => {
    const progress = emptyAvalonRoleSkinProgress()
    progress.roles.merlin.wins = 2
    progress.roles.merlin.upgradeUnlocked = true

    expect(isRoleSkinUnlocked(progress, 'merlin', 'classic-tabletop')).toBe(true)
    expect(isRoleSkinUnlocked(progress, 'merlin', 'dark-chronicle')).toBe(true)
    expect(isRoleSkinUnlocked(progress, 'merlin', 'stained-glass')).toBe(true)
    expect(isRoleSkinUnlocked(progress, 'merlin', 'royal-codex')).toBe(true)
    expect(isRoleSkinUnlocked(progress, 'merlin', 'grail-myth')).toBe(false)
  })

  it('shares loyal-servant unlocks with the dissenting courtier', () => {
    const progress = emptyAvalonRoleSkinProgress()
    progress.roles.loyal_servant.wins = 5
    progress.roles.loyal_servant.upgradeUnlocked = true
    progress.roles.loyal_servant.ultimateUnlocked = true

    expect(
      isRoleSkinUnlocked(progress, 'dissenting_courtier', 'grail-myth'),
    ).toBe(true)
  })

  it('offers only the classic skin to shadow Merlin for now', () => {
    const progress = emptyAvalonRoleSkinProgress()
    progress.legacyAllUnlocked = true

    expect(
      isRoleSkinUnlocked(progress, 'shadow_merlin', 'classic-tabletop'),
    ).toBe(true)
    expect(
      isRoleSkinUnlocked(progress, 'shadow_merlin', 'dark-chronicle'),
    ).toBe(false)
    expect(
      isRoleSkinUnlocked(progress, 'shadow_merlin', 'grail-myth'),
    ).toBe(false)
  })

  it('keeps every style available to legacy accounts', () => {
    const progress = emptyAvalonRoleSkinProgress()
    progress.legacyAllUnlocked = true

    expect(isRoleSkinUnlocked(progress, 'oberon', 'grail-myth')).toBe(true)
  })

  it('turns an invalid server response into a readable error', async () => {
    rememberAccessToken('access-token')
    rememberAccountToken('account-token')
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('<!doctype html>', { status: 200 })),
    )

    await expect(loadAvalonRoleSkinProgress()).rejects.toThrow(
      '身份皮肤进度读取失败',
    )
  })
})
