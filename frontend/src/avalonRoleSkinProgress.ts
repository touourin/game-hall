import { storedAccessToken } from './access'
import { storedAccountToken } from './account'
import {
  ROLE_SKINS,
  ROLE_SKIN_ROLES,
  isRoleSkinAvailable,
  roleSkinRoleCode,
  type RoleSkinId,
  type RoleSkinRoleCode,
} from './gameRoleSkins'

export interface AvalonRoleSkinRoleProgress {
  wins: number
  upgradeUnlocked: boolean
  ultimateUnlocked: boolean
}

export type AvalonRoleSkinProgressRoleCode = Exclude<
  RoleSkinRoleCode,
  'shadow_merlin'
>

export interface AvalonRoleSkinProgress {
  legacyAllUnlocked: boolean
  eventAllUnlocked: boolean
  eventEndsAt: string | null
  rankedOnly: boolean
  upgradeWinsRequired: number
  ultimateWinsRequired: number
  roles: Record<AvalonRoleSkinProgressRoleCode, AvalonRoleSkinRoleProgress>
}

export const AVALON_ROLE_SKIN_FREE_WEEK_START = '2026-08-02T16:00:00.000Z'
export const AVALON_ROLE_SKIN_FREE_WEEK_END = '2026-08-09T16:00:00.000Z'

export function isAvalonRoleSkinFreeWeek(now = new Date()): boolean {
  const timestamp = now.getTime()
  return timestamp >= Date.parse(AVALON_ROLE_SKIN_FREE_WEEK_START)
    && timestamp < Date.parse(AVALON_ROLE_SKIN_FREE_WEEK_END)
}

const ROLE_SKIN_PROGRESS_ROLE_CODES = ROLE_SKIN_ROLES
  .map((role) => role.code)
  .filter((role): role is AvalonRoleSkinProgressRoleCode => (
    role !== 'shadow_merlin'
  ))

export function emptyAvalonRoleSkinProgress(
  eventAllUnlocked = false,
): AvalonRoleSkinProgress {
  return {
    legacyAllUnlocked: false,
    eventAllUnlocked,
    eventEndsAt: eventAllUnlocked ? AVALON_ROLE_SKIN_FREE_WEEK_END : null,
    rankedOnly: true,
    upgradeWinsRequired: 2,
    ultimateWinsRequired: 5,
    roles: Object.fromEntries(
      ROLE_SKIN_PROGRESS_ROLE_CODES.map((role) => [
        role,
        { wins: 0, upgradeUnlocked: false, ultimateUnlocked: false },
      ]),
    ) as Record<AvalonRoleSkinProgressRoleCode, AvalonRoleSkinRoleProgress>,
  }
}

export function isRoleSkinUnlocked(
  progress: AvalonRoleSkinProgress,
  roleCode: string,
  skinId: RoleSkinId,
): boolean {
  const skin = ROLE_SKINS.find((item) => item.id === skinId)
  if (!skin || !isRoleSkinAvailable(roleCode, skinId)) return false
  if (skin.tier === '基础') return true
  if (progress.eventAllUnlocked) return true
  if (progress.legacyAllUnlocked) return true
  const family = roleSkinRoleCode(roleCode)
  if (!family) return false
  const progressFamily = family === 'shadow_merlin' ? 'merlin' : family
  const role = progress.roles[progressFamily]
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
