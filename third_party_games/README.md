# 第三方游戏接入手册

本地开发目录 `/Users/ourin/project/game-hall/third_party_games` 是本项目放置第三方游戏源码的唯一位置；服务器上的对应位置是 `/opt/game-hall/third_party_games`。每款游戏拥有一个完全独立的子目录，不要把某款第三方游戏的页面、规则、图片或后端逻辑散落到 `frontend/src`、`backend/app` 或其他主项目目录。

插件通过清单自动注册，不需要修改大厅、路由、房间页、账号系统、Socket 连接或后端游戏注册表。启用后，游戏会出现在大厅的“第三方游戏”入口中，并复用现有的账号、游客、创建/加入房间、邀请、聊天、断线保护、对局战绩、排行榜和响应式房间外壳。

> 当前 API v1 是“经代码审核后随主项目一起构建”的源码插件，不是可以安全运行任意陌生代码的沙箱。未经信任的代码应改用独立服务和 iframe 隔离，不能直接启用。

## 一、目录规则

目录名和插件 ID 必须一致，并以 `plugin-` 开头：

```text
third_party_games/
├── README.md
├── plugin.schema.json
├── plugin-counter-demo/             # 默认关闭的完整示例
└── plugin-your-game/                 # 你的游戏，目录名 = manifest.id
    ├── manifest.json                 # 必需：插件信息和启用开关
    ├── README.md                     # 必需：玩法、动作和维护说明
    ├── backend/
    │   ├── plugin.py                 # 必需：固定后端入口
    │   ├── engine.py                 # 可选：已有规则引擎
    │   ├── state.py                  # 可选：状态模型
    │   └── ...                       # 可继续拆分本游戏自己的 Python 文件
    ├── frontend/
    │   ├── GameView.vue              # 必需：固定前端入口
    │   ├── components/               # 可选：本游戏自己的 Vue 组件
    │   ├── composables/               # 可选：本游戏自己的前端逻辑
    │   └── assets/                   # 可选：本游戏自己的图片、字体等资源
    └── tests/                        # 建议：本游戏的规则和界面测试
```

自动发现器只把 `manifest.json`、`backend/plugin.py` 和 `frontend/GameView.vue` 当作入口，但入口可以用相对路径导入同一插件目录内的其他文件。例如 `plugin.py` 可以写 `from .engine import ExistingEngine`，Vue 文件也可以写 `import Board from './components/Board.vue'`。

## 二、最快接入一款新游戏

在项目根目录执行：

```bash
cp -R third_party_games/plugin-counter-demo third_party_games/plugin-your-game
```

然后依次完成：

1. 把目录改为唯一的 `plugin-*` ID。
2. 修改 `manifest.json`，确保 `id` 与目录名完全一致，开发期间保持 `enabled: false`。
3. 在 `backend/` 实现规则、状态、胜负和给不同玩家看的数据。
4. 在 `frontend/` 实现棋盘或操作界面。
5. 为关键规则和主要操作补测试。
6. 本地执行 `npm test && npm run build`。
7. 最后把 `enabled` 改为 `true`，重新执行测试和构建。
8. 重启服务。插件会自动出现在“第三方游戏”入口，无需再改大厅代码。

接入框架已经存在后，一款普通新插件的提交原则上只能修改 `third_party_games/plugin-your-game/`。如果 `git diff --name-only` 还出现该目录以外的文件，应先确认它确实是所有插件都需要的通用框架升级，并将其与单款游戏代码分开审查。

可以先阅读默认示例：

- `plugin-counter-demo/manifest.json`：完整清单。
- `plugin-counter-demo/backend/plugin.py`：最小规则引擎。
- `plugin-counter-demo/frontend/GameView.vue`：动作发送和状态展示。

## 三、把已经写好的游戏逻辑迁进来

不要重写已有规则本身，先加一层适配器。推荐按以下顺序迁移。

### 1. 先把原文件完整移入插件目录

- Python 规则、状态、牌库、棋盘算法：放进 `backend/`。
- Vue 组件、TypeScript 工具、CSS、图片：放进 `frontend/`。
- 原项目的测试数据和单元测试：放进 `tests/`。
- 不要保留对原仓库绝对路径的引用；全部改为插件目录内的相对导入。

已有后端逻辑可以保留在 `backend/engine.py`，只让固定入口负责创建引擎：

```python
# third_party_games/plugin-your-game/backend/plugin.py
from .engine import ExistingGameEngine


def create_engine():
    return ExistingGameEngine()
```

已有前端主界面可以保留为单独组件，再由固定入口承接大厅快照：

```vue
<!-- third_party_games/plugin-your-game/frontend/GameView.vue -->
<script setup lang="ts">
import ExistingGame from './components/ExistingGame.vue'
import type { ArcadeSnapshot } from '@game-hall/plugin-sdk'

defineProps<{ snapshot: ArcadeSnapshot }>()
</script>

<template>
  <ExistingGame :snapshot="snapshot" />
</template>
```

### 2. 把原来的通信改成统一动作协议

