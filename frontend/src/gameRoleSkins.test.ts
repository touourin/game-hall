import {
  ROLE_SKINS,
  ROLE_SKIN_ROLES,
  ROLE_SKIN_STORAGE_KEY,
  clearRoleSkinLoadoutLock,
  defaultRoleSkinLoadout,
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

  it('brings the smaller classic Merlin portrait up to the base-set scale', () => {
    expect(roleArtworkFraming('merlin', 'classic-tabletop')).toEqual({
      scale: 1.1,
      originXPercent: 50,
      originYPercent: 36,
    })
    expect(roleArtworkFraming('percival', 'classic-tabletop').scale).toBe(1)
  })

  it('brings stained-glass Percival up to the set scale without cropping its frame', () => {
    expect(roleArtworkFraming('percival', 'stained-glass')).toEqual({
      scale: 1.09,
      originXPercent: 50,
      originYPercent: 50,
      preserveFrame: true,
    })
    expect(roleArtworkFraming('merlin', 'stained-glass').scale).toBe(1)
  })

  it('calibrates the royal-codex portraits while preserving their manuscript frames', () => {
    expect(roleArtworkFraming('merlin', 'royal-codex')).toEqual({
      scale: 1.26,
      originXPercent: 50,
      originYPercent: 42,
      preserveFrame: true,
      treatment: 'codex-ink-wash',
    })
    expect(roleArtworkFraming('percival', 'royal-codex')).toMatchObject({
      scale: 1.08,
      preserveFrame: true,
      treatment: 'codex-ink-wash',
    })
    expect(roleArtworkFraming('mordred', 'royal-codex')).toMatchObject({
      scale: 1.12,
      preserveFrame: true,
      treatment: 'codex-ink-wash',
    })
    expect(roleArtworkFraming('oberon', 'royal-codex')).toMatchObject({
      scale: 1.15,
      treatment: 'codex-ink-wash',
    })
    expect(ROLE_SKIN_ROLES.every(
      (role) => roleArtworkFraming(role.code, 'royal-codex').treatment === 'codex-ink-wash',
    )).toBe(true)
  })

  it('keeps the established ultimate heroes unchanged and corrects the oversized Assassin', () => {
    expect(roleArtworkFraming('merlin', 'grail-myth')).toEqual({
      scale: 1,
      originXPercent: 50,
      originYPercent: 50,
    })
    expect(roleArtworkFraming('percival', 'grail-myth').scale).toBe(1)
    expect(roleArtworkFraming('loyal-servant', 'grail-myth').scale).toBe(1)
    expect(roleArtworkFraming('assassin', 'grail-myth')).toEqual({
      scale: 1.18,
      originXPercent: 50,
      originYPercent: 60,
    })
  })

  it('brings the more distant ultimate-skin portraits closer', () => {
    expect(roleArtworkFraming('morgana', 'grail-myth')).toEqual({
      scale: 1.1,
      originXPercent: 50,
      originYPercent: 29,
    })
    expect(roleArtworkFraming('mordred', 'grail-myth').scale).toBe(1.1)
    expect(roleArtworkFraming('oberon', 'grail-myth').scale).toBe(1.08)
    expect(roleArtworkFraming('minion', 'grail-myth').scale).toBe(1.1)
  })

  it('uses the same framing data in the eight-role preview model', () => {
    const roles = ROLE_SKIN_ROLES.map((role) => ({
      ...role,
      framing: roleArtworkFraming(role.code, 'grail-myth'),
    }))
    expect(roles).toHaveLength(8)
    expect(roles.find((role) => role.code === 'merlin')?.framing.scale).toBe(1)
    expect(roles.find((role) => role.code === 'morgana')?.framing.scale).toBe(1.1)
  })

  it('temporarily reuses the loyal servant artwork for the dissenting courtier', () => {
    for (const skin of ROLE_SKINS) {
      expect(roleArtwork('dissenting_courtier', skin.id)).toBe(
        roleArtwork('loyal_servant', skin.id),
      )
    }
  })

  it('maps the dissenting courtier into the loyal-servant skin family', () => {
    expect(roleSkinRoleCode('dissenting_courtier')).toBe('loyal_servant')
    expect(roleSkinRoleCode('loyal_servant')).toBe('loyal_servant')
    expect(roleSkinRoleCode('unknown')).toBeNull()
  })

  it('maps shadow Merlin into the Merlin skin family', () => {
    for (const skin of ROLE_SKINS) {
      expect(roleArtwork('shadow_merlin', skin.id)).toBe(
        roleArtwork('merlin', skin.id),
      )
    }
    expect(roleSkinRoleCode('shadow_merlin')).toBe('merlin')
  })

  it('stores an independent eight-role loadout per account', () => {
    const loadout = defaultRoleSkinLoadout()
    loadout.merlin = 'dark-chronicle'
    loadout.assassin = 'grail-myth'

    rememberRoleSkinLoadout('account-a', loadout)

    expect(storedRoleSkinLoadout('account-a')).toEqual(loadout)
    expect(storedRoleSkinLoadout('account-b')).toEqual(
      defaultRoleSkinLoadout(),
    )
  })

  it('migrates the previous whole-set preference into all eight roles', () => {
    localStorage.setItem(ROLE_SKIN_STORAGE_KEY, 'stained-glass')

    expect(storedRoleSkinLoadout('legacy-account')).toEqual(
      defaultRoleSkinLoadout('stained-glass'),
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
