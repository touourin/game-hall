# 官方游戏模块减法重构清单

更新日期：2026-08-14  
当前基线：`main@af151d3`

## 目标

在保留官方模块注册制的前提下，删除迁移后不再承担独立职责的文件和重复实现，为大厅、房间和游戏内 UI 重写提供更小、更稳定的前端表面。

这不是以文件越少越好为目标。只有满足以下条件才能删除：

1. 新位置已经接管全部行为，且没有两套实现并存。
2. 游戏独有逻辑仍归属于对应游戏模块。
3. 相同逻辑才进入共享层，不为减少行数强行抽象。
4. 每一批删除后必须通过前端全量测试、生产构建和主题检查；涉及后端时必须通过 `backend/tests`。

## 状态说明

- `[x]` 已完成并验证
- `[ ]` 确认可执行
- `[~]` 需要先迁移，再删除
- `[-]` 保留，不应删除

## 已完成

- [x] 将官方游戏目录、能力、规则、展示和战绩接入前端模块注册表。
- [x] 将 18 个官方引擎、目录和能力接入后端模块注册表。
- [x] 删除 `StatsModal.vue` 中按游戏分支，文件从 753 行降至 213 行。
- [x] 删除 `GameRuleSettings.vue` 中按游戏分支，文件从 446 行降至 136 行。
- [x] 删除 `gameRules.ts` 中旧规则实现，保留统一模块/插件入口，文件从 305 行降至 82 行。
- [x] 删除 `LeaderboardModal.vue`、`SoloChallengeLauncher.vue` 和 `ArcadeRoom.vue` 中已迁移的展示分支。
- [x] 抽取共享玩家列表和座位排布，房间页不再自己渲染每个座位。
- [x] 建立单人游戏能力类别，删除以下 7 个过度拆分文件（`af151d3`）：
  - `frontend/src/games/deep_shaft/roomPresentation.ts`
  - `frontend/src/games/hanoi/roomPresentation.ts`
  - `frontend/src/games/minesweeper/roomPresentation.ts`
  - `frontend/src/games/reaction/roomPresentation.ts`
  - `frontend/src/games/schulte/roomPresentation.ts`
  - `frontend/src/games/survive_three_seconds/roomPresentation.ts`
  - `frontend/src/games/tetris/roomPresentation.ts`
- [x] 第一批减法重构通过 373 项前端测试、生产构建和主题检查；本批净减少 48 行。
- [x] 删除第二批 13 个无独立职责的前端文件：平台薄访问器、阿瓦隆纯转发组件、3 个房间展示薄文件和 6 个战绩工厂薄文件。
- [x] 删除仅供房间页二次查询的 `builtinGameComponent()`；房间页复用已经解析的模块定义。
- [x] 第二批运行时代码与测试新增 75 行、删除 161 行，净减少 86 行；372 项前端测试、生产构建、主题选择器和月白陶瓷对比度检查全部通过。
- [x] 将后端官方目录派生逻辑迁回唯一数据源 `builtin.py`，删除 `catalog.py`；新增 27 行、删除 28 行，后端 563 项测试全部通过。
- [x] 将 7 个单人战绩详情迁为模块自有数据映射和单一共享渲染器，删除 7 个异步组件；源码与测试新增 192 行、删除 196 行，净减少 4 行、净减少 6 个文件；372 项前端测试、生产构建和主题检查通过。
- [x] 默认玩家详情支持模块自有角色标签，删除 `junqi/MatchDetail.vue`；棋类和斗地主同步获得一致的执棋方/身份展示；源码与测试新增 25 行、删除 32 行，372 项前端测试、生产构建和主题检查通过。

## 第一优先级：可以整文件删除

### 平台薄访问器

- [x] 删除 `frontend/src/game-platform/roomPresentation.ts`。
  - 将房间展示查找并入 `game-platform/registry.ts`，或直接使用已解析的模块定义。
  - 验收：`ArcadeRoom.vue` 不再有第二套注册表访问路径。
- [x] 删除 `frontend/src/game-platform/statsPresentation.ts`。
  - 将统计展示查找并入现有 `game-platform/records.ts`。
  - 验收：排行榜和统计只经过一个战绩展示入口。

### 纯转发组件

- [x] 删除 `frontend/src/games/avalon/AvalonRoomView.vue`。
  - 注册表直接加载 `AvalonTable.vue`；`ArcadeRoom.vue` 已经提供它需要的 `snapshot`、`roleSkin` 和 `openChat`。
- [x] 删除 `frontend/src/games/avalon/AvalonRoomView.test.ts`。
  - 将必要的皮肤和聊天事件验证放回 `ArcadeRoom.test.ts` 与 `AvalonTable.test.ts`。

### 仍然过小的房间展示文件

- [x] 删除 `frontend/src/games/departed_suspicion/roomPresentation.ts`，内容放回模块 `index.ts`。
- [x] 删除 `frontend/src/games/junqi/roomPresentation.ts`，内容放回模块 `index.ts`。
- [x] 删除 `frontend/src/games/poker/roomPresentation.ts`，内容放回模块 `index.ts`。

