import { defineComponent } from 'vue'
import { GENERATED_THIRD_PARTY_GAME_MODULES } from './generated/thirdPartyGameModules'
import {
  buildThirdPartyGameRegistration,
  THIRD_PARTY_GAME_REGISTRATIONS,
  type GeneratedPluginModule,
  type ThirdPartyGameManifest,
} from './thirdPartyGameRegistry'

describe('third-party game registrations', () => {
  it('adapts every generated module without knowing concrete plugin ids', () => {
    const generatedModules = (
      GENERATED_THIRD_PARTY_GAME_MODULES as readonly GeneratedPluginModule[]
    )
    expect(THIRD_PARTY_GAME_REGISTRATIONS.map(({ key }) => key)).toEqual([
      ...generatedModules.map(({ manifest }) => manifest.id),
    ])
    expect(THIRD_PARTY_GAME_REGISTRATIONS.every(
      ({ source }) => source === 'third_party',
    )).toBe(true)
  })

  it('adapts plugin metadata to the shared game registration contract', () => {
    const manifest = {
      apiVersion: 1,
      version: '1.2.3',
      author: 'Test Author',
      license: 'UNLICENSED',
      id: 'plugin-test-game',
      name: '测试插件',
      description: '用于验证主项目插件适配器',
      category: '测试游戏',
      tone: 'test-game',
      roomLayout: 'immersive',
      players: { min: 1, max: 1, label: '1 人' },
      capabilities: {
        guests: false,
        spectators: true,
        spectatorFrames: false,
        firstPlayer: false,
        undoActions: [],
        drawRequests: false,
        replay: false,
        ai: false,
      },
      records: { scoreKind: 'time_trial' },
      defaultOptions: { listed: false },
    } as const satisfies ThirdPartyGameManifest
    const generated: GeneratedPluginModule = {
      directory: 'plugin-test-game',
      status: 'enabled',
      order: 100,
      manifest,
      loadView: async () => ({ default: defineComponent({ template: '<main />' }) }),
    }

    const registration = buildThirdPartyGameRegistration(generated)

    expect(registration).toMatchObject({
      key: 'plugin-test-game',
      source: 'third_party',
      availability: 'enabled',
      catalog: {
        name: '测试插件',
        players: { min: 1, max: 1 },
      },
      capabilities: {
        guests: false,
        spectators: true,
        spectatorFrames: false,
        firstPlayer: false,
      },
      presentation: { roomLayout: 'immersive' },
      plugin: { version: '1.2.3' },
      records: { scoreKind: 'time_trial' },
    })
    expect(registration.rules.defaults).toMatchObject({
      allowSpectators: true,
    })
    expect(registration.records?.leaderboard?.entryScore({
      rank: 1,
      accountId: 'a1',
      playerName: '玩家一',
      games: 1,
      wins: 1,
      draws: 0,
      winRate: 100,
      bestMs: 65_400,
    })).toBe('1 分 5 秒')
  })
})