插件页面不能自己连接 Socket，也不要直接请求主项目内部接口。前端通过稳定 SDK 发动作：

```ts
import { usePluginGameActions } from '@game-hall/plugin-sdk'

const actions = usePluginGameActions()

// action 名称由当前插件自己定义，payload 必须可 JSON 序列化
await actions.action('move', { from: 12, to: 20 })
await actions.action('play_card', { cardId: 'heart-7' })

// 高频但允许丢弃中间响应的交互，例如拖动或连续点击
actions.rapidAction('aim', { x: 0.42, y: 0.68 })
```

后端在 `act()` 中接收完全相同的 `action` 和 `payload`，验证当前玩家是否允许执行，再修改服务端状态：

```python
def act(self, room, player, action, payload):
    if action != "move":
        raise GameRuleError("不支持这个操作")
    if player.id != room.state.current_player_id:
        raise GameRuleError("还没有轮到你")
    apply_existing_move_logic(room.state, payload["from"], payload["to"])
```

也就是说，迁移时通常只需要替换原来的 HTTP/WebSocket 控制层，棋盘判定、出牌规则、计分算法可以继续使用。

### 3. 把原状态映射到大厅房间生命周期

已有逻辑需要适配下面六个方法：

| 插件方法 | 接入已有逻辑时负责什么 |
| --- | --- |
| `initial_state()` | 返回未开局的初始状态；不要放账号令牌或不可序列化的外部连接 |
| `start(room)` | 按房间玩家和规则初始化一局，并设置 `room.phase = "playing"` |
| `act(room, player, action, payload)` | 校验玩家动作并调用已有规则逻辑；非法动作抛 `GameRuleError` |
| `view(room, viewer)` | 返回给当前观看者的 `snapshot.game`，在这里过滤手牌、身份等隐藏信息 |
| `player_result(room, player)` | 返回 `(角色, 阵营, 是否获胜)`，用于战绩和排行榜 |
| `create_engine()` | 返回本游戏引擎实例，是后端唯一固定入口 |

判定结束后调用公共房间能力，不要另建一套结算接口：

```python
room.finish(
    "red",                       # 胜方/胜利类型
    [winner_player.id],           # 获胜玩家 ID 列表
    "红方率先完成目标",          # 对局结果说明
)
```

`view()` 是防止信息泄露的关键边界。服务端真实状态可以保存所有手牌或身份，但返回给每位 `viewer` 的字典只能包含该玩家当前应该看到的信息。

### 4. 处理原技术栈差异

- 原前端是 Vue 3：可直接移入并用 `GameView.vue` 包装。
- 原前端是原生 HTML/Canvas：把初始化和绘制逻辑放进 Vue 组件的 `onMounted()`，动作仍通过插件 SDK 发送。
- 原前端是 React/Svelte：API v1 不会额外打包这些运行时，建议迁成 Vue 3；不要擅自修改根依赖。
- 原后端是 Python：通常只需实现上面的引擎适配器。
- 原后端是 Node、Java、Go 或独立服务：不能直接作为进程内插件加载；需要迁成 Python 引擎，或另行设计经过审核的“远程插件 API”。
- 原游戏自带登录、房间、聊天、战绩：删除这些重复模块，使用大厅提供的公共能力。

## 四、manifest.json

完整字段约束见同目录的 `plugin.schema.json`。示例：

```json
{
  "$schema": "../plugin.schema.json",
  "apiVersion": 1,
  "enabled": false,
  "id": "plugin-your-game",
  "name": "游戏名称",
  "description": "显示在第三方游戏入口中的一句话简介",
  "category": "棋类竞技",
  "tone": "your-game",
  "players": {
    "min": 2,
    "max": 4,
    "label": "2–4 人"
  },
  "defaultOptions": {
    "listed": true,
    "allowGuests": true,
    "firstPlayer": "random"
  },
  "ruleLabels": ["公开房间", "允许游客"]
}
```

- `apiVersion`：当前必须为 `1`。
- `enabled`：只有严格等于 `true` 才会注册；开发和迁移阶段应保持 `false`。
- `id`：以 `plugin-` 开头，最长 32 位，只能包含小写字母、数字和连字符。
- `name`：1–24 个字符，并且必须与后端引擎的 `name` 一致。
- `players.min/max`：1–20 人，并且必须与后端引擎人数一致。
- `players.label`：可选，控制入口展示的人数文案。
- `defaultOptions`：创建房间时合并进公共默认规则。
- `ruleLabels`：房间规则摘要，最多 6 条。
- `tone`：当前插件的稳定视觉标识，不允许用它覆盖主项目全局样式。

目录名、`manifest.id`、后端 `engine.key` 三者必须完全一致；`manifest.name` 与 `engine.name` 也必须一致。

## 五、前后端契约

### 后端入口

`backend/plugin.py` 必须导出无参数函数：

```python
def create_engine():
    return YourEngine()
```

引擎需实现 `backend.app.games.base.GameEngine` 约定，并提供：

