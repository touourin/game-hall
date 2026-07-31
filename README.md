# 圆桌密令 · Avalon LAN

一个为手机和局域网设计的阿瓦隆实时房间。服务端掌握完整状态，每台手机只会收到该玩家有权看到的信息。

## 已实现

- 5–10 人创建、加入和重新连接房间
- 访问密码之后的个人账号注册、登录和 30 天会话保持
- 常用角色预设：梅林、派西维尔、刺客、莫甘娜、莫德雷德、奥伯伦
- 队长轮换、组队、公开表决和五次否决判负
- 完整组队投票复盘：队长、队伍、逐人赞成/反对和任务结果
- 私密任务票、第四任务双失败规则
- 三次成功后的刺杀梅林阶段与完整刺杀记录
- 可选“提前刺杀”房规：刺客可在任务期间豪赌梅林，刺错则好人立即获胜
- 湖中仙女：第 2、3、4 次任务后查验阵营、传递持有者、限制重复查验
- 湖中仙女历史：查验链公开、个人结果私密、结算后显示真实阵营
- 刺杀阶段公开所有玩家阵营（包括奥伯伦），结算后再公开具体身份
- 房间实时文字聊天、未读提示、最近 100 条消息记录
- 首页公开房间列表、快速选择加入、房主隐藏房间
- 真人全部离线时立即隐藏圆桌，5 分钟内无人回来则自动清理
- 玩家整局固定编号，选队、聊天和复盘统一显示
- 房主可添加带统一号码与 AI 标识的测试玩家，自动完成组队、投票及必要特殊动作
- 个人战绩与完整对局详情；含 AI 的测试局会记录，但不会影响排行榜
- 仅全部由已登录真人完成的正式局计入排行榜
- 三套本地界面皮肤，不改变好坏阵营与投票结果的语义颜色
- 手机竖屏界面、按住查看身份、房间二维码
- 房主移除大厅玩家、刷新和掉线恢复
- Docker Compose 一键部署应用、MySQL 和 Redis

## 推荐：Docker 部署

服务器需要安装 Docker 和 Docker Compose。

首次部署时复制环境变量模板并设置访问密码：

```bash
cp .env.example .env
```

编辑 `.env` 中的访问密码、MySQL 密码和 Redis 密码，不要把 `.env` 提交到 Git。建议为三个密码分别使用随机值。

```bash
docker compose up -d --build
```

启动后，在服务器或同一局域网的设备访问：

```text
http://服务器内网IP:8800
```

例如：

```text
http://192.168.1.20:8800
```

房主应当使用内网 IP 打开页面，而不是 `localhost`，这样大厅生成的二维码才会包含其他手机能够访问的地址。
所有浏览器必须先通过访问密码验证，再注册或登录个人账号；验证前无法连接房间和游戏服务。

账号、战绩和排行榜保存在 MySQL 命名卷 `mysql-data` 中；Redis 数据保存在 `redis-data` 中。普通的重新构建和重启不会清空这些数据；不要使用 `docker compose down -v`，除非确定要删除全部持久化数据。

停止服务：

```bash
docker compose down
```

## 本地开发

需要 Node.js 24+ 和 Python 3.11+。

```bash
python3 -m venv .venv
.venv/bin/pip install -e 'backend[dev]'
npm install
npm --prefix frontend install
npm run dev
```

开发地址：

- 手机和其他电脑：`http://服务器内网IP:5173`
- 本机：`http://localhost:5173`

前端开发服务会把实时通信和 `/api` 请求代理到 Python 服务。

## 测试与构建

```bash
npm test
npm run build
npm run smoke
```

`npm run smoke` 需要开发服务正在运行，它会通过真实 Socket.IO 连接模拟五名玩家发送聊天消息并完成第一轮任务。

生产构建后，也可以在已经准备好 MySQL 和 Redis、且 `.env` 包含 `DATABASE_URL` 与 `REDIS_URL` 时直接运行：

```bash
.venv/bin/uvicorn backend.app.main:app --env-file .env --host 0.0.0.0 --port 8800 --workers 1
```

然后访问 `http://服务器内网IP:8800`。

## 内网检查

如果手机打不开：

1. 确认手机与服务器连接同一个 Wi‑Fi。
2. 确认访问的是服务器内网 IP，不是 `localhost`。
3. 确认系统防火墙允许 8800 端口。
4. 确认路由器没有开启访客网络或客户端隔离。

## 数据库与实时通信

Docker 部署使用 MySQL 8.4 保存账号、会话、游戏目录、战绩与排行榜，并通过 Alembic 在应用启动前自动执行数据库迁移。表结构已经按多游戏大厅拆分，后续五子棋、围棋和象棋可以共用账号体系，并通过 `games.key` 区分各游戏战绩。

Redis 负责 Socket.IO 跨进程消息协调，并启用 AOF 持久化。当前圆桌、聊天记录和正在进行的阿瓦隆状态仍保存在应用进程内存中：

- 服务重启后，正在进行的房间会消失。
- 服务重启不会丢失账号、登录会话和已结束对局的战绩。
- 聊天消息不会写入数据库。
- 必须保持 `--workers 1`，不能直接启动多个 Uvicorn worker。
- 后续要做多实例或重启续局时，再把房间快照和操作事件持久化到 Redis/MySQL。

MySQL 和 Redis 默认只监听服务器的 `127.0.0.1`，不会暴露到局域网或公网。需要用数据库可视化软件时，推荐建立 SSH 隧道：

```bash
ssh -L 13306:127.0.0.1:3306 root@服务器IP
```

然后在数据库软件中连接 `127.0.0.1:13306`，用户名、密码和数据库名取自服务器的 `.env`。这样无需开放公网 3306；如果本机的 13306 已被占用，可以换成其他本地端口。

备份 MySQL：

```bash
docker exec avalon-mysql sh -c 'exec mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' > avalon-backup.sql
```

## 项目结构

```text
frontend/              Vue 3 + TypeScript + Pinia
backend/app/game/      纯 Python 游戏规则与状态机
backend/app/realtime.py
                       Socket.IO 房间事件
backend/app/views.py   玩家专属状态视图
backend/tests/         规则、安全边界与房间测试
```
