# 服务重启脚本

`restart.py` 使用 Docker Compose 重新构建并重启游戏大厅。它会根据脚本自身的位置寻找仓库根目录，不依赖固定目录名；推荐把仓库放在本机的 `game-hall` 目录和服务器的 `/opt/game-hall`。

每次运行都会先以 `--ff-only` 更新主仓库的 `main` 分支，再把所有 Git
Submodule 更新到各自配置的远端分支（`third_party_games` 为 `origin/main`），
然后重新构建并重启：

```bash
python3 scripts/restart.py
```

如果只想用当前已经检出的代码重建，不更新主仓库和第三方仓库：

```bash
python3 scripts/restart.py --no-pull
```

从另一台电脑远程更新服务器：

```bash
ssh root@SERVER_IP 'cd /opt/game-hall && python3 scripts/restart.py'
```

脚本必须在主仓库的 `main` 分支运行；当主仓库存在未提交的受跟踪文件，或子模块存在会被检出覆盖的本地修改时会拒绝更新。脚本会检查 Docker 和 `.env`、执行 Compose 数据库迁移依赖、只重新构建应用镜像、等待应用健康检查，并在失败时打印最近的应用日志。它不会执行 `docker compose down -v`，也不会删除 MySQL 或 Redis 数据卷。
