// 此文件由 scripts/generate-plugin-registry.mjs 自动生成，请勿手动修改。
export const GENERATED_THIRD_PARTY_GAME_MODULES = [
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
