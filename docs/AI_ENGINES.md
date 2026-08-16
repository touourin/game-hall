# 本地游戏 AI

游戏大厅通过统一机器人组件接入三套本地 AI：

- 中国象棋：Pikafish `Pikafish-2026-01-02`
- 围棋：KataGo `v1.17.2`，Eigen CPU 后端，`b10c384h6nbttflrs` 小模型
- 斗地主：DouZero `1.1.0` 官方预训练模型，按需选装

正式 Docker 镜像会在构建时下载、校验并编译 Pikafish 与 KataGo；斗地主的
DouZero 依赖与本地权重按需打入同一个自包含镜像。容器启动后不需要联网，也不依赖
宿主机模型挂载。AI 进程按需启动并复用；计算超时或进程退出时，服务端会使用各游戏
的安全兜底动作完成当前回合，房间不会卡死。

Docker 构建默认使用阿里云 Debian/PyPI 镜像和 GitHub 下载代理，以适配国内服务器。
随默认镜像构建的引擎源码和模型都会校验固定的 SHA-256；代理异常或文件内容变化时
构建会直接失败。需要直连官方源时，可将 `DEBIAN_MIRROR`、`DEBIAN_SECURITY_MIRROR`、
`GITHUB_DOWNLOAD_PREFIX` 和 `PIP_INDEX_URL` 作为 build args 覆盖。

KataGo 在应用启动后会用 1 visit 在后台预热，避免第一位玩家承担模型加载时间。
互动对局的三档搜索量分别为 4、16、48 visits，单次分析最多 10 秒；同一进程最多
同时分析两个局面并保留两个排队位置，队列满或等待超时会自动使用内置棋手。
Eigen 后端最多使用 4 个 CPU 线程，多个房间共享同一个模型进程，不会为每个房间
重复加载模型。

斗地主只提供 DouZero 模型 AI，不再把随机或规则评分策略作为可选择的 AI 难度。
经典和不洗牌玩法共用相同的牌型与动作空间，均可添加 DouZero AI 玩家；癞子改变了
动作空间，暂不开放 AI。模型未配置时房间视图不会显示添加 AI 的空席入口，服务端也
会拒绝对应请求。

应用启动后会通过与围棋相同的通用预热流程启动 DouZero worker，并实际加载、验证
三个角色模型。只有预热成功时新房间才开放 AI 空席；进程后续失败时空席会再次关闭，
已有牌局使用安全兜底并允许后续请求重新拉起进程。

正式出牌由三个角色模型决策。叫地主和抢地主不使用固定手牌评分：服务端从 AI 可见的
37 张未知牌中默认采样 32 组底牌，分别构造假设成为地主后的起始局面，批量取得
DouZero 的最佳首手价值，再按有利样本比例决定叫或抢。这个过程不会读取真实底牌或
对手隐藏手牌。模型调用失败时，叫抢选择不叫/不抢；进行中的出牌选择不出，若必须
领出则使用权威规则生成的第一手合法牌。这些动作只负责故障恢复，不是正常 AI 策略。

DouZero 使用单个按需启动的 CPU 进程，三个角色模型只加载一次并由全部房间共享；
默认限制为 1 个 CPU 线程，单次决策最多等待 8 秒。

三个 DouZero 网络的 FP32 参数合计约 17 MiB，主要磁盘与常驻内存开销来自 PyTorch，
应按数百 MiB 预留。服务端只维护一个共享进程，不会随房间数重复加载模型；不启用
DouZero 时则没有这部分依赖、进程和内存占用。

DouZero 官方代码不随预训练权重一起发布，因此默认 Docker 构建不会安装 PyTorch，
也不会下载无法固定校验地址的模型。不配置时仍可进行三人对局，但不能添加斗地主
AI 玩家。首次启用时：

1. 从 DouZero 官方 README 指向的模型下载页取得一组同目标的三个权重。
2. 将它们命名为 `landlord.ckpt`、`landlord_up.ckpt`、`landlord_down.ckpt`，放入
   `./ai/douzero`。
3. 在 `.env` 设置 `INSTALL_DOUZERO_AI=1` 后重新构建镜像。

构建会先确认三个文件齐全且非空，生成 `SHA256SUMS`，再通过正式 worker 真实加载
三个角色模型；任一步失败都不会替换当前运行的应用。验证通过的模型会直接进入最终
镜像，Compose 不再挂载宿主机模型目录。因此权重只需在构建机器上取得一次，之后该
镜像可以独立部署。应用启动预热成功后才开放 AI，避免半套、损坏或不兼容的权重进入
房间。`ai/douzero` 已被 Git 忽略，代码更新不会覆盖它；后续需要重新构建镜像时应
继续保留这三个源文件。

## 本机开发

象棋和围棋没有安装外部引擎时仍可使用内置降级棋手；斗地主只有完整配置 DouZero
后才开放 AI 席位。设置以下环境变量：

```text
PIKAFISH_PATH=/absolute/path/to/pikafish
PIKAFISH_EVAL_FILE=/absolute/path/to/pikafish.nnue
KATAGO_PATH=/absolute/path/to/katago
KATAGO_MODEL_PATH=/absolute/path/to/b10c384h6nbttflrs.bin.gz
KATAGO_CONFIG_PATH=/absolute/path/to/katago-analysis.cfg
DOUZERO_MODEL_DIR=/absolute/path/to/douzero_WP
```

本机还需安装可选依赖：

```bash
pip install -e './backend[doudizhu-ai]'
```

可选资源限制：`PIKAFISH_THREADS`（默认 1）、`PIKAFISH_HASH_MB`（默认 64）、
`DOUZERO_THREADS`（默认 1）和 `DOUZERO_BID_SAMPLES`（默认 32，范围 1–256）。
如需隔离 PyTorch，也可通过 `DOUZERO_PYTHON_PATH` 指定装有 `douzero` 与 `torch`
的 Python 解释器。

## 依赖与许可证

Pikafish 程序使用 GPL-3.0，但官方 `pikafish.nnue` 权重另有条款：未经许可不得商用。
如果该项目用于商业服务，需要先取得权重许可或换成许可证合适且兼容的权重。
KataGo 使用其仓库中的宽松许可证，所带第三方代码各自保留原许可证。镜像内
`/usr/share/game-hall/licenses` 保存全部随镜像分发的许可证，Pikafish 对应版本的
完整源代码保存在 `/usr/share/game-hall/source/pikafish`。

DouZero 代码使用 Apache-2.0；预训练权重由用户从官方链接单独取得，本项目不重新
分发。公开或商用部署前仍应自行确认所选权重的适用条款。

- https://github.com/official-pikafish/Pikafish
- https://github.com/official-pikafish/Networks
- https://github.com/lightvector/KataGo
- https://github.com/kwai/DouZero
