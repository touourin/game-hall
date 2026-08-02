import { storedAccessToken } from './access'
import { storedAccountToken } from './account'
import {
  ROLE_SKINS,
  ROLE_SKIN_ROLES,
  roleSkinRoleCode,
  type RoleSkinId,
  type RoleSkinRoleCode,
} from './gameRoleSkins'

export interface AvalonRoleSkinRoleProgress {
  wins: number
  upgradeUnlocked: boolean
  ultimateUnlocked: boolean
}

export interface AvalonRoleSkinProgress {
  legacyAllUnlocked: boolean
  rankedOnly: boolean
  upgradeWinsRequired: number
  ultimateWinsRequired: number
  roles: Record<RoleSkinRoleCode, AvalonRoleSkinRoleProgress>
}

export function emptyAvalonRoleSkinProgress(): AvalonRoleSkinProgress {
  return {
    legacyAllUnlocked: false,
    rankedOnly: true,
    upgradeWinsRequired: 2,
    ultimateWinsRequired: 5,
    roles: Object.fromEntries(
      ROLE_SKIN_ROLES.map((role) => [
        role.code,
        { wins: 0, upgradeUnlocked: false, ultimateUnlocked: false },
      ]),
    ) as Record<RoleSkinRoleCode, AvalonRoleSkinRoleProgress>,
  }
}

export function isRoleSkinUnlocked(
  progress: AvalonRoleSkinProgress,
  roleCode: string,
  skinId: RoleSkinId,
): boolean {
  const skin = ROLE_SKINS.find((item) => item.id === skinId)
  if (!skin || skin.tier === '基础') return Boolean(skin)
  if (progress.legacyAllUnlocked) return true
  const family = roleSkinRoleCode(roleCode)
  if (!family) return false
  const role = progress.roles[family]
  return skin.tier === '终极'
    ? role.ultimateUnlocked
    : role.upgradeUnlocked
}

export async function loadAvalonRoleSkinProgress(): Promise<AvalonRoleSkinProgress> {
  const accessToken = storedAccessToken()
  const accountToken = storedAccountToken()
  if (!accessToken || !accountToken) {
    throw new Error('登录状态已失效，请重新登录')
  }

  let response: Response
  try {
    response = await fetch('/api/games/avalon/role-skins/me', {
      headers: {
        'X-Game-Hall-Access': accessToken,
        Authorization: `Bearer ${accountToken}`,
      },
    })
  } catch {
    throw new Error('无法读取身份皮肤进度，请检查网络')
  }

  if (!response.ok) {
    let message = '身份皮肤进度读取失败'
    try {
      const body = (await response.json()) as { detail?: string }
      message = body.detail ?? message
    } catch {}
    throw new Error(message)
  }

  let body: { ok: boolean; progress: AvalonRoleSkinProgress }
  try {
    body = (await response.json()) as {
      ok: boolean
      progress: AvalonRoleSkinProgress
    }
  } catch {
    throw new Error('身份皮肤进度读取失败')
  }
  if (!body.ok || !body.progress?.roles) {
    throw new Error('身份皮肤进度读取失败')
  }
  return body.progress
}
