# 圆桌密令 · Avalon LAN

一个为手机和局域网设计的阿瓦隆实时房间。服务端掌握完整状态，每台手机只会收到该玩家有权看到的信息。

## 已实现

- 5–10 人创建、加入和重新连接房间
- 常用角色预设：梅林、派西维尔、刺客、莫甘娜、莫德雷德、奥伯伦
- 队长轮换、组队、公开表决和五次否决判负
- 完整组队投票复盘：队长、队伍、逐人赞成/反对和任务结果
- 私密任务票、第四任务双失败规则
- 三次成功后的刺杀梅林阶段与完整刺杀记录
- 可选“提前刺杀”房规：刺客可在任务期间豪赌梅林，刺错则好人立即获胜
- 湖中仙女：第 2、3、4 次任务后查验阵营、传递持有者、限制重复查验
- 湖中仙女历史：查验链公开、个人结果私密、结算后显示真实阵营
- 房间实时文字聊天、未读提示、最近 100 条消息记录
- 首页公开房间列表、快速选择加入、房主隐藏房间
- 玩家整局固定编号，选队、聊天和复盘统一显示
- 房主可在任意游戏阶段修改其他玩家的显示名称
- 手机竖屏界面、按住查看身份、房间二维码
- 房主移除大厅玩家、刷新和掉线恢复
- Docker 单容器内网部署

## 推荐：Docker 部署

服务器需要安装 Docker 和 Docker Compose。

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

生产构建后，也可以直接运行：

```bash
.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8800 --workers 1
```

然后访问 `http://服务器内网IP:8800`。

## 内网检查

如果手机打不开：

1. 确认手机与服务器连接同一个 Wi‑Fi。
2. 确认访问的是服务器内网 IP，不是 `localhost`。
3. 确认系统防火墙允许 8800 端口。
4. 确认路由器没有开启访客网络或客户端隔离。

## 当前存储方式

房间和游戏进度保存在单个服务进程的内存中：

- 服务重启后，正在进行的房间会消失。
- 必须保持 `--workers 1`，不能直接启动多个 Uvicorn worker。
- 当前方式足够用于内网聚会；以后需要持久化或多实例时再接 Redis。

## 项目结构

```text
frontend/              Vue 3 + TypeScript + Pinia
backend/app/game/      纯 Python 游戏规则与状态机
backend/app/realtime.py
                       Socket.IO 房间事件
backend/app/views.py   玩家专属状态视图
backend/tests/         规则、安全边界与房间测试
```