以下两个文件暂时保留，因为包含独立阶段映射，不属于单纯转发：

- `frontend/src/games/avalon/roomPresentation.ts`
- `frontend/src/games/one_night_werewolf/roomPresentation.ts`

### 只有一层工厂调用的战绩文件

以下文件没有独立算法，可将 `createCompetitiveStatsPresentation(...)` 直接放入对应模块清单：

- [x] 删除 `frontend/src/games/chess/records.ts`。
- [x] 删除 `frontend/src/games/doudizhu/records.ts`。
- [x] 删除 `frontend/src/games/go/records.ts`。
- [x] 删除 `frontend/src/games/gomoku/records.ts`。
- [x] 删除 `frontend/src/games/poker/records.ts`。
- [x] 删除 `frontend/src/games/xiangqi/records.ts`。

具有独立格式化、筛选或详情逻辑的其他 `records.ts` 保留。

### 后端派生目录文件

- [x] 删除 `backend/app/games/catalog.py`。
  - 将排序校验、`BUILTIN_GAME_CATALOG` 和 `BUILTIN_GAME_NAMES` 并入 `games/builtin.py`。
  - 更新 `accounts.py`、`registry.py` 和测试的导入。
  - 验收：后端目录只从官方定义生成一次。

## 第二优先级：迁移后整批删除

### 单人战绩详情组件

下列组件共用相同的“标题 + 指标卡片”结构，仅数据映射不同：

- [x] `frontend/src/games/deep_shaft/MatchDetail.vue`
- [x] `frontend/src/games/hanoi/MatchDetail.vue`
- [x] `frontend/src/games/minesweeper/MatchDetail.vue`
- [x] `frontend/src/games/reaction/MatchDetail.vue`
- [x] `frontend/src/games/schulte/MatchDetail.vue`
- [x] `frontend/src/games/survive_three_seconds/MatchDetail.vue`
- [x] `frontend/src/games/tetris/MatchDetail.vue`

迁移结果：各游戏在战绩模块中声明详情区块数据，由 `MatchMetricDetail.vue` 统一渲染；以上 7 个文件和对应的异步组件注册已经删除。

- [x] 将军旗角色映射交给共享玩家详情渲染器，删除 `junqi/MatchDetail.vue` 和异步注册。
- [-] 保留 `avalon/MatchDetail.vue`；它包含完整任务、提案、仙女和刺杀回放，不应强行复用。

### 简单规则设置组件

先建立声明式选项组渲染器，再评估删除以下重复模板：

- [~] `departed_suspicion/RuleSettings.vue`
- [~] `doudizhu/RuleSettings.vue`
- [~] `hanoi/RuleSettings.vue`
- [~] `junqi/RuleSettings.vue`
- [~] `minesweeper/RuleSettings.vue`
- [~] `monopoly/RuleSettings.vue`
- [~] `poker/RuleSettings.vue`

只有当共享渲染器与配置的总复杂度低于现有组件时才实施。阿瓦隆、围棋、五子棋、中国象棋和一夜狼人的条件逻辑较多，继续使用独立组件。

## 第三优先级：减少声明样板，但不以删文件为目标

- [ ] 棋类游戏统一使用多人能力类别，仅保留 `undo/draw/replay/ai` 差异。
- [ ] 卡牌和社交游戏统一使用多人能力类别，仅保留观战、先手、AI 等差异。
- [ ] 检查 `index.ts` 中重复的目录、规则默认值和展示默认值，使用小型构造器表达真正一致的部分。
- [ ] 任何构造器都必须允许游戏覆盖差异，不能形成新的中央 `gameKey` 分支。

## 必须保留的核心边界

- [-] `frontend/src/games/*/index.ts`：每个官方游戏的模块清单和所有权边界。
- [-] `backend/app/games/*/definition.py`：每个官方引擎的后端声明和能力边界。
- [-] 游戏引擎、棋盘、牌桌和独有规则组件。
- [-] `frontend/src/game-platform/types.ts`、`defineGame.ts`、`registry.ts`：前端模块契约。
- [-] `backend/app/games/definition.py`、`builtin.py`、`registry.py`：后端模块契约与运行时注册。
- [-] `gameCatalog.ts` 和 `gameRules.ts`：官方模块与第三方插件之间的统一公共入口；只有替代入口完整覆盖后才能删除。
- [-] `soloPresentation.ts`：单人游戏入口 UI 的独有文案、指标和强调色，后续设计 UI 时需要保留。

## 每批验收清单

- [ ] `rg` 确认被删除文件没有残留导入。
- [ ] `git diff --check` 通过。
- [ ] 前端全量测试通过。
- [ ] 前端生产构建通过。
- [ ] 主题选择器和月白陶瓷对比度检查通过。
- [ ] 涉及后端时，`backend/tests` 全量通过。
- [ ] 提交统计必须同时报告删除文件数、新增行、删除行和净变化。
- [ ] 每批独立提交，出现问题可以单独回滚。
