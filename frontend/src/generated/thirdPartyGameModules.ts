// 此文件由 scripts/generate-plugin-registry.mjs 自动生成，请勿手动修改。
export const GENERATED_THIRD_PARTY_GAME_MODULES = [
  {
    directory: "plugin-cheat-poker",
    manifest: {
      "$schema": "../plugin.schema.json",
      "apiVersion": 1,
      "enabled": true,
      "id": "plugin-cheat-poker",
      "name": "欺诈者",
      "description": "暗扣手牌、真假宣告与全员质疑的 4–6 人吹牛扑克",
      "category": "扑克派对",
      "tone": "cheat-poker",
      "players": {
        "min": 4,
        "max": 6,
        "label": "4–6 人"
      },
      "defaultOptions": {
        "listed": true,
        "allowGuests": true,
        "firstPlayer": "random"
      },
      "ruleLabels": [
        "54 张全部发完",
        "每次 1–3 张",
        "全员可质疑",
        "15 张封堆"
      ]
    },
    loadView: () => import("../../../third_party_games/plugin-cheat-poker/frontend/GameView.vue"),
  },
  {
    directory: "plugin-crazy-futures",
    manifest: {
      "$schema": "../plugin.schema.json",
      "apiVersion": 1,
      "enabled": true,
      "id": "plugin-crazy-futures",
      "name": "疯狂期货",
      "description": "交易四类商品、解读信息牌并管理杠杆风险的 4–8 人金融桌游",
      "category": "金融策略",
      "tone": "crazy-futures",
      "players": {
        "min": 4,
        "max": 8,
        "label": "4–8 人"
      },
      "defaultOptions": {
        "listed": true,
        "allowGuests": true,
        "firstPlayer": "random"
      },
      "ruleLabels": [
        "固定 8 回合",
        "四类商品",
        "2 倍杠杆",
        "蛇形竞价",
        "允许做空",
        "终局现货回归"
      ]
    },
    loadView: () => import("../../../third_party_games/plugin-crazy-futures/frontend/GameView.vue"),
  },
  {
    directory: "plugin-number-vault",
    manifest: {
      "$schema": "../plugin.schema.json",
      "apiVersion": 1,
      "enabled": true,
      "id": "plugin-number-vault",
      "name": "数字密匣",
      "description": "六次机会破解 1–20 之间的秘密数字",
      "category": "单人挑战",
      "tone": "number-vault",
      "players": {
        "min": 1,
        "max": 1,
        "label": "1 人"
      },
      "defaultOptions": {
        "listed": false,
        "allowGuests": true
      },
      "ruleLabels": [
        "1–20 猜数",
        "6 次机会"
      ]
    },
    loadView: () => import("../../../third_party_games/plugin-number-vault/frontend/GameView.vue"),
  },
  {
    directory: "plugin-pyramid-solitaire",
    manifest: {
      "$schema": "../plugin.schema.json",
      "apiVersion": 1,
      "enabled": true,
      "id": "plugin-pyramid-solitaire",
      "name": "金字塔纸牌",
      "description": "配对凑成 13，清空七层 28 张牌的单人计时纸牌挑战",
      "category": "单人纸牌",
      "tone": "pyramid-solitaire",
      "roomLayout": "immersive",
      "players": {
        "min": 1,
        "max": 1,
        "label": "1 人"
      },
      "defaultOptions": {
        "listed": false,
        "allowGuests": true
      },
      "ruleLabels": [
        "七层 28 张",
        "两牌合计 13",
        "K 单独消除",
        "牌库只翻一轮",
        "服务端计时"
      ]
    },
    loadView: () => import("../../../third_party_games/plugin-pyramid-solitaire/frontend/GameView.vue"),
  },
  {
    directory: "plugin-star-stones",
    manifest: {
      "$schema": "../plugin.schema.json",
      "apiVersion": 1,
      "enabled": true,
      "id": "plugin-star-stones",
      "name": "星石争夺",
      "description": "双人轮流取走星石，拿到最后一颗即获胜",
      "category": "双人对战",
      "tone": "star-stones",
      "players": {
        "min": 2,
        "max": 2,
        "label": "2 人"
      },
      "defaultOptions": {
        "listed": true,
        "allowGuests": true,
        "firstPlayer": "random"
      },
      "ruleLabels": [
        "15 颗星石",
        "每次取 1–3 颗"
      ]
    },
    loadView: () => import("../../../third_party_games/plugin-star-stones/frontend/GameView.vue"),
  }
] as const
