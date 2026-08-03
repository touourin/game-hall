export type Alignment = 'good' | 'evil'
export type AvalonMode = 'standard' | 'court_undercurrent'

export type Phase =
  | 'lobby'
  | 'role_reveal'
  | 'team_building'
  | 'team_voting'
  | 'mission_voting'
  | 'round_result'
  | 'lady_select'
  | 'lady_reveal'
  | 'assassination'
  | 'dagger_grant'
  | 'final_council'
  | 'game_over'

export interface Knowledge {
  playerId: string
  playerName: string
  kind:
    | 'evil'
    | 'merlin_candidate'
    | 'evil_ally'
    | 'assassin'
    | 'dissenting_courtier'
  label: string
}

export interface PrivateRole {
  code: string
  label: string
  alignment: Alignment
  description: string
  knowledge: Knowledge[]
}

export interface PlayerView {
  id: string
  name: string
  avatarUrl?: string | null
  seat: number
  connected: boolean
  disconnectForfeitAt?: string | null
  disconnectForfeited?: boolean
  isBot: boolean
  isHost: boolean
  isLeader: boolean
  isSelected: boolean
  role?: string
  roleLabel?: string
  alignment?: Alignment
}

export interface MissionRecord {
  number: number
  teamIds: string[]
  success: boolean
  failCount: number
  failedByRejections: boolean
}

export interface ProposalRecord {
  missionNumber: number
  attempt: number
  leaderId: string
  teamIds: string[]
  votes: Array<{ playerId: string; approve: boolean }>
  accepted: boolean
}

export interface ChatMessage {
  id: string
  senderId: string
  senderName: string
  content: string
  createdAt: string
}

export interface LobbyRoom {
  roomCode: string
  hostName: string
  hostAvatarUrl?: string | null
  playerCount: number
  maxPlayers: number
  ladyEnabled: boolean
  mode: AvalonMode
  phase?: Phase
  cleanupAvailable?: boolean
  allHumansOffline?: boolean
}

export interface RoomActions {
  canStart: boolean
  canUpdateSettings: boolean
  canDissolve: boolean
  canLeave: boolean
  canConfirmRole: boolean
  canProposeTeam: boolean
  canVoteTeam: boolean
  canVoteMission: boolean
  canMissionFail: boolean
  canContinueRound: boolean
  canUseLady: boolean
  canAcknowledgeLady: boolean
  canAssassinate: boolean
  canGrantDagger: boolean
  canDissentingAssassinate: boolean
  canEarlyAssassinate: boolean
  canAddAiPlayer: boolean
  canRestart: boolean
}

export interface RoomSnapshot {
  [key: string]: unknown
  roomCode: string
  revision: number
  phase: Phase
  hostTransferAt?: string | null
  self: {
    id: string
    name: string
    avatarUrl?: string | null
    isHost: boolean
    role: PrivateRole | null
  }
  players: PlayerView[]
  settings: {
    mode: AvalonMode
    ladyEnabled: boolean
    ladyRecommended: boolean
    listed: boolean
    earlyAssassinationEnabled: boolean
    rolePreset: Array<{ code: string; label: string }>
  }
  game: {
    missionNumber: number
    requiredTeamSize: number | null
    failThreshold: number
    leaderId: string | null
    proposalAttempt: number
    selectedTeamIds: string[]
    teamVotesSubmitted: number
    myTeamVoteSubmitted: boolean
    lastTeamVotes: Array<{ playerId: string; approve: boolean }>
    missionVotesSubmitted: number
    myMissionVoteSubmitted: boolean
    roleConfirmedCount: number
    missionHistory: MissionRecord[]
    proposalHistory: ProposalRecord[]
    successCount: number
    failCount: number
  }
  lady: {
    enabled: boolean
    holderId: string | null
    usedByIds: string[]
    eligibleTargetIds: string[]
    pendingInspectorId: string | null
    pendingTargetId: string | null
    history: Array<{
      inspectorId: string
      inspectorName: string
      targetId: string
      targetName: string
      missionNumber: number
    }>
    myChecks: Array<{
      targetId: string
      targetName: string
      alignment: Alignment
      missionNumber: number
    }>
    currentResult: {
      targetId: string
      targetName: string
      alignment: Alignment
    } | null
  }
  result: {
    winner: Alignment | null
    reason: string | null
    endingRoute: string | null
    assassinTargetId: string | null
    assassinationWasEarly: boolean
    eligibleTargetIds: string[]
  }
  courtUndercurrent: {
    enabled: boolean
    daggerCandidateIds: string[]
    daggerTargetId: string | null
    daggerHit: boolean | null
    transformedPlayerId: string | null
    eligibleTargetIds: string[]
    assassinationTargetId: string | null
  }
  chat: {
    maxLength: number
    messages: ChatMessage[]
  }
  actions: RoomActions
}
