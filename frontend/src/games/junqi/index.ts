import { defineAsyncComponent } from 'vue'
import junqiArtwork from '../../assets/game-hall/icons/junqi.webp'
import { boardDuelCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
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
  capabilities: boardDuelCapabilities({ undo: false, draw: false }),
  presentation: {
    component: defineAsyncComponent(() => import('./JunqiBoard.vue')),
    roomLayout: 'wide',
    skinKind: 'board',
    launcher: {
      kicker: '暗中布阵，铁路突袭',
      title: '建立前线指挥所',
      description: '选择暗棋或翻棋模式，与对手在隐蔽信息中争夺最后的军旗。',
      accent: '#b4bd75',
      glow: '#687039',
    },
    roomShell: {
      headerEyebrowSuffix: (snapshot) =>
        ` · ${snapshot.options.mode === 'flip' ? '翻棋军旗' : '暗军旗'}`,
    },
  },
  rules: junqiRules,
  records: {
    stats: junqiStats,
  },
})

export default junqiGame
