import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  clearAccountToken,
  loginAccount,
  rememberAccountToken,
  storedAccountToken,
  validateAccountToken,
} from './account'

afterEach(() => {
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('account service', () => {
  it('persists the account session across browser restarts', () => {
    rememberAccountToken('account-token')
    expect(storedAccountToken()).toBe('account-token')
    clearAccountToken()
    expect(storedAccountToken()).toBeNull()
  })

  it('sends both the front-door token and login credentials', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ok: true,
          token: 'account-token',
          account: {
            id: 'a1',
            username: 'player',
            displayName: '玩家',
            createdAt: '2026-08-01T00:00:00+00:00',
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await loginAccount('access-token', {
      username: 'player',
      password: 'secret123',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/login',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'X-Avalon-Access': 'access-token',
        }),
      }),
    )
  })

  it('restores the saved account profile', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            ok: true,
            account: {
              id: 'a1',
              username: 'player',
              displayName: '玩家',
              createdAt: '2026-08-01T00:00:00+00:00',
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    await expect(
      validateAccountToken('access-token', 'account-token'),
    ).resolves.toMatchObject({ username: 'player', displayName: '玩家' })
  })
})
