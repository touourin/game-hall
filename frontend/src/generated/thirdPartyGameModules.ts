// 此文件由 scripts/generate-plugin-registry.mjs 自动生成，请勿手动修改。
export const GENERATED_THIRD_PARTY_GAME_MODULES = [
  {
    directory: "plugin-cheat-poker",
    status: "enabled",
    order: 100,
    manifest: {
      "$schema": "../plugin.schema.json",
      "apiVersion": 1,
      "version": "1.0.0",
      "author": "Game Hall Contributors",
      "license": "UNLICENSED",
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
      "capabilities": {
        "guests": true,
        "spectators": true,
        "spectatorFrames": false,
        "firstPlayer": true,
        "undoActions": [],
        "drawRequests": false,
        "replay": false,
        "ai": false
      },
      "records": {
        "scoreKind": "outcome"
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
    status: "enabled",
    order: 110,
    manifest: {
      "$schema": "../plugin.schema.json",
      "apiVersion": 1,
      "version": "1.0.0",
      "author": "Game Hall Contributors",
      "license": "UNLICENSED",
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
      "capabilities": {
        "guests": true,
        "spectators": true,
        "spectatorFrames": false,
        "firstPlayer": true,
        "undoActions": [],
        "drawRequests": false,
        "replay": false,
        "ai": false
      },
      "records": {
        "scoreKind": "outcome"
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
    directory: "plugin-pyramid-solitaire",
    status: "enabled",
    order: 120,
    manifest: {
      "$schema": "../plugin.schema.json",
      "apiVersion": 1,
      "version": "1.0.0",
      "author": "Game Hall Contributors",
      "license": "UNLICENSED",
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
      "capabilities": {
        "guests": false,
        "spectators": true,
        "spectatorFrames": false,
        "firstPlayer": false,
        "undoActions": [],
        "drawRequests": false,
        "replay": false,
        "ai": false
      },
      "records": {
        "scoreKind": "time_trial"
      },
      "defaultOptions": {
        "listed": false
      },
      "ruleLabels": [
        "七层 28 张",
        "两牌合计 13",
        "K 单独消除",
        "牌库只翻一轮",
        "保证存在解法",
        "服务端计时"
      ]
    },
    loadView: () => import("../../../third_party_games/plugin-pyramid-solitaire/frontend/GameView.vue"),
  }
] as const
