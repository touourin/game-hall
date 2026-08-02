import {
  roleArtworkFraming,
  roleSkinPreviewRoles,
} from './roleSkins'

describe('Avalon role skin artwork framing', () => {
  it('keeps the established ultimate-skin hero cards unchanged', () => {
    expect(roleArtworkFraming('merlin', 'grail-myth')).toEqual({
      scale: 1,
      originXPercent: 50,
      originYPercent: 50,
    })
    expect(roleArtworkFraming('assassin', 'grail-myth').scale).toBe(1)
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
})
