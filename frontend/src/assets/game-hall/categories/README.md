# 游戏分类导视图规范

这套资源用于大厅一级“游戏分类”入口。分类图表达一组玩法的共同结构，不代表任何一款具体游戏。

制作时的参考优先级是：**运行中的分类总览 > 当前正式资源 > 本文文字规范**。先打开前端看实际画面，再用本文解释为什么它们属于同一套系统；不要只看文字猜风格，也不要在 README 里复制一套容易过期的图片预览。

```bash
cd frontend
npm run dev
```

## 1. 分类与游戏必须是两个视觉层级

分类图和具体游戏图共享低饱和配色、精细材质、克制光影和圆角细节，因此放在同一大厅中不会违和；构图语言必须明显不同：

| 项目 | 分类导视图 | 具体游戏封面 |
| --- | --- | --- |
| 信息层级 | 一组玩法 | 一款具体游戏 |
| 构图 | 满版、裁边、具有明确类别主语义的导视画面 | 居中、完整、独立器物 |
| 视角 | 正视或近似正交俯视 | 略俯视 3/4 产品镜头 |
| 空间 | 画面本身就是材质表面 | 主体置于安静棚拍背景 |
| 深度 | `1–3 mm` 浅浮雕、压印和叠纸 | `4–6` 层结构、厚倒角和真实基座 |
| 识别方式 | 类别原型、大结构和空间关系 | 具体游戏器物和玩法细节 |

分类图禁止使用居中的方形底座、产品台、按钮、旋钮和小零件。否则它会看起来像另一批游戏图标，一级分类与二级游戏的层级会消失。

## 2. 当前正式资源

每个分类有同一主图形与空间关系的 `dark` / `light` 两张 WebP：

| 分类 ID | 分类 | 主体构图 | 基准色 |
| --- | --- | --- | --- |
| `board` | 棋类竞技 | 完整策略网格与两种相向棋子，直接表达对弈 | `#719b8a` |
| `social` | 推理社交 | 多张身份面具交叠，以观察孔表达隐藏与判断 | `#8a7ca6` |
| `cards` | 扑克牌类 | 三张大牌扇形展开，以花色表达牌组而非具体玩法 | `#a97579` |
| `solo` | 单人挑战 | 唯一棋子沿单一路径穿越三道门槛并抵达靶心 | `#6f9da2` |
| `party` | 多人派对 | 五个参与圆点围绕同一节奏核心聚合 | `#a78e64` |
| `community` | 社区游戏 | 四种纹理模块从边缘接入中央扩展接口 | `#b46f35` |

```text
categories/
├── board-dark.webp
├── board-light.webp
├── social-dark.webp
├── social-light.webp
├── cards-dark.webp
├── cards-light.webp
├── solo-dark.webp
├── solo-light.webp
├── party-dark.webp
├── party-light.webp
├── community-dark.webp
├── community-light.webp
└── README.md
```

运行时由 `GameCategoryCard.vue` 根据当前主题只选择一个变体。不要保留同名 SVG、PNG、生成草稿或孤立的单主题资源。

## 3. 如何设计新分类

### 第一步：在真实页面确定视觉边界

打开分类总览，同时进入任意分类看里面的具体游戏封面。新增作品必须满足：

- 与现有分类并排时，满版比例、材质深度和信息密度相近；
- 与具体游戏并排时，一眼能看出它是导视画面而不是新的游戏封面；
- 电脑三列、手机单列和深浅主题中都保持同一层级。

### 第二步：提炼两个分类概念

先写两个并列概念，例如“布局 · 计算”“身份 · 判断”“创意 · 扩展”，再为它们选择一个能代表整类玩法的主图形。

- 主图形可以使用棋盘、牌面、面具、玩家标记等跨游戏的类别原型，但不能指向某个具体游戏；
- 再用区域关系、路径、聚合、对峙、重复或开放留白强化语义；
- 只选一个主结构，不拼贴多款游戏的物件；
- 不使用人物、角色、品牌标志、文字缩写或现有游戏封面；
- 遮住标题时仍应大致判断出所属大类，缩到 `104px` 后仍应保留主语义。

### 第三步：先做深色母版

- 画布：`768 × 768`，sRGB，完整方形背景；
- 构图：至少在两条边被有意识地裁切，避免形成悬浮的居中图标；
- 形状：使用 `3–7` 个大结构，避免密集小线条；
- 材质：炭黑纸、磨砂石、烟熏树脂和少量精细边缘；
- 深度：浅浮雕和压印，不使用厚产品基座；
- 色彩：黑、灰和材质中性色占 `80%–90%`，分类色占 `10%–20%`；
- 光线：近似正面的掠射柔光，只用于解释表面层次。

