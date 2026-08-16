# 官方游戏图标规范

这套资源用于游戏大厅、分类页、房间入口和移动端导航中的官方游戏图标。目标是让所有游戏看起来属于同一套产品，同时保留足够强的游戏识别度。

游戏分类一级入口不是另一套方形图标，使用现有游戏图标组合成横向分类视觉；对应规则见 [`../categories/README.md`](../categories/README.md)。

## 1. 视觉方向

统一方向为 **克制的赛博骨架 + Apple 产品级 2.5D 材质**：

- 图标是一个经过棚拍的精密产品，不是插画、截图或徽章。
- 使用圆润比例、4–6 层结构、精密倒角、柔和高光和真实接触阴影。
- 画面有空间感和材质细节，但在 104px 尺寸下仍能一眼识别。
- 每款游戏只使用一个低饱和点缀色；不依赖颜色区分游戏。
- 黑、白、灰和金属中性色必须占画面 80%–90%，点缀色只占 10%–20%，并且只承担核心状态或结构提示。
- 多人游戏的玩家阵营色属于对局 UI，不得原样搬进大厅图标；大厅图标仍只保留一种点缀色。
- 所有主题共享同一构图、镜头和轮廓，只切换材质。

禁止使用：人物、电影场景、电竞盾牌、奇幻徽章、强霓虹、卡通造型、廉价手游边框、大段文字、Apple 标志、水印和无意义装饰。

## 2. 双材质资源

每款官方游戏必须同时提供以下两个文件：

| 变体 | 使用主题 | 材质 |
| --- | --- | --- |
| `dark` | 幽蓝冷钢、曜石黑钛 | 近黑军蓝、黑钛、深石墨陶瓷、阳极氧化金属 |
| `light` | 月白云瓷、橘光晴釉 | 月白或奶油陶瓷、磨砂表面、香槟银、浅色金属 |

两个变体必须保持完全一致的主体轮廓、镜头角度、物体数量和空间关系。浅色版不是重新设计，只是同一件产品的另一种材质配置。

## 3. 文件与画布

- 命名：`<game-slug>-dark.webp`、`<game-slug>-light.webp`。
- 格式：WebP，sRGB，768 × 768，质量 90；使用完整方形棚拍背景，不使用透明通道。
- 运行时目录只允许提交成对的 WebP 和本 README；不得保留 SVG、PNG、生成草稿或同名旧资源，避免出现双轨源图。
- 构图：正方形画布，略俯视 3/4 产品镜头；主体视觉中心约为 `(50%, 52%)`。
- 安全区：主体宽高占画布 72%–82%，任何零件不得进入外侧 7% 的裁切危险区。
- 背景：安静的单色棚拍台；可有微弱径向亮度和接触阴影，不得出现风景、房间或地平线。
- 光照：左上方大面积柔光，右后方极弱轮廓光；高光不能过曝，暗部仍需保留层次。
- 小尺寸：必须在 142px、104px 和 72px 三档检查识别度与边缘清晰度。

## 4. 统一形态语言

- 所有主体都落在同一类圆角双层基座上；基座是家族特征，不是游戏内容。
- 主体通常包含：承托基座、核心识别物、一个辅助识别物、少量功能刻度或连接结构。
- 细节只能帮助解释结构；删除缩小后看不见、且不影响识别的装饰。
- 不使用可读小字。必须出现符号时，仅使用稳定的大号棋形、牌面符号或几何刻度。
- 同类游戏必须主动拉开轮廓：围棋与五子棋、德州扑克与斗地主、国际象棋与中国象棋不能只靠标题区分。

## 5. 当前官方游戏身份

