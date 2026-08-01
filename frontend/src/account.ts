const ACCOUNT_TOKEN_KEY = 'game-hall:account-token'
const LEGACY_ACCOUNT_TOKEN_KEY = 'avalon:account-token'

export interface AccountProfile {
  id: string
  username: string
  playerName: string
  nextRenameAt: string | null
  createdAt: string
}

interface AuthResponse {
  ok: boolean
  token: string
  account: AccountProfile
}

export function storedAccountToken(): string | null {
  const token = localStorage.getItem(ACCOUNT_TOKEN_KEY)
  if (token) return token

  const legacyToken = localStorage.getItem(LEGACY_ACCOUNT_TOKEN_KEY)
  if (!legacyToken) return null

  localStorage.setItem(ACCOUNT_TOKEN_KEY, legacyToken)
  localStorage.removeItem(LEGACY_ACCOUNT_TOKEN_KEY)
  return legacyToken
}

export function rememberAccountToken(token: string): void {
  localStorage.setItem(ACCOUNT_TOKEN_KEY, token)
  localStorage.removeItem(LEGACY_ACCOUNT_TOKEN_KEY)
}

export function clearAccountToken(): void {
  localStorage.removeItem(ACCOUNT_TOKEN_KEY)
  localStorage.removeItem(LEGACY_ACCOUNT_TOKEN_KEY)
}

async function authFetch(
  path: string,
  accessToken: string,
  options: RequestInit = {},
): Promise<Response> {
  try {
    return await fetch(path, {
      ...options,
      headers: {
        'X-Game-Hall-Access': accessToken,
        ...(options.headers ?? {}),
      },
    })
  } catch {
    throw new Error('无法连接服务器，请检查网络')
  }
}

async function responseError(response: Response): Promise<Error> {
  try {
    const data = (await response.json()) as { detail?: string }
    return new Error(data.detail ?? '操作失败，请稍后重试')
  } catch {
    return new Error('操作失败，请稍后重试')
  }
}

export async function registerAccount(
  accessToken: string,
  payload: { username: string; player_name: string; password: string },
): Promise<AuthResponse> {
  const response = await authFetch('/api/auth/register', accessToken, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw await responseError(response)
  return (await response.json()) as AuthResponse
}

export async function loginAccount(
  accessToken: string,
  payload: { username: string; password: string },
): Promise<AuthResponse> {
  const response = await authFetch('/api/auth/login', accessToken, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw await responseError(response)
  return (await response.json()) as AuthResponse
}

export async function validateAccountToken(
  accessToken: string,
  token: string,
): Promise<AccountProfile | null> {
  const response = await authFetch('/api/auth/me', accessToken, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (response.status === 401) return null
  if (!response.ok) throw await responseError(response)
  const data = (await response.json()) as {
    ok: boolean
    account: AccountProfile
  }
  return data.account
}

export async function logoutAccount(
  accessToken: string,
  token: string,
): Promise<void> {
  await authFetch('/api/auth/logout', accessToken, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
}

export async function renamePlayer(
  accessToken: string,
  token: string,
  playerName: string,
): Promise<AccountProfile> {
  const response = await authFetch('/api/auth/me', accessToken, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ player_name: playerName }),
  })
  if (!response.ok) throw await responseError(response)
  const data = (await response.json()) as {
    ok: boolean
    account: AccountProfile
  }
  return data.account
}
