import { defineAsyncComponent } from 'vue'
import junqiArtwork from '../../assets/game-hall/icons/junqi.webp'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import RuleSettings from './RuleSettings.vue'
import { junqiStats } from './records'
import { junqiRules } from './rules'

export const junqiGame = defineBuiltinGame({
  key: 'junqi',
  catalog: {
    order: 90,
    name: '军旗',
    players: { min: 2, max: 2 },
    description: '秘密布阵，沿铁路突袭敌旗',
    tone: 'army',
    category: '棋类竞技',
    artwork: junqiArtwork,
  },
  capabilities: {
    undo: false,
    draw: false,
    guests: true,
    spectators: true,
    firstPlayer: true,
    replay: false,
    ai: false,
  },
  presentation: {
    component: defineAsyncComponent(() => import('./JunqiBoard.vue')),
    roomLayout: 'wide',
    skinKind: 'board',
    roomShell: {
      headerEyebrowSuffix: (snapshot) =>
        ` · ${snapshot.options.mode === 'flip' ? '翻棋军旗' : '暗军旗'}`,
    },
  },
  rules: { ...junqiRules, settingsComponent: RuleSettings },
  records: {
    stats: junqiStats,
  },
})

export default junqiGame
