import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  clearAccountToken,
  clearAccountTokenIfCurrent,
  confirmPasswordReset,
  createGuestSession,
  loginAccount,
  rememberAccountToken,
  requestEmailBindingCode,
  requestPasswordResetCode,
  selectAvatarPreset,
  storedAccountToken,
  uploadAvatar,
  validateAccountToken,
  verifyEmailBinding,
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

  it('migrates a legacy Avalon account session', () => {
    localStorage.setItem('avalon:account-token', 'legacy-account-token')

    expect(storedAccountToken()).toBe('legacy-account-token')
    expect(localStorage.getItem('game-hall:account-token')).toBe('legacy-account-token')
    expect(localStorage.getItem('avalon:account-token')).toBeNull()
  })

  it('only clears the login token that was actually replaced', () => {
    rememberAccountToken('new-login-token')

    expect(clearAccountTokenIfCurrent('old-login-token')).toBe(false)
    expect(storedAccountToken()).toBe('new-login-token')
    expect(clearAccountTokenIfCurrent('new-login-token')).toBe(true)
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
            playerName: '玩家昵称',
            nextRenameAt: null,
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
          'X-Game-Hall-Access': 'access-token',
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
              playerName: '玩家昵称',
              nextRenameAt: null,
              createdAt: '2026-08-01T00:00:00+00:00',
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    await expect(
      validateAccountToken('access-token', 'account-token'),
    ).resolves.toMatchObject({ username: 'player', playerName: '玩家昵称' })
  })

  it('uses the expected authenticated email and password-reset endpoints', async () => {
    const account = {
      id: 'a1',
      username: 'player',
      playerName: '玩家昵称',
      nextRenameAt: null,
      email: 'player@example.com',
      emailVerified: true,
      createdAt: '2026-08-01T00:00:00+00:00',
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ message: '验证码已发送' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ message: '密码已重置' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ message: '绑定验证码已发送' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ account, message: '邮箱绑定成功' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    await requestPasswordResetCode('access-token', 'player')
    await confirmPasswordReset('access-token', {
      identifier: 'player@example.com',
      code: '123456',
      newPassword: 'new-secret',
    })
    await requestEmailBindingCode(
      'access-token',
      'account-token',
      'player@example.com',
    )
    await verifyEmailBinding(
      'access-token',
      'account-token',
      'player@example.com',
      '654321',
    )

    expect(fetchMock.mock.calls[0]).toEqual([
      '/api/auth/password-reset/code',
      expect.objectContaining({ body: JSON.stringify({ identifier: 'player' }) }),
    ])
    expect(fetchMock.mock.calls[1]).toEqual([
      '/api/auth/password-reset/confirm',
      expect.objectContaining({
        body: JSON.stringify({
          identifier: 'player@example.com',
          code: '123456',
          new_password: 'new-secret',
        }),
      }),
    ])
    expect(fetchMock.mock.calls[2]?.[1]).toEqual(
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer account-token',
        }),
        body: JSON.stringify({ email: 'player@example.com' }),
      }),
    )
    expect(fetchMock.mock.calls[3]?.[1]).toEqual(
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer account-token',
        }),
        body: JSON.stringify({
          email: 'player@example.com',
          code: '654321',
        }),
      }),
    )
  })

  it('creates a temporary guest session through the front door', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ok: true,
          token: 'guest-token',
          account: {
            id: 'guest:1',
            username: '',
            playerName: '临时骑士',
            nextRenameAt: null,
            avatarType: 'preset',
            avatarPreset: 'moon-fox',
            avatarUrl: '/avatars/moon-fox.webp',
            createdAt: '2026-08-02T00:00:00+00:00',
            isGuest: true,
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await createGuestSession('access-token', '临时骑士')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/guest',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'X-Game-Hall-Access': 'access-token',
        }),
        body: JSON.stringify({ player_name: '临时骑士' }),
      }),
    )
  })

  it('selects a built-in avatar with the authenticated account', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ok: true,
          account: {
            id: 'a1',
            username: 'player',
            playerName: '玩家昵称',
            nextRenameAt: null,
            avatarType: 'preset',
            avatarPreset: 'jade-owl',
            avatarUrl: '/avatars/jade-owl.webp',
            createdAt: '2026-08-01T00:00:00+00:00',
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await selectAvatarPreset('access-token', 'account-token', 'jade-owl')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/me/avatar',
      expect.objectContaining({
        method: 'PATCH',
        headers: expect.objectContaining({
          Authorization: 'Bearer account-token',
          'X-Game-Hall-Access': 'access-token',
        }),
        body: JSON.stringify({ preset: 'jade-owl' }),
      }),
    )
  })

  it('uploads the original image body for server-side normalization', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ok: true,
          account: {
            id: 'a1',
            username: 'player',
            playerName: '玩家昵称',
            nextRenameAt: null,
            avatarType: 'custom',
            avatarPreset: 'moon-fox',
            avatarUrl: '/api/avatars/random-token',
            createdAt: '2026-08-01T00:00:00+00:00',
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['png-data'], 'avatar.png', { type: 'image/png' })

    await uploadAvatar('access-token', 'account-token', file)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/me/avatar',
      expect.objectContaining({
        method: 'PUT',
        headers: expect.objectContaining({
          Authorization: 'Bearer account-token',
          'Content-Type': 'image/png',
        }),
        body: file,
      }),
    )
  })

  it('rejects unsupported avatar files before making a request', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      uploadAvatar(
        'access-token',
        'account-token',
        new File(['text'], 'avatar.txt', { type: 'text/plain' }),
      ),
    ).rejects.toThrow('仅支持')
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
