const ACCOUNT_TOKEN_KEY = 'game-hall:account-token'
const LEGACY_ACCOUNT_TOKEN_KEY = 'avalon:account-token'

export interface AccountProfile {
  id: string
  username: string
  playerName: string
  nextRenameAt: string | null
  avatarType?: 'preset' | 'custom'
  avatarPreset?: AvatarPresetId
  avatarUrl?: string
  email?: string | null
  emailVerified?: boolean
  createdAt: string
  isGuest?: boolean
}

export const AVATAR_PRESETS = [
  { id: 'moon-fox', name: '月影游侠', url: '/avatars/moon-fox.webp' },
  { id: 'jade-owl', name: '翡翠先知', url: '/avatars/jade-owl.webp' },
  { id: 'sun-lion', name: '曜日骑士', url: '/avatars/sun-lion.webp' },
  { id: 'cloud-rabbit', name: '流云乐师', url: '/avatars/cloud-rabbit.webp' },
  { id: 'ember-cat', name: '余烬剑士', url: '/avatars/ember-cat.webp' },
  { id: 'frost-wolf', name: '霜原守望', url: '/avatars/frost-wolf.webp' },
  { id: 'star-deer', name: '星林祭司', url: '/avatars/star-deer.webp' },
  { id: 'ink-dragon', name: '玄墨术士', url: '/avatars/ink-dragon.webp' },
] as const

export type AvatarPresetId = (typeof AVATAR_PRESETS)[number]['id']

export const MAX_AVATAR_UPLOAD_BYTES = 8 * 1024 * 1024
export const ACCEPTED_AVATAR_TYPES = [
  'image/gif',
  'image/jpeg',
  'image/png',
  'image/webp',
]

interface AuthResponse {
  ok: boolean
  token: string
  account: AccountProfile
}

export interface PasswordResetCodeResult {
  sent: boolean
  message: string
}

export interface EmailCodeResult {
  message: string
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

export function clearAccountTokenIfCurrent(expectedToken: string): boolean {
  if (!expectedToken || storedAccountToken() !== expectedToken) return false
  clearAccountToken()
  return true
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
  payload: {
    username: string
    player_name: string
    password: string
    email?: string
    email_code?: string
  },
): Promise<AuthResponse> {
  const response = await authFetch('/api/auth/register', accessToken, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw await responseError(response)
  return (await response.json()) as AuthResponse
}

export async function requestRegistrationEmailCode(
  accessToken: string,
  email: string,
): Promise<EmailCodeResult> {
  const response = await authFetch(
    '/api/auth/register/email/code',
    accessToken,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    },
  )
  if (!response.ok) throw await responseError(response)
  return (await response.json()) as EmailCodeResult
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

export async function requestPasswordResetCode(
  accessToken: string,
  identifier: string,
): Promise<PasswordResetCodeResult> {
  const response = await authFetch('/api/auth/password-reset/code', accessToken, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ identifier }),
  })
  if (!response.ok) throw await responseError(response)
  return (await response.json()) as PasswordResetCodeResult
}

export async function confirmPasswordReset(
  accessToken: string,
  payload: { identifier: string; code: string; newPassword: string },
): Promise<string> {
  const response = await authFetch(
    '/api/auth/password-reset/confirm',
    accessToken,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        identifier: payload.identifier,
        code: payload.code,
        new_password: payload.newPassword,
      }),
    },
  )
  if (!response.ok) throw await responseError(response)
  const data = (await response.json()) as { message: string }
  return data.message
}

export async function createGuestSession(
  accessToken: string,
  playerName: string,
): Promise<AuthResponse> {
  const response = await authFetch('/api/auth/guest', accessToken, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName }),
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

export async function requestEmailBindingCode(
  accessToken: string,
  token: string,
  email: string,
): Promise<string> {
  const response = await authFetch('/api/auth/me/email/code', accessToken, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  })
  if (!response.ok) throw await responseError(response)
  const data = (await response.json()) as { message: string }
  return data.message
}

export async function verifyEmailBinding(
  accessToken: string,
  token: string,
  email: string,
  code: string,
): Promise<{ account: AccountProfile; message: string }> {
  const response = await authFetch('/api/auth/me/email/verify', accessToken, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, code }),
  })
  if (!response.ok) throw await responseError(response)
  return (await response.json()) as {
    account: AccountProfile
    message: string
  }
}

export async function requestEmailUnbindCode(
  accessToken: string,
  token: string,
): Promise<EmailCodeResult> {
  const response = await authFetch(
    '/api/auth/me/email/unbind/code',
    accessToken,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    },
  )
  if (!response.ok) throw await responseError(response)
  return (await response.json()) as EmailCodeResult
}

export async function unbindEmail(
  accessToken: string,
  token: string,
  code: string,
): Promise<{ account: AccountProfile; message: string }> {
  const response = await authFetch(
    '/api/auth/me/email/unbind',
    accessToken,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code }),
    },
  )
  if (!response.ok) throw await responseError(response)
  return (await response.json()) as {
    account: AccountProfile
    message: string
  }
}

export async function selectAvatarPreset(
  accessToken: string,
  token: string,
  preset: AvatarPresetId,
): Promise<AccountProfile> {
  const response = await authFetch('/api/auth/me/avatar', accessToken, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ preset }),
  })
  if (!response.ok) throw await responseError(response)
  const data = (await response.json()) as {
    ok: boolean
    account: AccountProfile
  }
  return data.account
}

export async function uploadAvatar(
  accessToken: string,
  token: string,
  file: File,
): Promise<AccountProfile> {
  if (!ACCEPTED_AVATAR_TYPES.includes(file.type)) {
    throw new Error('仅支持 JPEG、PNG、WebP 或 GIF 图片')
  }
  if (file.size > MAX_AVATAR_UPLOAD_BYTES) {
    throw new Error('头像图片不能超过 8 MB')
  }
  const response = await authFetch('/api/auth/me/avatar', accessToken, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': file.type,
    },
    body: file,
  })
  if (!response.ok) throw await responseError(response)
  const data = (await response.json()) as {
    ok: boolean
    account: AccountProfile
  }
  return data.account
}
