import { io } from 'socket.io-client'

const baseUrl = process.env.ARCADE_SMOKE_URL ?? 'http://127.0.0.1:8800'
const prefix = process.env.ARCADE_SMOKE_PREFIX ?? `smoke_${Date.now().toString(36)}`
const accessPassword = process.env.ARCADE_SMOKE_ACCESS_PASSWORD ?? 'avalon'
const password = 'SmokePass123!'

async function jsonRequest(path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, options)
  const body = await response.json()
  if (!response.ok) {
    throw new Error(`${path}: ${body.detail ?? response.statusText}`)
  }
  return body
}

async function register(accessToken, index) {
  const username = `${prefix}_${index}`
  const result = await jsonRequest('/api/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Avalon-Access': accessToken,
    },
    body: JSON.stringify({
      username,
      password,
      display_name: `冒烟玩家${index}`,
    }),
  })
  return { ...result, username }
}

function connectClient(accessToken, accountToken) {
  return new Promise((resolve, reject) => {
    const socket = io(baseUrl, {
      auth: { token: accessToken, accountToken },
      transports: ['websocket'],
      reconnection: false,
    })
    socket.once('connect', () => resolve(socket))
    socket.once('connect_error', reject)
  })
}

function emitAck(socket, event, payload = {}) {
  return new Promise((resolve, reject) => {
    socket.timeout(5000).emit(event, payload, (error, response) => {
      if (error) return reject(error)
      if (!response?.ok) {
        return reject(new Error(`${event}: ${response?.error ?? 'unknown error'}`))
      }
      resolve(response)
    })
  })
}

async function playToResignation(gameKey, clients, names) {
  const created = await emitAck(clients[0], 'arcade:create', {
    game_key: gameKey,
    name: names[0],
  })
  for (let index = 1; index < clients.length; index += 1) {
    await emitAck(clients[index], 'arcade:join', {
      game_key: gameKey,
      room_code: created.roomCode,
      name: names[index],
    })
  }
  await emitAck(clients[0], 'arcade:start')
  if (gameKey === 'doudizhu') {
    await emitAck(clients[0], 'arcade:action', {
      action: 'bid',
      payload: { score: 3 },
    })
  }
  await emitAck(clients[0], 'arcade:action', {
    action: 'resign',
    payload: {},
  })
  for (const client of clients) {
    const left = await emitAck(client, 'arcade:leave')
    if (left.seatPreserved) {
      throw new Error(`${gameKey} 已结束房间仍然要求续局`)
    }
  }
  return created.roomCode
}

const sockets = []
try {
  const access = await jsonRequest('/api/access/unlock', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password: accessPassword }),
  })
  const accounts = await Promise.all([1, 2, 3].map((index) => register(access.token, index)))
  for (const account of accounts) {
    sockets.push(await connectClient(access.token, account.token))
  }

  const names = accounts.map((account) => account.account.displayName)
  const rooms = {}
  for (const gameKey of ['gomoku', 'xiangqi', 'go']) {
    rooms[gameKey] = await playToResignation(gameKey, sockets.slice(0, 2), names.slice(0, 2))
  }
  rooms.doudizhu = await playToResignation('doudizhu', sockets, names)

  const headers = {
    Authorization: `Bearer ${accounts[0].token}`,
    'X-Avalon-Access': access.token,
  }
  const catalog = await jsonRequest('/api/games', { headers })
  if (catalog.games.length !== 5) throw new Error('游戏目录数量不是 5')
  for (const gameKey of ['gomoku', 'xiangqi', 'go', 'doudizhu']) {
    const stats = await jsonRequest(`/api/stats/me?game=${gameKey}`, { headers })
    if (stats.summary.games !== 1 || stats.history[0]?.gameKey !== gameKey) {
      throw new Error(`${gameKey} 战绩没有正确保存`)
    }
  }

  process.stdout.write(`${JSON.stringify({ ok: true, prefix, rooms })}\n`)
} finally {
  for (const socket of sockets) socket.disconnect()
}