- `key`、`name`、`min_players`、`max_players`
- `initial_state()`
- `start(room)`
- `act(room, player, action, payload)`
- `view(room, viewer)`
- `player_result(room, player)`

插件加载异常时会禁用当前插件，不影响其他游戏和大厅启动。

### 前端入口

`frontend/GameView.vue` 必须接收一个 `snapshot` 属性：

```ts
import {
  usePluginGameActions,
  type ArcadeSnapshot,
} from '@game-hall/plugin-sdk'

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const actions = usePluginGameActions()
```

常用数据：

- `snapshot.self`：当前玩家。
- `snapshot.players`：房间成员。
- `snapshot.phase`：当前阶段。
- `snapshot.actions.canAct`：公共外壳判定当前玩家是否可操作。
- `snapshot.game`：后端 `view()` 返回的当前玩家可见状态。

样式必须使用 `<style scoped>`；根元素应有 `min-width: 0; max-width: 100%`。至少检查 320、375、390、768、1024、1440 像素宽度，不能产生页面级横向滚动，触控按钮最小点击区域建议为 44×44 像素。

## 六、禁止事项和隔离边界

- 不要为单个插件修改 `frontend/src`、`backend/app`、大厅路由或根依赖文件。
- 不要把第三方游戏文件放到 `frontend/src/games` 或 `backend/app/games`。
- 不要使用全局 CSS、覆盖 `document.body`、改变根主题变量或写死页面宽高。
- 不要读取账号令牌、访问令牌、Cookie、localStorage 或 sessionStorage。
- 不要直接连接 Socket；只使用 `@game-hall/plugin-sdk`。
- 不要把客户端传来的坐标、牌 ID、分数或胜负结果当成可信数据，必须由后端验证。
- 第三方依赖必须先经项目维护者审核，不能自行修改根 `package.json` 或 `pyproject.toml`。
- 不要在 `enabled: true` 前跳过完整测试和手机端检查。

这些规则能保证经过审核的插件在源码和维护层面不污染其他目录，但 API v1 仍是同进程源码插件，并不是对恶意代码的安全沙箱。插件后端与主服务运行在同一个 Python 进程，插件前端也会进入主站构建；如果接入不可信代码，必须升级为独立容器/进程、独立域名的 sandbox iframe 和受限消息协议。

删除插件目录并重启即可卸载。卸载前要先结束该插件仍未完成的房间，否则这些房间会因为引擎缺失而无法恢复。

## 七、测试、启用和发布

在项目根目录执行：

```bash
# 可选：只运行当前插件自己的后端测试
.venv/bin/python -m pytest third_party_games/plugin-your-game/tests

# 可选：只运行当前插件自己的前端测试
npm --prefix frontend run test:run -- ../third_party_games/plugin-your-game/frontend

# 后端插件发现与公共房间测试
.venv/bin/python -m pytest backend/tests/test_game_plugins.py

# 同步启用的前端插件清单
npm --prefix frontend run plugins:sync

# 整套测试与生产构建
npm test
npm run build
```

`npm test` 会自动发现所有 `plugin-*/tests/test_*.py`，也会运行插件目录里的 `*.test.ts` / `*.spec.ts`，因此每款游戏的测试文件仍然只需放在自己的插件目录中。

测试和构建全部通过后：

1. 将当前插件 `manifest.json` 的 `enabled` 改为 `true`。
2. 再运行一次 `npm test && npm run build`。
3. 在桌面端和手机端进入“第三方游戏”，检查入口、建房、加入、操作、重连、结束和战绩。
4. 提交插件目录及必要的通用框架变更。
5. 服务器拉取代码并执行 `python3 scripts/restart.py --pull`。

## 八、常见问题

### 插件没有出现在入口中

依次检查：`enabled` 是否为 `true`、目录名是否等于 `id`、ID 是否以 `plugin-` 开头、三个必需入口是否存在、测试/构建日志是否提示清单无效。

### 后端插件被自动禁用

检查服务端日志中的 `game_plugin.disabled`。常见原因是 Python 导入失败、`create_engine()` 缺失、引擎名称/人数与 manifest 不一致，或引擎缺少必需方法。

### 已有游戏文件很多，是否必须合并成一个文件

不需要。后端文件全部放在当前插件的 `backend/` 并通过相对导入组织；前端组件、资源和工具全部放在当前插件的 `frontend/` 并通过相对导入组织。只有 `plugin.py` 和 `GameView.vue` 的入口位置固定。

### 能否复用大厅内部某个未公开组件

不能直接导入。插件只能使用稳定 SDK 和 CSS 主题变量。如果多款插件确实都需要同一能力，应先把它设计成经过测试的通用 SDK，再由主项目统一开放，而不是让插件依赖内部路径。

关闭的插件不会进入前端构建产物，也不会被后端导入。清单无效、入口缺失或后端加载失败的插件会被跳过，不会阻止大厅启动；但已启用插件自身的 TypeScript、Vue 或 Python 语法错误仍会在测试或构建阶段暴露，必须修复后才能发布。
