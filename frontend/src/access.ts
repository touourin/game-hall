const ACCESS_TOKEN_KEY = 'game-hall:access-token'
const LEGACY_ACCESS_TOKEN_KEY = 'internal:access-token'

interface UnlockResponse {
  ok: boolean
  token: string
}

export function storedAccessToken(): string | null {
  const token = sessionStorage.getItem(ACCESS_TOKEN_KEY)
  if (token) return token

  const legacyToken = sessionStorage.getItem(LEGACY_ACCESS_TOKEN_KEY)
  if (!legacyToken) return null

  sessionStorage.setItem(ACCESS_TOKEN_KEY, legacyToken)
  sessionStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY)
  return legacyToken
}

export function rememberAccessToken(token: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
  sessionStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY)
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY)
}

export async function validateAccessToken(token: string): Promise<boolean> {
  try {
    const response = await fetch('/api/access/status', {
      headers: { Authorization: `Bearer ${token}` },
    })
    return response.ok
  } catch {
    return false
  }
}

export async function requestAccessToken(password: string): Promise<string> {
  let response: Response
  try {
    response = await fetch('/api/access/unlock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    })
  } catch {
    throw new Error('无法连接服务器，请检查网络')
  }

  if (response.status === 401) {
    throw new Error('密码不正确，请重新输入')
  }
  if (!response.ok) {
    throw new Error('验证失败，请稍后重试')
  }

  const data = (await response.json()) as UnlockResponse
  if (!data.ok || !data.token) {
    throw new Error('服务器返回了无效的访问凭证')
  }
  return data.token
}
