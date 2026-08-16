# 第三方游戏前端 SDK 维护规范

`@game-hall/plugin-sdk` 是第三方游戏唯一可以依赖的宿主前端入口。插件只认识这里公开的组件、类型和组合式函数，不认识主项目目录结构。

## 公共边界

- `index.ts` 是唯一导出入口。
- `actions.ts` 把宿主 Store 适配成稳定的插件动作接口。
- `types.ts` 只包含插件作者可以依赖的公共类型。
- `components/` 使用包装组件固定 Props、Events、Slots 和无障碍约束，不直接向插件暴露内部组件路径。
- `formatting.ts`、`fullscreen.ts`、`theme.ts` 提供与宿主实现解耦的公共函数和组合式能力。

公共组件必须满足：

1. 不要求插件了解账号、路由、房间 Store 或具体官方游戏。
2. 能依靠 Props、Events 和 Slots 独立表达行为。
3. 同时适配大厅主题、手机和桌面布局。
4. 有公共契约测试，而不只依赖内部组件测试。
5. 在插件 API v1 内只做兼容性新增；删除、重命名或改变既有语义属于破坏性变更。

大厅、聊天、账号、房间管理等业务组件不应直接进入 SDK。若插件确实需要相关能力，应先设计更小的宿主无关接口或包装组件。

## 当前公共能力

| 分类 | 导出 |
| --- | --- |
| 操作 | `PluginButton`、`PluginIconButton`、`usePluginGameActions` |
| 游戏展示 | `PluginPlayingCard`、`PluginRevealCard`、`PluginMetricGrid`、`PluginResultCard`、`PluginRuleGuide` |
| 弹窗 | `PluginModal`、`PluginConfirmDialog` |
| 表单 | `PluginTextField`、`PluginNumberField`、`PluginSelect` |
| 状态 | `PluginStatePanel`、`PluginLoadingState`、`PluginEmptyState`、`PluginErrorState` |
| 宿主环境 | `usePluginFullscreen`、`usePluginTheme`、`pluginThemeMaterials` |
| 格式化 | `formatPluginDuration`、`formatPluginScore` |

公共主题只开放当前主题的只读状态和不可变材质值，不开放修改用户主题的能力。公共全屏能力只控制插件明确传入的根元素，不允许插件操作宿主其他 DOM。

## 新增能力的方式

1. 先确认能力至少能服务多款游戏，且不含账号、路由、房间 Store 等业务依赖。
2. 为内部实现增加公共包装，公共类型只引用 `types.ts` 中的结构。
3. 在 `index.ts` 显式导出，补公共契约测试。
4. 至少迁移一个真实插件或模板使用新接口。
5. 更新第三方仓库接入手册，并验证带插件和无插件构建。

API v1 可以兼容性新增导出，不因为新增组件升级到 v2。已有 Props、事件、返回值或语义发生不兼容变化时，才需要设计新的版本边界。

## 校验

`npm run plugins:verify-boundaries` 会扫描每个插件的前端源码。生产代码只能导入：

- 插件目录内的相对路径；
- `@game-hall/plugin-sdk`；
- `vue`；
- `@lucide/vue`。

测试可以额外使用 `vitest`、`@vue/test-utils` 和 `pinia`。任何越过插件目录的相对导入都会失败。

新增公共能力后，必须同步更新：

- `index.ts` 和公共类型；
- `index.test.ts` 契约测试；
- `third_party_games/README.md` 使用说明；
- `plugin-counter-demo` 示例（能力适用时）。
