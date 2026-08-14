import { defineAsyncComponent } from 'vue'
import avalonArtwork from '../../assets/game-hall/icons/avalon.webp'
import { socialTableCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'
import { avalonLeaderboard, avalonStats } from './records'
import { avalonRoomShell } from './roomPresentation'
import { avalonRules } from './rules'

export const avalonGame = defineBuiltinGame({
  key: 'avalon',
  catalog: {
    order: 0,
    name: '阿瓦隆',
    players: { min: 5, max: 10 },
    description: '谎言上桌，忠诚接受考验',
    tone: 'gold',
    category: '社交推理',
    artwork: avalonArtwork,
  },
  capabilities: socialTableCapabilities({
    firstPlayer: false,
    replay: true,
    ai: true,
  }),
  presentation: {
    component: defineAsyncComponent(() => import('./AvalonRoomGame.vue')),
    roomLayout: 'wide',
    skinKind: null,
    launcher: {
      kicker: '忠诚与谎言同时入席',
      title: '召集远征议会',
      description: '建立你的议会，邀请熟悉的伙伴，在身份与投票之间决定王国的命运。',
      accent: '#e1bc68',
      glow: '#a77a2d',
    },
    roomShell: avalonRoomShell,
  },
  rules: { ...avalonRules, settingsComponent: RuleSettings },
  records: {
    leaderboard: avalonLeaderboard,
    stats: avalonStats,
    matchDetailComponent: defineAsyncComponent(() => import('./MatchDetail.vue')),
  },
})

export default avalonGame
