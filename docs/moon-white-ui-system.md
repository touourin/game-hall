# 月白陶瓷 UI 系统

## 1. 方案状态

“月白陶瓷 · 精密底盘”是已通过审核的浅色主题方向。它不是纯白背景，也不是传统拟物界面，而是由三层材料共同构成：

1. 后层底盘：冷月灰珍珠陶瓷，负责页面背景与整机轮廓。
2. 主内容井：暖月白陶瓷，承载页面主要模块。
3. 内嵌控件：乳雾玻璃，承载卡片、输入、按钮和状态。

喷砂自然铝只用于边缘、接缝和控件结构，不作为大面积装饰。界面的高级感来自材料层级、接触阴影、倒角精度和克制高光，而不是花纹或强光效。

当前三套正式主题名称为：

- `emerald`：极光雾舱
- `midnight`：暖钛陶瓷
- `royal`：月白陶瓷

保留现有主题 ID，避免迁移用户本地偏好；只更新展示名称、说明和主题变量。

## 2. 审核预览

所有预览均为视觉与布局参考，正式界面继续使用 Vue、CSS 和现有确定性游戏组件实现，不直接使用图片中的文字、棋盘或交互状态。

| 编号 | 页面 | 设备 | 文件 |
| --- | --- | --- | --- |
| 01 | 游戏大厅 | 手机 | [01-mobile-hall.png](ui-previews/moon-white/01-mobile-hall.png) |
| 02 | 游戏入口与房间选择 | 手机 | [02-mobile-game-entry.png](ui-previews/moon-white/02-mobile-game-entry.png) |
| 03 | 多人等待房 | 手机 | [03-mobile-waiting-room.png](ui-previews/moon-white/03-mobile-waiting-room.png) |
| 04 | 棋盘对局 | 手机 | [04-mobile-board-game.png](ui-previews/moon-white/04-mobile-board-game.png) |
| 05 | 棋盘对局 | 电脑 | [05-desktop-board-game.png](ui-previews/moon-white/05-desktop-board-game.png) |
| 06 | 高人数身份推理 | 电脑 | [06-desktop-social-deduction.png](ui-previews/moon-white/06-desktop-social-deduction.png) |
| 07 | 牌桌对战 | 电脑 | [07-desktop-card-table.png](ui-previews/moon-white/07-desktop-card-table.png) |
| 08 | 单人挑战 | 手机 | [08-mobile-solo-challenge.png](ui-previews/moon-white/08-mobile-solo-challenge.png) |
| 09 | 地产经营 | 手机 | [09-mobile-property-game.png](ui-previews/moon-white/09-mobile-property-game.png) |
| 10 | 弹层与基础控件 | 电脑 | [10-desktop-overlays-and-controls.png](ui-previews/moon-white/10-desktop-overlays-and-controls.png) |
| 11 | 设置与确认抽屉 | 手机 | [11-mobile-settings-sheet.png](ui-previews/moon-white/11-mobile-settings-sheet.png) |
| 12 | 游戏入口与建房 | 电脑 | [12-desktop-game-entry.png](ui-previews/moon-white/12-desktop-game-entry.png) |

### 预览限制

- 图片生成可能出现个别文字偏差；主题正式名称以本文件为准。
- 棋盘坐标、棋子局面、牌局数值与地图格子必须由现有游戏代码确定性渲染。
- 预览中的头像、房间码和统计数字仅用于表达布局。
- 不增加好友系统、社交动态、金币、商城、会员或广告。

## 3. 内置游戏分组

只覆盖游戏大厅内的 15 款内置游戏，不覆盖第三方游戏。

| 内容骨架 | 游戏 | 共享部分 | 保持独立的部分 |
| --- | --- | --- | --- |
| 棋盘竞技 | 围棋、五子棋、中国象棋、军旗 | 房间外壳、双人座位、回合状态、历史、操作坞、棋盘容器 | 棋盘规则、棋子、合法操作、胜负结算 |
| 牌桌对战 | 德州扑克、斗地主 | 房间外壳、3–8 人座位、牌桌容器、手牌区、操作坞、历史 | 发牌、叫牌/下注、牌型、各自行动逻辑 |
| 身份推理 | 阿瓦隆、无间疑云、一夜狼人 | 5–10 人座位、私密信息卡、阶段头、选择托盘、投票/决策面板 | 身份、知识、任务/夜晚/装备等阶段逻辑 |
| 单人挑战 | 反应挑战、舒尔特方格、扫雷、汉诺塔、落块挑战 | 单人页头、挑战配置、指标、记录、结果卡、操作坞 | 挑战舞台与输入方式 |
| 地产经营 | 大富翁 | 4 人座位、回合状态、资产指标、事件卡、操作坞、历史 | 地图、地产、交易、回合事件 |

## 4. 共享组件层级

### 4.1 全局原语

优先从全局 CSS 与基础组件统一，禁止各游戏重新定义外观相同的按钮和表单。

