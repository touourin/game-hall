import { defineAsyncComponent } from 'vue'
import pixelPushArtworkDark from '../../assets/game-hall/icons/pixel-push-dark.webp'
import pixelPushArtworkLight from '../../assets/game-hall/icons/pixel-push-light.webp'
import { socialTableCapabilities } from '../../game-platform/capabilities'
import { defineBuiltinGame } from '../../game-platform/defineGame'
import { createCompetitiveStatsPresentation } from '../../game-platform/recordFormatting'

const MAP_LABELS: Record<string, string> = {
  rotation: '三图轮换',
  moon_station: '月台零号',
  cross_bridge: '十字断桥',
  pulse_factory: '脉冲工厂',
}

export const pixelPushGame = defineBuiltinGame({
  key: 'pixel_push',
  catalog: {
    order: 95,
    name: '像素推推王',
    players: { min: 2, max: 4 },
    description: '冲刺撞击，把对手推出像素擂台',
    tone: 'pixel-push',
    category: '多人派对',
    artwork: { dark: pixelPushArtworkDark, light: pixelPushArtworkLight },
  },
  capabilities: socialTableCapabilities({ firstPlayer: false }),
  presentation: {
    component: defineAsyncComponent(() => import('./PixelPushArena.vue')),
    roomLayout: 'immersive',
    skinKind: null,
    launcher: {
      kicker: '冲刺 · 稳住 · 最后留在场上',
      title: '开启像素擂台乱斗',
      description: '邀请 2–4 名玩家，在收缩擂台中寻找角度、抵住冲击，把所有对手推入虚空。',
      accent: '#5ce1e6',
      glow: '#1e8793',
    },
    roomShell: {
      activeExitDescription: '暂时返回会立即清空操作；连续离线 5 秒将在当前回合淘汰，重连后可从下一回合继续。',
      abandonLabel: '退出并认输',
      finishedLabel: '擂台结束',
      rematchLabel: '准备再战',
    },
  },
  rules: {
    settingsGroups: [
      {
        key: 'arena',
        title: '首发擂台',
        description: '轮换模式会在每个回合切换地图；固定模式整场使用同一张地图',
        control: 'cards',
        columns: 2,
        options: [
          ['rotation', '三图轮换', '月台、断桥与工厂依次登场'],
          ['moon_station', '月台零号', '标准圆角擂台，纯粹比拼走位'],
          ['cross_bridge', '十字断桥', '四条短臂逐步坍塌，边缘更危险'],
          ['pulse_factory', '脉冲工厂', '周期脉冲横扫场地，改变站位'],
        ],
      },
    ],
    defaults: {
      allowGuests: true,
      allowSpectators: true,
      arena: 'rotation',
    },
    labels: (options) => [
      '2–4 人',
      '先胜 2 回合',
      '45 秒回合',
      MAP_LABELS[String(options.arena)] ?? '三图轮换',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ],
  },
  records: {
    stats: createCompetitiveStatsPresentation({
      roleLabels: {
        seat_1: '青色选手',
        seat_2: '红色选手',
        seat_3: '黄色选手',
        seat_4: '紫色选手',
      },
      winnerLabel: () => '最后留在擂台的玩家获胜',
    }),
  },
})

export default pixelPushGame
