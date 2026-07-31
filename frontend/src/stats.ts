import { storedAccessToken } from './access'
import { storedAccountToken } from './account'

export interface StatsSummary {
  games: number
  wins: number
  winRate: number
  goodGames: number
  goodWins: number
  evilGames: number
  evilWins: number
}

export interface MatchHistoryItem {
  id: string
  roomCode: string
  playerCount: number
  winner: 'good' | 'evil'
  reason: string
  ranked: boolean
  assassinationHit: boolean | null
  endedAt: string
  displayName: string
  role: string
  alignment: 'good' | 'evil'
  won: boolean
}

export interface MatchDetail {
  id: string
  roomCode: string
  playerCount: number
  winner: 'good' | 'evil'
  reason: string
  ranked: boolean
  assassinationHit: boolean | null
  startedAt: string
  endedAt: string
  details: {
    players: Array<{
      id: string
      name: string
      seat: number
      isBot: boolean
      role: string
      alignment: 'good' | 'evil'
    }>
    missions: Array<{
      number: number
      teamIds: string[]
      success: boolean
      failCount: number
    }>
    proposals: Array<{
      missionNumber: number
      attempt: number
      leaderId: string
      teamIds: string[]
      votes: Record<string, boolean>
      accepted: boolean
    }>
    ladyChecks: Array<{
      inspectorId: string
      targetId: string
      alignment: 'good' | 'evil'
      missionNumber: number
    }>
    assassinTargetId: string | null
    assassinationWasEarly: boolean
  }
}

export interface LeaderboardEntry {
  rank: number
  accountId: string
  displayName: string
  games: number
  wins: number
  winRate: number
}

async function statsRequest<T>(path: string): Promise<T> {
  const accessToken = storedAccessToken()
  const accountToken = storedAccountToken()
  if (!accessToken || !accountToken) {
    throw new Error('登录状态已失效，请重新登录')
  }
  let response: Response
  try {
    response = await fetch(path, {
      headers: {
        'X-Avalon-Access': accessToken,
        Authorization: `Bearer ${accountToken}`,
      },
    })
  } catch {
    throw new Error('无法连接服务器，请检查网络')
  }
  if (!response.ok) {
    try {
      const body = (await response.json()) as { detail?: string }
      throw new Error(body.detail ?? '读取数据失败')
    } catch (error) {
      if (error instanceof Error && error.message !== '读取数据失败') {
        throw error
      }
      throw new Error('读取数据失败')
    }
  }
  return (await response.json()) as T
}

export async function loadPersonalStats(): Promise<{
  summary: StatsSummary
  history: MatchHistoryItem[]
}> {
  const response = await statsRequest<{
    ok: boolean
    summary: StatsSummary
    history: MatchHistoryItem[]
  }>('/api/stats/me')
  return { summary: response.summary, history: response.history }
}

export async function loadMatchDetail(matchId: string): Promise<MatchDetail> {
  const response = await statsRequest<{ ok: boolean; match: MatchDetail }>(
    `/api/matches/${encodeURIComponent(matchId)}`,
  )
  return response.match
}

export async function loadLeaderboard(): Promise<LeaderboardEntry[]> {
  const response = await statsRequest<{
    ok: boolean
    players: LeaderboardEntry[]
  }>('/api/leaderboard')
  return response.players
}
