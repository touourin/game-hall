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

房间生命周期还会记录以下自动事件：

- `room.disconnect_forfeit`：仍有真人在线时，某位玩家掉线超过 10 分钟并被判定弃权。
- `room.disconnect_timeout_resolved`：游戏已不需要对该玩家执行额外的掉线弃权动作。
- `room.cleanup_ready`：所有真人离线满 10 分钟，房间进入可清理状态；该事件不代表产生胜负。
- `room.abandoned`：玩家主动放弃单人挑战，或认输并退出多人对局。
- `account.active_room_conflict`：同一账号已占用一个房间时，又尝试创建或加入其他房间。
- `account.session_replaced`：注册账号产生新登录会话，数据库中的旧会话已失效。
- `account.session_connections_revoked`：新登录已通知并断开旧会话仍然在线的 Socket；`connection_count` 表示断开的连接数。
- `account.session_notification_failed`：新令牌已经生效，但旧连接的即时下线通知发生异常；旧连接后续操作仍会被会话校验拒绝。
- `account.stale_session_rejected`：旧会话未及时断开并继续提交实时操作，服务端拒绝该操作并强制下线。
- `guest.created`：通过访问密码后创建了临时游客身份；只记录游客标识，不记录游客 Token。
- `match.skipped_guest`：完成的对局包含游客，因此整局未写入 MySQL 战绩。

日志不会写入访问密码、账号密码、登录或游客 Token、请求正文或聊天内容。游客的 `account_id` 使用 `guest:` 前缀，便于排查连接和房间生命周期，但不能用于恢复游客凭证。

所有游戏（包括阿瓦隆）共用 `arcade:*` 实时协议。因此阿瓦隆创建、开局和玩法操作会分别记录为 `arcade:create`、`arcade:start`、`arcade:action`，具体动作写入 `action` 字段；旧的 `room:*`、`game:*` 和 `lobby:*` 事件不再产生。

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
