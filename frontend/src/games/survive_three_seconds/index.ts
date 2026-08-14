import { defineAsyncComponent } from 'vue'
import surviveArtwork from '../../assets/game-hall/icons/survive-three-seconds.webp'
import { soloGameCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import {
  surviveThreeSecondsLeaderboard,
  surviveThreeSecondsStats,
} from './records'
import { surviveThreeSecondsSoloPresentation } from './soloPresentation'

export const surviveThreeSecondsGame = defineBuiltinGame({
  key: 'survive_three_seconds',
  catalog: {
    order: 130,
    name: '坚持三秒',
    players: { min: 1, max: 1 },
    description: '看清三段弹幕缺口，远离边缘撑过三秒',
    tone: 'barrage',
    category: '个人挑战',
    artwork: surviveArtwork,
  },
  capabilities: soloGameCapabilities(),
  presentation: {
    component: defineAsyncComponent(() => import('./SurviveThreeSecondsGame.vue')),
    roomLayout: 'standard',
    skinKind: null,
    roomShell: {
      headerEyebrowSuffix: () => ' · 三秒极限闪避',
      headerTitle: () => '坚持三秒',
    },
    solo: surviveThreeSecondsSoloPresentation,
  },
  rules: {
    defaults: { allowSpectators: false },
    labels: () => ['3 秒极限挑战', '服务端轨迹重放'],
  },
  records: {
    leaderboard: surviveThreeSecondsLeaderboard,
    stats: surviveThreeSecondsStats,
    matchDetailComponent: defineAsyncComponent(() => import('./MatchDetail.vue')),
  },
})

export default surviveThreeSecondsGame
