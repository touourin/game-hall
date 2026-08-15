# 官方游戏图标规范

这套资源用于游戏大厅、分类页、房间入口和移动端导航中的官方游戏图标。目标是让所有游戏看起来属于同一套产品，同时保留足够强的游戏识别度。

## 1. 视觉方向

统一方向为 **克制的赛博骨架 + Apple 产品级 2.5D 材质**：

- 图标是一个经过棚拍的精密产品，不是插画、截图或徽章。
- 使用圆润比例、4–6 层结构、精密倒角、柔和高光和真实接触阴影。
- 画面有空间感和材质细节，但在 104px 尺寸下仍能一眼识别。
- 每款游戏只使用一个低饱和点缀色；不依赖颜色区分游戏。
- 所有主题共享同一构图、镜头和轮廓，只切换材质。

禁止使用：人物、电影场景、电竞盾牌、奇幻徽章、强霓虹、卡通造型、廉价手游边框、大段文字、Apple 标志、水印和无意义装饰。

## 2. 双材质资源

每款官方游戏必须同时提供以下两个文件：

| 变体 | 使用主题 | 材质 |
| --- | --- | --- |
| `dark` | 极光雾舱、暖钛陶瓷 | 黑钛、烟熏玻璃、深石墨陶瓷、阳极氧化金属 |
| `light` | 月白陶瓷 | 月白陶瓷、磨砂玻璃、香槟银、浅冷灰金属 |

两个变体必须保持完全一致的主体轮廓、镜头角度、物体数量和空间关系。浅色版不是重新设计，只是同一件产品的另一种材质配置。

## 3. 文件与画布

- 命名：`<game-slug>-dark.webp`、`<game-slug>-light.webp`。
- 格式：WebP，sRGB，768 × 768，质量 90；使用完整方形棚拍背景，不使用透明通道。
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
| `minesweeper` | 方格盘、切面地雷、旗标 | 方板 + 球形雷 | 红色 |
| `hanoi` | 三根立柱、阶梯圆盘 | 递减圆锥塔 | 金色 |
| `tetris` | 竖向游戏舱、合法四格骨牌 | 窄高矩形舱 | 蓝紫 |
| `monopoly` | 城市积木、路线环、骰子 | 城市天际线 | 翡翠绿 |
| `one-night-werewolf` | 月相仪表、狼影遮片、三席节点 | 月盘 + 三节点 | 冷紫 |
| `departed-suspicion` | 指纹扫描器、双人席位、证据槽 | 八角扫描台 | 青绿 |

## 6. 生成提示词模板

后续新增游戏时，在下面模板中只替换方括号内容。必须先制作 `dark`，再以 `dark` 作为几何参考制作 `light`。

```text
Final square game-lobby product icon for [game name].
Identity: [core object and silhouette from the table].
Use the established official icon family: elevated three-quarter product camera,
rounded double plinth, 4–6 material layers, precision bevels, soft studio highlights,
real contact shadows, one restrained accent color, quiet full-square studio backdrop.
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
6. 深色版在极光雾舱和暖钛陶瓷中对比度合格。
7. 浅色版在月白陶瓷中边界、按钮和主体层次清楚。
8. 大厅运行时只加载当前主题需要的一个变体。
