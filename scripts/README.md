# 服务重启脚本

`restart.py` 使用 Docker Compose 重新构建并重启 Avalon。它会根据脚本自身的位置寻找仓库根目录，因此既能用于本机目录，也能用于 `/opt/Avalon` 这样的服务器目录。

重新构建当前代码：

```bash
python3 scripts/restart.py
```

以 `--ff-only` 方式拉取当前 Git 分支，再重新构建并重启：

```bash
python3 scripts/restart.py --pull
```

从另一台电脑远程更新服务器：

```bash
ssh root@SERVER_IP 'cd /opt/Avalon && python3 scripts/restart.py --pull'
```

当 Git 工作区存在未提交文件时，`--pull` 会拒绝运行。脚本会检查 Docker 和 `.env`、执行 Compose 数据库迁移依赖、只重新构建应用镜像、等待应用健康检查，并在失败时打印最近的应用日志。它不会执行 `docker compose down -v`，也不会删除 MySQL 或 Redis 数据卷。
