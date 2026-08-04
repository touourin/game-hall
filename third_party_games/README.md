# 第三方游戏插件

这个目录是游戏大厅唯一允许放置第三方游戏源码的位置。插件通过固定清单和前后端入口自动注册，不需要修改大厅、路由、房间页或后端游戏注册表。

## 快速开始

1. 复制 `plugin-counter-demo/`，并把新目录改成以 `plugin-` 开头的唯一 ID。
2. 修改 `manifest.json`，目录名必须与 `id` 完全一致。
3. 实现 `backend/plugin.py` 中的 `create_engine()`。
4. 实现 `frontend/GameView.vue`。
5. 将 `enabled` 改为 `true`，重启前后端。前端启动和构建命令会自动重新生成启用插件清单。
6. 运行前后端测试和前端生产构建。

启用后，插件会自动出现在游戏大厅，并复用主项目的账号、房间、邀请、聊天、排行榜入口和响应式房间外壳。

## 固定目录结构

```text
third_party_games/
└── plugin-your-game/
    ├── manifest.json
    ├── README.md
    ├── backend/
    │   └── plugin.py
    ├── frontend/
    │   └── GameView.vue
    └── tests/
```

不要更改入口文件的位置。自动发现器只读取 `manifest.json`、`backend/plugin.py` 和 `frontend/GameView.vue`。

## manifest.json

完整字段约束见 `plugin.schema.json`。核心字段：

- `apiVersion`：当前必须是 `1`。
- `enabled`：只有 `true` 才会注册。
- `id`：必须以 `plugin-` 开头，最长 32 位，只能包含小写字母、数字和连字符。
- `players.min/max`：支持 1–20 人。
- `defaultOptions`：创建房间时合并到公共默认规则中。
- `ruleLabels`：大厅规则摘要中的静态标签。

## 后端契约

`backend/plugin.py` 必须导出无参数函数：

```python
def create_engine():
    return YourEngine()
```

返回对象必须实现 `backend.app.games.base.GameEngine`：

- `key`、`name`、`min_players`、`max_players`
- `initial_state()`
- `start(room)`
- `act(room, player, action, payload)`
- `view(room, viewer)`
- `player_result(room, player)`

引擎标识、名称和人数必须与 manifest 一致。插件加载异常时只会禁用该插件，游戏大厅仍会启动。

## 前端契约

`frontend/GameView.vue` 接收一个 `snapshot` 属性。只允许从稳定 SDK 导入主项目能力：

```ts
import {
  usePluginGameActions,
  type ArcadeSnapshot,
} from '@game-hall/plugin-sdk'
```

通过 `usePluginGameActions()` 发送游戏动作，不要直接导入主项目的 store、socket、路由或内部组件。

插件样式必须使用 `<style scoped>`，根元素应设置 `min-width: 0; max-width: 100%`，并在 320px 手机宽度下无横向滚动。

## 隔离边界

- 不允许修改 `frontend/src`、`backend/app` 或根目录依赖文件来适配单个插件。
- 不允许使用全局 CSS、修改 `document.body` 或覆盖主项目 CSS 变量。
- 不允许读取账号令牌、访问令牌、Cookie 或浏览器存储。
- 不允许直接连接 Socket；使用插件 SDK。
- 第三方依赖必须先经项目维护者审核，不能自行修改根 `package.json` 或 `pyproject.toml`。
- 删除插件目录并重启即可卸载；已有该插件未结束的房间会因为引擎缺失而无法恢复，应先结束相关房间。

关闭的插件不会进入前端构建产物，也不会被后端导入。清单无效、入口缺失或后端加载失败的插件会被跳过，不会阻止大厅启动；但已启用插件自身的 TypeScript、Vue 或 Python 语法错误仍会在测试或构建阶段暴露，必须修复后才能发布。当前版本是“受控源码插件”，适用于经过代码审核的游戏。真正不可信的第三方代码仍应使用 iframe 与独立后端进程隔离。
