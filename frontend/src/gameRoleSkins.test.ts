import {
  ROLE_SKINS,
  roleArtwork,
  roleArtworkFraming,
  roleSkinPreviewRoles,
} from './gameRoleSkins'

describe('Avalon role skin artwork framing', () => {
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

  it('finishes the restrained royal-codex Merlin composition correction', () => {
    expect(roleArtworkFraming('merlin', 'royal-codex')).toEqual({
      scale: 1.16,
      originXPercent: 50,
      originYPercent: 50,
      preserveFrame: true,
    })
    expect(roleArtworkFraming('percival', 'royal-codex').scale).toBe(1)
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
    const roles = roleSkinPreviewRoles('grail-myth')
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
})