### 第四步：以母版制作浅色版

浅色版只换材质与明暗关系，必须保留深色版的几何、裁切、比例、接缝和空间关系：

- 月白矿物纸、暖象牙石、雾灰树脂和香槟银边缘；
- 分类色位置不变，可略微加深以保证对比度；
- 不新增或删除结构，不重新生成另一套构图；
- 高光不得过曝，浅色表面仍需看得到接缝和浮雕。

### 第五步：导出并放进页面校准

- 命名：`<category-id>-dark.webp`、`<category-id>-light.webp`；
- 格式：WebP，质量 `90`，`768 × 768`；
- 在 `GameCategoryCard.vue` 中登记资源和同一基准色；
- 图片铺满 `.category-card-art`，不要再套小徽章、轨道或统一方形底盘；
- hover 只做轻微放大，不把分类画面变成悬浮产品。

## 4. 生成提示词骨架

实际生成前仍然先看运行中的页面。下面只负责稳定制作方法，不代替视觉参考。

```text
Final full-bleed game-lobby category wayfinding mural for [category].
Concepts: [two semantic concepts].
Subject: [one recognizable category archetype, reinforced by regions, paths or rhythm].
Premium editorial graphic meets museum wayfinding; front-facing or orthographic;
shallow embossed relief, matte mineral paper, thin smoked resin, precise broad cuts.
The canvas itself is the artwork. Crop large shapes intentionally at 2–4 edges.
The category should remain recognizable with its title hidden and at 104 px.
[dark: charcoal paper, graphite stone, restrained category accent]
[light: preserve exact geometry; moon-white paper, ivory stone, same accent placement]
No isolated object, pedestal, centered rounded-square badge, product camera, buttons,
dials, branded or game-specific props, people, text, logo, watermark, neon or cartoon styling.
```

## 5. 页面布局规格

### 电脑端

- 分类卡片最小高度：`230px`；
- 文案区与视觉区比例约为 `48:52`；
- 视觉区最小高度：`188px`，图片全覆盖；
- 六张图的裁切尺度和视觉重量接近，不要求使用相同中心点。

### 手机端

- 分类卡片最小高度：`148px`；
- 视觉区最小高度：`118px`；
- 小于 `380px` 时可以隐藏描述，但分类名、数量和进入意图必须保留；
- 大结构在窄裁切中仍要清楚，不得产生横向滚动。

## 6. 新增分类流程

1. 在 `frontend/src/gameCategories.ts` 增加稳定英文 ID、名称、眉题、描述和收录规则。
2. 运行前端，对照现有分类总览和分类内具体游戏封面。
3. 在本文“当前正式资源”表中先定义主体构图与基准色。
4. 制作深色母版，检查 `188px`、`118px` 和 `104px` 识别度。
5. 以深色母版制作完全同构的浅色版。
6. 导出成对 WebP，在 `GameCategoryCard.vue` 中登记并设置 `--category-tone`。
7. 更新 `gameCategories.test.ts` 和 `GameCategoryBrowser.test.ts`。
8. 检查电脑三列、平板两列、`390px` 手机单列，以及四套主题。
9. 运行相关测试、类型检查和生产构建。

## 7. 验收清单

1. 已先在运行中的前端对照现有画面，本文只作为文字拆解和制作方法。
2. 分类图是具有明确主语义的满版导视图，不是居中的 3D 游戏器物。
3. 没有复用、缩小、裁切或拼接具体游戏封面。
4. 深浅变体几何与裁切一致，材质适配当前主题。
5. 六个分类的体量接近，但构图不只是同一模板换颜色。
6. 遮住标题仍能大致判断所属分类，`104px` 下主语义仍成立。
7. 手机和电脑无横向溢出，hover 不改变信息层级。
8. 社区游戏仍保留来源标识，不因视觉平级隐藏维护边界。
9. 资源目录没有 SVG、PNG、草稿或孤立变体。
10. 测试和生产构建全部通过。

## 8. 相关文件

- 分类数据：`frontend/src/gameCategories.ts`
- 分类总览与详情：`frontend/src/components/GameCategoryBrowser.vue`
- 分类卡片与主题资源选择：`frontend/src/components/GameCategoryCard.vue`
- 分类导视图：`frontend/src/assets/game-hall/categories/*-{dark,light}.webp`
- 具体游戏封面规范：`frontend/src/assets/game-hall/icons/README.md`
