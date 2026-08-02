import { io } from 'socket.io-client'

export const socket = io({
  autoConnect: false,
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 700,
  reconnectionDelayMax: 3000,
})

let accessToken = ''
let accountToken = ''

function syncSocketAuth(): void {
  socket.auth = { token: accessToken, accountToken }
}

export function setSocketAccessToken(token: string): void {
  accessToken = token
  syncSocketAuth()
}

export function setSocketAccountToken(token: string): void {
  accountToken = token
  syncSocketAuth()
}

export interface AckResponse {
  ok: boolean
  error?: string
  roomCode?: string
  playerId?: string
  resumeToken?: string
  seatPreserved?: boolean
  activeRoom?: boolean
  gameKey?: string
}

export function emitWithAck(
  event: string,
  payload: Record<string, unknown> = {},
): Promise<AckResponse> {
  return new Promise((resolve, reject) => {
    socket.timeout(8000).emit(
      event,
      payload,
      (error: Error | null, response: AckResponse) => {
        if (error) {
          reject(new Error('连接超时，请检查局域网或重试'))
          return
        }
        resolve(response)
      },
    )
  })
}