- `UiSurface`：底盘、内容井、内嵌面三种 elevation。
- `UiButton`：primary、secondary、quiet、danger、disabled。
- `UiIconButton`：返回、设置、更多、关闭、复制、二维码。
- `UiField`：文本、房间码、数字、只读与错误状态。
- `UiSegmentedControl`：创建/加入、难度、模式与规则选项。
- `UiToggle`：规则、偏好与权限开关。
- `UiStatusPill`：在线、房主、准备、观战、阶段状态。
- `UiMetricCell`：计时、得分、资产与房间统计。
- `UiAvatar`：头像、在线点、选中环与状态角标。
- `UiToast`、`UiEmptyState`、`UiLoadingState`、`UiErrorState`。

### 4.2 流程组件

- `GamePageHeader`：游戏入口、房间和对局共用页头。
- `RoomIdentityCard`：房间码、复制、邀请和二维码。
- `RoomBrowserList`：公开房间与观战房间使用同一行组件变体。
- `RoomRulesSummary`：入口摘要、等待房摘要和游戏内只读规则。
- `RoomActionDock`：手机底部操作坞、电脑右侧操作面板。
- `GameHistoryPanel`：棋盘落子、牌局行动与阶段事件的通用容器。
- `InvitePanel`、`StatsPanel`、`LeaderboardPanel`、`ResultPanel`。
- `BaseModal`：电脑端居中弹窗。
- `BaseSheet`：手机端底部抽屉；危险确认、规则和邀请优先使用。

### 4.3 玩家座位组件

玩家座位不按游戏拆成十五套，而按信息密度与布局拆成同一家族的三种变体：

- `PlayerSeatCompact`：5–10 人身份游戏和桌面侧栏。
- `PlayerSeatStandard`：2–4 人等待房和棋盘游戏。
- `PlayerSeatTable`：牌桌环形定位，只改变布局锚点，不改变玩家状态模型。

统一输入数据：座位号、头像、昵称、在线状态、房主、自己、AI、准备状态、当前行动、游戏内标签和可选操作。游戏可以通过插槽加入“黑方”“白方”“地主”“队长”等局部标签，但不重新实现头像、在线点、选中态和管理操作。

## 5. 响应式规则

### 5.1 手机端

- 纵向单列；主游戏舞台优先，信息模块位于其前后。
- 顶部只保留返回、标题和最多三个高频操作；低频动作进入更多菜单。
- 主要操作固定或粘附在底部安全区，最小点击高度 44px。
- 长设置、规则和资料库使用完整页面或底部抽屉。
- 双人座位可横排；4 人使用横向滚动条；5–10 人使用 2 列紧凑网格。
- 聊天、历史、资产和资料库默认折叠，不覆盖游戏主舞台。
- 不在游戏入口与对局页显示大厅底部导航。

### 5.2 电脑端

- 游戏入口使用主视觉/公开房间、对局控制台、上下文信息三栏。
- 游戏内使用左侧玩家/规则、中央舞台、右侧操作/历史三栏。
- 中央舞台至少占可用宽度的 50%，不得被社交或装饰模块挤压。
- 弹窗使用居中面板；较长设置可使用两栏或独立页面。
- 窗口变窄时先折叠右栏，再将左栏移到舞台上方，最终进入手机布局。

建议断点：

- `>= 1180px`：三栏桌面工作台。
- `760–1179px`：双栏或主舞台 + 抽屉。
- `< 760px`：手机纵向布局。

## 6. 月白陶瓷设计令牌

下面是方向值，实施时应通过视觉回归微调，而不是在各组件内硬编码。

```css
:root[data-theme="royal"] {
  --chassis: #cbd3d9;
  --chassis-edge: #b8c2c9;
  --surface-primary: #f4f2ec;
  --surface-inset: rgba(231, 237, 240, 0.82);
  --surface-glass: rgba(246, 248, 249, 0.68);
  --text-primary: #20292f;
  --text-secondary: #66737b;
  --line-soft: rgba(70, 88, 98, 0.14);
  --accent: #4d8b7b;
  --accent-soft: #8fb5aa;
  --danger: #d95343;
  --warning: #b98942;
  --shadow-contact: 0 2px 4px rgba(47, 59, 67, 0.16);
  --shadow-raised: 0 12px 28px rgba(54, 67, 76, 0.13);
  --radius-control: 12px;
  --radius-card: 20px;
  --radius-panel: 28px;
}
```

每个游戏只增加一个低饱和内容强调色，不能改变基础表面、字体和状态色语义。

## 7. 实施顺序

1. 主题令牌与全局原语：`styles.css`、按钮、表单、表面、弹层。
2. 页头、底部操作坞、玩家座位、状态与历史等共享组件。
3. `GameHall`、`ArcadeHome`、`MultiplayerMatchLauncher`、`SpectatorBrowser`。
4. `ArcadeRoom` 的等待房和公共对局外壳。
5. 棋盘竞技与牌桌对战。
6. 身份推理。
7. 单人挑战与地产经营。
8. 设置、战绩、排行榜、邀请、结算和错误/空/加载状态。
9. 手机/电脑视觉回归、键盘导航、触摸目标和性能检查。

实施时每批只迁移一种共享组件，并保持现有测试通过；不要一次性重写所有游戏逻辑。
