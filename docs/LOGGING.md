# 日志与故障排查

应用会把日志同时输出到 Docker 控制台和项目根目录的 `logs/`。日志目录通过 Compose 挂载到容器，重新构建或重启容器不会丢失。

## 日志文件

- `logs/app.log`：启动、HTTP 请求、实时通信拒绝、房间后台任务和全部应用错误。
- `logs/error.log`：只记录 `ERROR` 及以上日志，并保留完整 Python 异常堆栈。
- `logs/app.log.YYYY-MM-DD`、`logs/error.log.YYYY-MM-DD`：按天轮转的历史文件。

日志文件使用一行一条 JSON，常用字段包括：

- `timestamp`：带时区的发生时间。
- `level`：`INFO`、`WARNING` 或 `ERROR`。
- `event`：稳定的事件名称，例如 `http.completed`、`socket.rejected`、`maintenance.failed`。
- `request_id`：HTTP 请求追踪编号，同时通过响应头 `X-Request-ID` 返回。
- `path`、`status_code`、`duration_ms`：请求路径、响应状态和耗时。
- `game_key`、`room_code`：游戏类型和房间代码，例如 `minesweeper`、`avalon`。
- `socket_event`、`action`：实时事件和具体游戏动作；普通高频动作只在 `DEBUG` 级别记录。
- `exception`：错误堆栈，仅在发生异常时出现。

日志不会写入访问密码、账号密码、登录 Token、请求正文或聊天内容。

## 常用命令

查看应用实时输出：

```bash
docker compose logs -f app
```

只查看最近 30 分钟：

```bash
docker compose logs --since 30m app
```

直接跟踪错误文件：

```bash
tail -f logs/error.log
```

按请求编号查找一次请求的全部记录：

```bash
grep '"request_id": "请求编号"' logs/app.log*
```

查看当天所有错误：

```bash
grep '"level": "ERROR"' logs/app.log
```

只查看扫雷或某个房间：

```bash
grep '"game_key": "minesweeper"' logs/app.log*
grep '"room_code": "ABCD"' logs/app.log*
```

## 配置

`.env` 支持以下配置：

```dotenv
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
TZ=Asia/Shanghai
```

日志每天零点轮转，默认保留 30 天，最长可配置为 365 天。Docker 自身的容器日志另外限制为每个文件 20 MB、最多 5 个文件，防止磁盘被无限占用。
