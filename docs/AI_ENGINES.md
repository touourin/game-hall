# 本地棋类 AI

游戏大厅通过统一机器人组件接入两个离线引擎：

- 中国象棋：Pikafish `Pikafish-2026-01-02`
- 围棋：KataGo `v1.17.2`，Eigen CPU 后端，`b10c384h6nbttflrs` 小模型

正式 Docker 镜像会在构建时下载、校验并编译它们。容器启动后不需要联网。AI
进程按需启动并复用；计算超时、进程退出或本地没有安装引擎时，服务端会自动改用
内置合法走法，房间不会卡死。

Docker 构建默认使用阿里云 Debian/PyPI 镜像和 GitHub 下载代理，以适配国内服务器。
所有引擎源码和模型都会校验固定的 SHA-256；代理异常或文件内容变化时构建会直接
失败。需要直连官方源时，可将 `DEBIAN_MIRROR`、`DEBIAN_SECURITY_MIRROR`、
`GITHUB_DOWNLOAD_PREFIX` 和 `PIP_INDEX_URL` 作为 build args 覆盖。

KataGo 在应用启动后会用 1 visit 在后台预热，避免第一位玩家承担模型加载时间。
互动对局的三档搜索量分别为 4、16、48 visits，单次分析最多 10 秒；同一进程最多
同时分析两个局面并保留两个排队位置，队列满或等待超时会自动使用内置棋手。
Eigen 后端最多使用 4 个 CPU 线程，多个房间共享同一个模型进程，不会为每个房间
重复加载模型。

## 本机开发

没有安装外部引擎也能测试完整的人机流程，只是会使用内置棋手。若要启用完整棋力，
设置以下环境变量：

```text
PIKAFISH_PATH=/absolute/path/to/pikafish
PIKAFISH_EVAL_FILE=/absolute/path/to/pikafish.nnue
KATAGO_PATH=/absolute/path/to/katago
KATAGO_MODEL_PATH=/absolute/path/to/b10c384h6nbttflrs.bin.gz
KATAGO_CONFIG_PATH=/absolute/path/to/katago-analysis.cfg
```

可选资源限制：`PIKAFISH_THREADS`（默认 1）和 `PIKAFISH_HASH_MB`（默认 64）。

## 依赖与许可证

Pikafish 程序使用 GPL-3.0，但官方 `pikafish.nnue` 权重另有条款：未经许可不得商用。
如果该项目用于商业服务，需要先取得权重许可或换成许可证合适且兼容的权重。
KataGo 使用其仓库中的宽松许可证，所带第三方代码各自保留原许可证。镜像内
`/usr/share/game-hall/licenses` 保存全部随镜像分发的许可证，Pikafish 对应版本的
完整源代码保存在 `/usr/share/game-hall/source/pikafish`。

- https://github.com/official-pikafish/Pikafish
- https://github.com/official-pikafish/Networks
- https://github.com/lightvector/KataGo
