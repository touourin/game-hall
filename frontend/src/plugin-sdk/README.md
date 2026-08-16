# 第三方游戏前端 SDK 维护规范

`@game-hall/plugin-sdk` 是第三方游戏唯一可以依赖的宿主前端入口。插件只认识这里公开的组件、类型和组合式函数，不认识主项目目录结构。

## 公共边界

- `index.ts` 是唯一导出入口。
- `actions.ts` 把宿主 Store 适配成稳定的插件动作接口。
- `types.ts` 只包含插件作者可以依赖的公共类型。
- `components/` 使用包装组件固定 Props、Events、Slots 和无障碍约束，不直接向插件暴露内部组件路径。

公共组件必须满足：

1. 不要求插件了解账号、路由、房间 Store 或具体官方游戏。
2. 能依靠 Props、Events 和 Slots 独立表达行为。
3. 同时适配大厅主题、手机和桌面布局。
4. 有公共契约测试，而不只依赖内部组件测试。
5. 在插件 API v1 内只做兼容性新增；删除、重命名或改变既有语义属于破坏性变更。

大厅、聊天、账号、房间管理等业务组件不应直接进入 SDK。若插件确实需要相关能力，应先设计更小的宿主无关接口或包装组件。

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
