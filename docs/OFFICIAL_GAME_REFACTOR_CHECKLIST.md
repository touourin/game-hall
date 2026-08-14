# 官方游戏模块减法重构清单

更新日期：2026-08-14  
当前基线：`main@94340ba`

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
- [x] 将 9 个静态或简单条件规则组件迁为模块自有 `settingsGroups`，删除对应的旧 Vue 文件；源码新增 151 行、删除 159 行，净减少 8 行；372 项前端测试、生产构建和主题检查通过。
- [x] 五个棋类模块统一使用边界明确的 `boardDuelCapabilities()`，模块只声明 `undo/draw/replay/ai` 差异；运行时代码新增 26 行、删除 45 行，净减少 19 行；新增五个游戏全部 35 项能力值的严格回归测试后，源码与测试合计新增 58 行、删除 47 行；373 项前端测试、生产构建和主题检查通过。

## 第四阶段：官方模块所有权收口

- [x] 将多人启动页的 11 套官方游戏文案、强调色和辉光从中央映射迁入各游戏 `index.ts`；第三方游戏继续使用共享回退，不强迫接入官方模块契约。
- [x] 将阿瓦隆类型、模式说明、角色皮肤与进度文件从前端根目录迁入 `games/avalon/`，删除旧路径，不保留转发兼容层。
- [x] 将阿瓦隆的号码表、身份与规则、皮肤选择、游戏视图和结果处理迁入模块自有房间扩展组件。
- [x] 将一夜狼人的顶部帮助和规则栏入口迁入模块自有房间扩展组件，保留原有两处入口行为。
- [x] `ArcadeRoom.vue` 只负责共享房间壳，通过 `headerDetailsComponent`、`headerActionsComponent`、`ruleActionsComponent`、`lobbyComponent`、`waitingMessage` 和 `handlesResult` 扩展点组合官方模块；中央页不再识别阿瓦隆或一夜狼人。
- [x] 将后端战绩查询允许的模式与变体迁入 `GameRecords`；个人战绩和排行榜共用同一个校验入口，`main.py` 不再保存游戏模式白名单或阿瓦隆变体特判。
- [x] 删除全局样式表中 289 行确认无运行时使用者的旧选择器；动态生成的排行榜名次选择器继续保留。
- [x] 本阶段移动 6 个阿瓦隆根级文件、增加 5 个有独立职责的模块组件；运行时/源码新增 764 行、删除 863 行，净减少 99 行。新增测试与清单净增加 99 行，整批总行数持平。
- [x] 全量验证通过：后端 564 项、第三方模块边界 48 项、前端 375 项；生产构建、主题选择器和月白陶瓷对比度检查通过。

## 第五阶段：社交桌游能力类别

- [x] 前端建立 `socialTableCapabilities()`，统一社交推理、扑克和派对桌游真正相同的平台能力默认值。
- [x] 后端建立对应的 `social_table_capabilities()`，前后端使用同一能力分类边界。
- [x] 阿瓦隆、无间疑云、一夜狼人、德州扑克、斗地主和大富翁只声明观战、先手、回放与 AI 的实际差异，不再重复七项完整能力对象。
- [x] 新增前后端严格矩阵测试，逐项锁定 6 个游戏共 42 项前端能力值及完整后端能力对象，并校验能力声明与房间规则默认值一致。
- [x] 复核目录、规则与展示声明：它们只有结构相似，人数、语义、皮肤和房间行为均不同，因此继续留在游戏模块，不建立强制构造器。
- [x] 前端构造器仅允许覆盖游客、观战、先手、回放与 AI 差异；固定关闭的撤销与和棋不能被社交桌游误改，构造器内部也没有 `gameKey` 分支。
- [x] 本阶段运行时/源码新增 66 行、删除 80 行，净减少 14 行；测试与清单新增 88 行、删除 5 行，整批新增 154 行、删除 85 行，净增加 69 行。
- [x] 全量验证通过：后端 565 项、第三方模块边界 48 项、前端 376 项；生产构建、主题选择器和月白陶瓷对比度检查通过。

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

以下重复模板已迁入各自模块的声明式选项组，并由共享设置页渲染：

- [x] `departed_suspicion/RuleSettings.vue`
- [x] `doudizhu/RuleSettings.vue`
- [x] `hanoi/RuleSettings.vue`
- [x] `junqi/RuleSettings.vue`
- [x] `minesweeper/RuleSettings.vue`
- [x] `monopoly/RuleSettings.vue`
- [x] `one_night_werewolf/RuleSettings.vue`
- [x] `poker/RuleSettings.vue`
- [x] `tetris/RuleSettings.vue`

迁移结果：静态卡片、分段选择和单字段 `visibleWhen` 统一使用共享渲染器；配置仍归对应游戏所有。阿瓦隆、围棋、五子棋和中国象棋包含多字段约束或专有交互，继续使用独立组件，不强行复用。

## 第三优先级：减少声明样板，但不以删文件为目标

- [x] 棋类游戏统一使用多人能力类别，仅保留 `undo/draw/replay/ai` 差异。
- [x] 卡牌、社交和派对桌游统一使用社交桌游能力类别，仅保留观战、先手、回放、AI 等差异。
- [x] 已检查 `index.ts` 中重复的目录、规则默认值和展示默认值；除能力类别外均具有独立语义，继续由各游戏模块直接声明。
- [x] 任何构造器都必须允许游戏覆盖差异，不能形成新的中央 `gameKey` 分支。

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
