import { io } from 'socket.io-client'

const serverUrl = process.env.AVALON_SERVER_URL ?? 'http://127.0.0.1:10618'
const accessPassword = 'avalon'
const accountPrefix = process.env.AVALON_SMOKE_PREFIX ?? `smk${Date.now().toString(36)}`
const clients = []
const snapshots = []
const waiters = []

function processWaiters() {
  for (const waiter of [...waiters]) {
    if (waiter.predicate()) {
      clearTimeout(waiter.timer)
      waiters.splice(waiters.indexOf(waiter), 1)
      waiter.resolve()
    }
  }
}

function waitUntil(predicate, message) {
  if (predicate()) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const waiter = {
      predicate,
      resolve,
      timer: setTimeout(() => {
        waiters.splice(waiters.indexOf(waiter), 1)
        reject(new Error(`等待超时：${message}`))
      }, 5000),
    }
    waiters.push(waiter)
  })
}

function emitAck(client, event, payload = {}) {
  return new Promise((resolve, reject) => {
    client.timeout(5000).emit(event, payload, (error, response) => {
      if (error) {
        reject(error)
      } else if (!response?.ok) {
        reject(new Error(response?.error ?? `${event} 失败`))
      } else {
        resolve(response)
      }
    })
  })
}

async function jsonRequest(path, options = {}) {
  const response = await fetch(`${serverUrl}${path}`, options)
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail ?? `${path} 失败`)
  return body
}

async function registerAccounts() {
  const access = await jsonRequest('/api/access/unlock', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password: accessPassword }),
  })
  const accounts = []
  for (let index = 0; index < 5; index += 1) {
    accounts.push(
      await jsonRequest('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Game-Hall-Access': access.token,
        },
        body: JSON.stringify({
          username: `${accountPrefix}_${index + 1}`,
          password: 'SmokePass123!',
          player_name: `测试玩家${index + 1}`,
        }),
      }),
    )
  }
  return { accessToken: access.token, accounts }
}

async function newClient(index, accessToken, accountToken) {
  const client = io(serverUrl, {
    autoConnect: false,
    auth: { token: accessToken, accountToken },
    transports: ['websocket'],
  })
  client.on('arcade:snapshot', (snapshot) => {
    if (snapshot.gameKey !== 'avalon') return
    snapshots[index] = snapshot.game
    processWaiters()
  })
  clients[index] = client
  client.connect()
  await new Promise((resolve, reject) => {
    client.once('connect', resolve)
    client.once('connect_error', reject)
  })
  return client
}

try {
  const { accessToken, accounts } = await registerAccounts()
  const host = await newClient(0, accessToken, accounts[0].token)
  const created = await emitAck(host, 'arcade:create', {
    game_key: 'avalon',
    options: {
      mode: 'standard',
      ladyEnabled: true,
      listed: true,
      earlyAssassinationEnabled: false,
    },
  })
  const lobbyBeforeStart = await emitAck(host, 'arcade:list')
  if (
    !lobbyBeforeStart.rooms?.some(
      (room) => room.roomCode === created.roomCode,
    )
  ) {
    throw new Error('新建的公开房间没有出现在大厅列表')
  }

  for (let index = 1; index < 5; index += 1) {
    const client = await newClient(index, accessToken, accounts[index].token)
    await emitAck(client, 'arcade:join', {
      game_key: 'avalon',
      room_code: created.roomCode,
    })
  }

  await waitUntil(
    () => snapshots.length === 5 && snapshots.every(Boolean),
    '五名玩家进入大厅',
  )
  await emitAck(clients[1], 'arcade:chat', { content: '第一轮我赞成' })
  await waitUntil(
    () =>
      snapshots.every(
        (snapshot) =>
          snapshot.chat.messages.at(-1)?.content === '第一轮我赞成',
      ),
    '聊天消息同步',
  )
  await emitAck(host, 'arcade:start')
  await waitUntil(
    () => snapshots.every((snapshot) => snapshot.phase === 'role_reveal'),
    '身份分配',
  )

  for (const client of clients) {
    await emitAck(client, 'arcade:action', { action: 'confirm_role' })
  }
  await waitUntil(
    () => snapshots.every((snapshot) => snapshot.phase === 'team_building'),
    '进入组队阶段',
  )

  const leaderId = snapshots[0].game.leaderId
  const leaderIndex = snapshots.findIndex(
    (snapshot) => snapshot.self.id === leaderId,
  )
  const required = snapshots[0].game.requiredTeamSize
  const teamIds = snapshots[0].players
    .slice(0, required)
    .map((player) => player.id)

  await emitAck(clients[leaderIndex], 'arcade:action', {
    action: 'propose_team',
    payload: { team_ids: teamIds },
  })
  for (const client of clients) {
    await emitAck(client, 'arcade:action', {
      action: 'vote_team',
      payload: { approve: true },
    })
  }
  await waitUntil(
    () => snapshots.every((snapshot) => snapshot.phase === 'mission_voting'),
    '进入任务投票',
  )
  await waitUntil(
    () =>
      snapshots.every(
        (snapshot) => snapshot.game.proposalHistory.length === 1,
      ),
    '记录组队投票复盘',
  )
  const lobbyAfterStart = await emitAck(host, 'arcade:list')
  if (
    lobbyAfterStart.rooms?.some(
      (room) => room.roomCode === created.roomCode,
    )
  ) {
    throw new Error('已经开局的房间仍出现在大厅列表')
  }

  for (const playerId of teamIds) {
    const clientIndex = snapshots.findIndex(
      (snapshot) => snapshot.self.id === playerId,
    )
    await emitAck(clients[clientIndex], 'arcade:action', {
      action: 'vote_mission',
      payload: { success: true },
    })
  }
  await waitUntil(
    () => snapshots.every((snapshot) => snapshot.phase === 'round_result'),
    '任务结算',
  )

  await emitAck(host, 'arcade:action', { action: 'continue_round' })
  await waitUntil(
    () => snapshots.every((snapshot) => snapshot.phase === 'team_building'),
    '进入下一次任务',
  )

  console.log(
    JSON.stringify({
      ok: true,
      accountPrefix,
      roomCode: created.roomCode,
      players: snapshots[0].players.length,
      chatMessages: snapshots[0].chat.messages.length,
      proposalRecords: snapshots[0].game.proposalHistory.length,
      hiddenFromLobbyAfterStart: true,
      completedMissions: snapshots[0].game.missionHistory.length,
      nextMission: snapshots[0].game.missionNumber,
    }),
  )
} finally {
  for (const client of clients) {
    client?.disconnect()
  }
}
