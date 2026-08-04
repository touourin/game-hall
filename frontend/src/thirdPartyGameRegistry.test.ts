import {
  THIRD_PARTY_GAME_PLUGINS,
  validateThirdPartyGameManifest,
} from './thirdPartyGameRegistry'

describe('third-party game registry', () => {
  it('registers the enabled single-player and multiplayer examples', () => {
    expect(THIRD_PARTY_GAME_PLUGINS.map(({ manifest }) => manifest.id)).toEqual([
      'plugin-number-vault',
      'plugin-star-stones',
    ])
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
      players: { min: 2, max: 4 },
    }, 'plugin-sample-game')

    expect(manifest?.id).toBe('plugin-sample-game')
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
