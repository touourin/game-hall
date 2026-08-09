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
  storedRoleSkinLoadout,
  storedRoleSkinLoadoutLock,
} from './gameRoleSkins'

describe('Avalon role skin artwork framing', () => {
  beforeEach(() => localStorage.clear())

  it('keeps curated thumbnail framing for consistent character scale', () => {
    expect(roleArtworkFraming('merlin', 'classic-tabletop')).toEqual({
      scale: 1,
      originXPercent: 50,
      originYPercent: 50,
    })
    expect(roleArtworkFraming('percival', 'stained-glass')).toMatchObject({
      scale: 1.09,
      preserveFrame: true,
    })
    expect(roleArtworkFraming('merlin', 'royal-codex')).toMatchObject({
      scale: 1.26,
      originYPercent: 42,
      treatment: 'codex-ink-wash',
    })
    expect(roleArtworkFraming('dissenting_courtier', 'royal-codex')).toMatchObject({
      scale: 1.1,
      originYPercent: 42,
    })
    expect(roleArtworkFraming('assassin', 'grail-myth')).toMatchObject({
      scale: 1.18,
      originYPercent: 60,
    })
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
    loadout.shadow_merlin = 'stained-glass'
    loadout.dissenting_courtier = 'royal-codex'
    loadout.assassin = 'grail-myth'

    rememberRoleSkinLoadout('account-a', loadout)

    expect(storedRoleSkinLoadout('account-a')).toEqual(loadout)
    expect(storedRoleSkinLoadout('account-b')).toEqual(
      defaultRoleSkinLoadout(),
    )
  })

  it('migrates the previous whole-set preference into all nine roles', () => {
    localStorage.setItem(ROLE_SKIN_STORAGE_KEY, 'stained-glass')

    expect(storedRoleSkinLoadout('legacy-account')).toEqual(
      defaultRoleSkinLoadout('stained-glass'),
    )
  })

  it('adds shadow Merlin and the dissenting courtier to a legacy loadout', () => {
    const legacyLoadout = defaultRoleSkinLoadout('classic-tabletop')
    legacyLoadout.merlin = 'royal-codex'
    legacyLoadout.loyal_servant = 'stained-glass'
    delete (legacyLoadout as Partial<typeof legacyLoadout>).shadow_merlin
    delete (legacyLoadout as Partial<typeof legacyLoadout>).dissenting_courtier
    rememberRoleSkinLoadout('legacy-account', legacyLoadout)

    expect(storedRoleSkinLoadout('legacy-account').shadow_merlin).toBe(
      'royal-codex',
    )
    expect(storedRoleSkinLoadout('legacy-account').dissenting_courtier).toBe(
      'stained-glass',
    )
  })

  it('locks and clears the full role loadout for one room', () => {
    const loadout = defaultRoleSkinLoadout()
    loadout.loyal_servant = 'royal-codex'

    expect(lockRoleSkinLoadout(' test ', loadout)).toEqual(loadout)
    expect(storedRoleSkinLoadoutLock('TEST')).toEqual(loadout)
    clearRoleSkinLoadoutLock('TEST')
    expect(storedRoleSkinLoadoutLock('TEST')).toBeNull()
  })
})
