import {
  THIRD_PARTY_GAME_PLUGINS,
  thirdPartyGameRoomLayout,
  validateThirdPartyGameManifest,
} from './thirdPartyGameRegistry'

describe('third-party game registry', () => {
  it('registers the enabled single-player and multiplayer examples', () => {
    expect(THIRD_PARTY_GAME_PLUGINS.map(({ manifest }) => manifest.id)).toEqual(expect.arrayContaining([
      'plugin-cheat-poker',
      'plugin-crazy-futures',
      'plugin-number-vault',
      'plugin-pyramid-solitaire',
      'plugin-star-stones',
    ]))
  })

  it('accepts a valid v1 plugin manifest', () => {
    const manifest = validateThirdPartyGameManifest({
      apiVersion: 1,
      enabled: true,
      id: 'plugin-sample-game',
      name: '示例游戏',
      description: '用于验证插件协议',
      category: '插件游戏',
      tone: 'sample',
      roomLayout: 'immersive',
      players: { min: 2, max: 4 },
    }, 'plugin-sample-game')

    expect(manifest?.id).toBe('plugin-sample-game')
    expect(manifest?.roomLayout).toBe('immersive')
  })

  it('exposes a safe room layout and rejects unknown layout values', () => {
    expect(thirdPartyGameRoomLayout('plugin-pyramid-solitaire')).toBe('immersive')
    expect(thirdPartyGameRoomLayout('plugin-number-vault')).toBe('standard')
    expect(validateThirdPartyGameManifest({
      apiVersion: 1,
      enabled: true,
      id: 'plugin-invalid-layout',
      name: '错误插件',
      description: '错误宽度请求',
      category: '插件',
      tone: 'bad-layout',
      roomLayout: 'fullscreen',
      players: { min: 1, max: 1 },
    }, 'plugin-invalid-layout')).toBeNull()
  })

  it('rejects unsafe keys, mismatched directories, and invalid player counts', () => {
    expect(validateThirdPartyGameManifest({
      apiVersion: 1,
      enabled: true,
      id: '../unsafe',
      name: '错误插件',
      description: '错误插件',
      category: '插件',
      tone: 'bad',
      players: { min: 0, max: 99 },
    }, 'plugin-safe')).toBeNull()
  })
})
