import { storedAccessToken } from './access'
import { storedAccountToken } from './account'

export interface StatsSummary {
  games: number
  wins: number
  draws: number
  losses: number
  winRate: number
  goodGames: number
  goodWins: number
  evilGames: number
  evilWins: number
  bestMs: number | null
  averageMs: number | null
}

export type MatchOutcome = 'win' | 'loss' | 'draw' | 'completed'

export interface MatchHistoryItem {
  id: string
  gameKey: string
  gameName: string
  roomCode: string
  playerCount: number
  winner: string
  reason: string
  ranked: boolean
  assassinationHit: boolean | null
  endedAt: string
  playerName: string
  role: string
  alignment: string
  won: boolean
  outcome: MatchOutcome
  scoreMs: number | null
  gameMode?: string | null
}

export interface MatchDetail {
  id: string
  gameKey: string
  gameName: string
  roomCode: string
  playerCount: number
  winner: string
  reason: string
  ranked: boolean
  assassinationHit: boolean | null
  startedAt: string
  endedAt: string
  details: {
    options?: Record<string, unknown>
    players: Array<{
      id: string
      name: string
      seat: number
      isBot?: boolean
      role?: string
      alignment?: string
    }>
    missions?: Array<{
      number: number
      teamIds: string[]
      success: boolean
      failCount: number
    }>
    proposals?: Array<{
      missionNumber: number
      attempt: number
      leaderId: string
      teamIds: string[]
      votes: Record<string, boolean>
      accepted: boolean
    }>
    ladyChecks?: Array<{
      inspectorId: string
      targetId: string
      alignment: 'good' | 'evil'
      missionNumber: number
    }>
    assassinTargetId?: string | null
    assassinationWasEarly?: boolean
    state?: Record<string, unknown> & {
      results_ms?: number[]
      disc_count?: number
      moves?: number
      elapsed_ms?: number
      mistakes?: number
      difficulty?: string
      rows?: number
      columns?: number
      mine_count?: number
      revealed_count?: number
      flagged_count?: number
      result?: string
    }
  }
}

export interface LeaderboardEntry {
  rank: number
  accountId: string
  playerName: string
  avatarUrl?: string
  games: number
  wins: number
  draws: number
  winRate: number
  bestMs?: number
  averageMs?: number
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
        'X-Game-Hall-Access': accessToken,
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

export async function loadPersonalStats(gameKey?: string, gameMode?: string): Promise<{
  summary: StatsSummary
  history: MatchHistoryItem[]
}> {
  const response = await statsRequest<{
    ok: boolean
    summary: StatsSummary
    history: MatchHistoryItem[]
  }>(`/api/stats/me${gameKey ? `?${new URLSearchParams({
    game: gameKey,
    ...(gameMode ? { mode: gameMode } : {}),
  }).toString()}` : ''}`)
  return { summary: response.summary, history: response.history }
}

export async function loadMatchDetail(matchId: string): Promise<MatchDetail> {
  const response = await statsRequest<{ ok: boolean; match: MatchDetail }>(
    `/api/matches/${encodeURIComponent(matchId)}`,
  )
  return response.match
}

export async function loadLeaderboard(gameKey: string, gameMode?: string): Promise<LeaderboardEntry[]> {
  const response = await statsRequest<{
    ok: boolean
    players: LeaderboardEntry[]
  }>(`/api/leaderboard?${new URLSearchParams({
    game: gameKey,
    ...(gameMode ? { mode: gameMode } : {}),
  }).toString()}`)
  return response.players
}
