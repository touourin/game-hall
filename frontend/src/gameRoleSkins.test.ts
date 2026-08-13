import {
  ROLE_SKINS,
  ROLE_SKIN_ROLES,
  ROLE_SKIN_STORAGE_KEY,
  clearRoleSkinLoadoutLock,
  defaultRoleSkinLoadout,
  isRoleSkinAvailable,
  lockRoleSkinLoadout,
  rememberRoleSkinLoadout,
  roleArtwork,
  roleArtworkFraming,
  roleSkinRoleCode,
  storedRoleSkin,
  storedRoleSkinLoadout,
  storedRoleSkinLoadoutLock,
} from './gameRoleSkins'

describe('Avalon role skin artwork framing', () => {
  beforeEach(() => localStorage.clear())

  it('exposes only the three active skin families', () => {
    expect(ROLE_SKINS.map((skin) => skin.id)).toEqual([
      'classic-tabletop',
      'dark-chronicle',
      'grail-myth',
    ])
  })

  it('keeps curated thumbnail framing for consistent character scale', () => {
    expect(roleArtworkFraming('merlin', 'classic-tabletop')).toEqual({
      scale: 1,
      originXPercent: 50,
      originYPercent: 50,
    })
    for (const role of ROLE_SKIN_ROLES) {
      expect(roleArtworkFraming(role.code, 'grail-myth')).toEqual({
        scale: 1,
        originXPercent: 50,
        originYPercent: 50,
      })
    }
    expect(roleArtworkFraming('shadow_merlin', 'classic-tabletop')).toEqual({
      scale: 1,
      originXPercent: 50,
      originYPercent: 50,
    })
  })

  it('uses dedicated dissenting courtier artwork in every skin family', () => {
    for (const skin of ROLE_SKINS) {
      expect(roleArtwork('dissenting_courtier', skin.id)).not.toBe(
        roleArtwork('loyal_servant', skin.id),
      )
      expect(isRoleSkinAvailable('dissenting_courtier', skin.id)).toBe(true)
    }
  })

  it('keeps the dissenting courtier independently selectable', () => {
    expect(roleSkinRoleCode('dissenting_courtier')).toBe('dissenting_courtier')
    expect(roleSkinRoleCode('loyal_servant')).toBe('loyal_servant')
    expect(roleSkinRoleCode('unknown')).toBeNull()
  })

  it('uses dedicated shadow Merlin artwork in every skin family', () => {
    const artworks = ROLE_SKINS.map((skin) => (
      roleArtwork('shadow_merlin', skin.id)
    ))
    expect(new Set(artworks)).toHaveLength(ROLE_SKINS.length)
    for (const skin of ROLE_SKINS) {
      expect(roleArtwork('shadow_merlin', skin.id)).not.toBe(
        roleArtwork('merlin', skin.id),
      )
      expect(isRoleSkinAvailable('shadow_merlin', skin.id)).toBe(true)
    }
    expect(roleSkinRoleCode('shadow_merlin')).toBe('shadow_merlin')
  })

  it('stores an independent ten-role loadout per account', () => {
    const loadout = defaultRoleSkinLoadout()
    loadout.merlin = 'dark-chronicle'
    loadout.shadow_merlin = 'dark-chronicle'
    loadout.dissenting_courtier = 'grail-myth'
    loadout.assassin = 'grail-myth'

    rememberRoleSkinLoadout('account-a', loadout)

    expect(storedRoleSkinLoadout('account-a')).toEqual(loadout)
    expect(storedRoleSkinLoadout('account-b')).toEqual(
      defaultRoleSkinLoadout(),
    )
  })

  it('migrates the previous whole-set preference into all ten roles', () => {
    localStorage.setItem(ROLE_SKIN_STORAGE_KEY, 'dark-chronicle')

    expect(storedRoleSkinLoadout('legacy-account')).toEqual(
      defaultRoleSkinLoadout('dark-chronicle'),
    )
  })

  it('adds shadow Merlin and the dissenting courtier to a legacy loadout', () => {
    const legacyLoadout = defaultRoleSkinLoadout('classic-tabletop')
    legacyLoadout.merlin = 'dark-chronicle'
    legacyLoadout.loyal_servant = 'grail-myth'
    delete (legacyLoadout as Partial<typeof legacyLoadout>).shadow_merlin
    delete (legacyLoadout as Partial<typeof legacyLoadout>).dissenting_courtier
    rememberRoleSkinLoadout('legacy-account', legacyLoadout)

    expect(storedRoleSkinLoadout('legacy-account').shadow_merlin).toBe(
      'dark-chronicle',
    )
    expect(storedRoleSkinLoadout('legacy-account').dissenting_courtier).toBe(
      'grail-myth',
    )
  })

  it('falls back only removed or invalid selections to the classic skin', () => {
    const stored = defaultRoleSkinLoadout('dark-chronicle') as Record<string, string>
    stored.merlin = 'removed-skin'
    localStorage.setItem(
      'avalon:role-skin-loadout:legacy-account',
      JSON.stringify(stored),
    )

    const migrated = storedRoleSkinLoadout('legacy-account')
    expect(migrated.merlin).toBe('classic-tabletop')
    expect(migrated.percival).toBe('dark-chronicle')
    expect(JSON.parse(localStorage.getItem(
      'avalon:role-skin-loadout:legacy-account',
    ) ?? '{}')).toEqual(migrated)
  })

  it('rewrites an invalid legacy whole-set preference to the classic skin', () => {
    localStorage.setItem(ROLE_SKIN_STORAGE_KEY, 'removed-skin')

    expect(storedRoleSkin()).toBe('classic-tabletop')
    expect(localStorage.getItem(ROLE_SKIN_STORAGE_KEY)).toBe('classic-tabletop')
  })

  it('locks and clears the full role loadout for one room', () => {
    const loadout = defaultRoleSkinLoadout()
    loadout.loyal_servant = 'dark-chronicle'

    expect(lockRoleSkinLoadout(' test ', loadout)).toEqual(loadout)
    expect(storedRoleSkinLoadoutLock('TEST')).toEqual(loadout)
    clearRoleSkinLoadoutLock('TEST')
    expect(storedRoleSkinLoadoutLock('TEST')).toBeNull()
  })
})
