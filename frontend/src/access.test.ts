import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  clearAccessToken,
  rememberAccessToken,
  requestAccessToken,
  storedAccessToken,
  validateAccessToken,
} from './access'

afterEach(() => {
  sessionStorage.clear()
  vi.restoreAllMocks()
})

describe('access service', () => {
  it('stores the access token only for the current browser session', () => {
    rememberAccessToken('session-token')
    expect(storedAccessToken()).toBe('session-token')
    expect(localStorage.getItem('game-hall:access-token')).toBeNull()

    clearAccessToken()
    expect(storedAccessToken()).toBeNull()
  })

  it('migrates the old session-only access key', () => {
    sessionStorage.setItem('internal:access-token', 'legacy-token')

    expect(storedAccessToken()).toBe('legacy-token')
    expect(sessionStorage.getItem('game-hall:access-token')).toBe('legacy-token')
    expect(sessionStorage.getItem('internal:access-token')).toBeNull()
  })

  it('creates the internal transport session without asking for a password', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ ok: true, token: 'server-token' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(requestAccessToken()).resolves.toBe('server-token')
    expect(fetch).toHaveBeenCalledWith('/api/access/session', { method: 'POST' })
  })

  it('validates a saved token with the server', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(validateAccessToken('saved-token')).resolves.toBe(true)
    expect(fetchMock).toHaveBeenCalledWith('/api/access/status', {
      headers: { Authorization: 'Bearer saved-token' },
    })
  })
})