| Slug | 核心识别物 | 轮廓要求 | 点缀色 |
| --- | --- | --- | --- |
| `avalon` | 圆形任务仪表盘、座位节点、交叉决策刃 | 圆盘 + 放射节点 | 冰蓝 |
| `chess` | 低矮 8×8 棋盘、国王与骑士 | 高低棋子剪影 | 靛蓝 |
| `gomoku` | 15 路小棋盘、连续五枚黑子、少量白子 | 低平正方板 | 青玉 |
| `xiangqi` | 楚河分界棋盘、两枚主将圆棋 | 横向分区 + 大圆棋 | 朱砂 |
| `go` | 19 路棋盘、黑白势力块、两只棋笥 | 大棋盘 + 双棋笥 | 琥珀 |
| `poker` | 两张底牌、三枚筹码、桌面按钮 | 扇形牌 + 圆筹码 | 海蓝 |
| `doudizhu` | 三张立牌、地主冠记、两枚阵营钮 | 三峰式牌组 | 暗红 |
| `junqi` | 铁路线地图、军旗、四枚覆子 | 分叉路径 + 旗杆 | 橄榄绿 |
| `reaction` | 精密秒表、反应按钮、环形刻度 | 竖向表体 + 大按钮 | 珊瑚橙 |
| `deep-shaft` | 垂直玻璃井、层叠平台、下降舱 | 明显纵向塔形 | 紫罗兰 |
| `schulte` | 5×5 方格阵列、中央扫描焦点 | 规则矩阵 + 光学环 | 青色 |
| `critical-crossing` | 四向脉冲导轨、中央安全孔与导航核心 | 十字导轨 + 中央核心 | 冰青 |
| `pixel-push` | 低矮推力擂台、两枚对抗推块、边缘坠落缺口 | 圆角擂台 + 对置方块 + 单侧缺口 | 冰青 |
| `minesweeper` | 方格盘、切面地雷、旗标 | 方板 + 球形雷 | 红色 |
| `hanoi` | 三根立柱、阶梯圆盘 | 递减圆锥塔 | 金色 |
| `tetris` | 竖向游戏舱、合法四格骨牌 | 窄高矩形舱 | 蓝紫 |
| `monopoly` | 城市积木、路线环、骰子 | 城市天际线 | 翡翠绿 |
| `one-night-werewolf` | 月相仪表、狼影遮片、三席节点 | 月盘 + 三节点 | 冷紫 |
| `departed-suspicion` | 指纹扫描器、双人席位、证据槽 | 八角扫描台 | 青绿 |

## 6. 新增与重做流程

任何新增或重做图标都必须按以下顺序执行，不得直接生成后入库：

1. 先在“当前官方游戏身份”中登记核心识别物、轮廓要求和唯一点缀色；没有身份定义不得开始制作。
2. 从现有正式资源中选择 2–3 个同层级图标作为家族参考，但不得复制它们的游戏专属物件。
3. 先制作 `dark` 几何母版；确认轮廓、镜头、留白和 104px 识别度后，才允许制作 `light`。
4. `light` 必须以 `dark` 为几何参考，只切换材质、背景和明暗关系，不得重新构图。
5. 导出时只把最终成对 WebP 放入本目录；旧版本、SVG 源图、PNG 母版和生成草稿必须移出或删除。
6. 在 142px、104px、72px 三档与至少三款现有图标并排检查，然后执行 `npm run verify:game-icons`。

### 生成提示词模板

后续新增游戏时，在下面模板中只替换方括号内容。必须先制作 `dark`，再以 `dark` 作为几何参考制作 `light`。

```text
Final square game-lobby product icon for [game name].
Identity: [core object and silhouette from the table].
Use the established official icon family: elevated three-quarter product camera,
rounded double plinth, 4–6 material layers, precision bevels, soft studio highlights,
real contact shadows, one restrained accent color, quiet full-square studio backdrop.
Keep 80–90% of the image in black/white/gray/metal neutrals and limit the single
accent color to 10–20%; multiplayer team colors belong to gameplay UI, not this icon.
Keep the subject inside the central 82% safe area and readable at 104 px.
[dark: black titanium, smoked glass, graphite ceramic, anodized metal]
[light: moon-white ceramic, frosted glass, champagne silver; preserve the exact dark geometry]
No people, scenery, text labels, logo, watermark, neon, fantasy badge, esports shield,
cartoon styling, cheap mobile-game frame, or cropped parts.
```

## 7. 验收清单

提交图标前必须全部通过：

1. 深浅两个文件均存在、尺寸和命名正确。
2. 两个变体的几何轮廓和镜头一致。
3. 104px 下不看标题也能辨认游戏。
4. 与最相近的另一款游戏并排时，轮廓不会混淆。
5. 主体无裁切、无错误文字、无水印、无异常零件。
6. 深色版在幽蓝冷钢和曜石黑钛中对比度合格。
7. 浅色版在月白云瓷和橘光晴釉中边界、按钮和主体层次清楚。
8. 大厅运行时只加载当前主题需要的一个变体。
9. 本目录没有 SVG、PNG、草稿或孤立变体，`npm run verify:game-icons` 通过。
10. 新图标已与三款现有图标在 142px、104px、72px 下并排审查，仍属于同一家族。
