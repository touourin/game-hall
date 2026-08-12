export interface OneNightRole {
  code: string
  label: string
  alignment: 'village' | 'werewolf' | 'tanner'
  description: string
}

export interface OneNightResolutionPlayer {
  playerId: string
  initialRole: OneNightRole
  finalRole: OneNightRole
  votedForId: string | null
  voteCount: number
  eliminated: boolean
  won: boolean
}

export interface OneNightWerewolfView {
  roleDeck: OneNightRole[]
  roleGuide: OneNightRole[]
  presetLabel: string
  self: {
    initialRole: OneNightRole | null
    finalRole?: OneNightRole | null
    nightResults: Array<{ kind: string; text: string }>
  }
  roleConfirmedCount?: number
  night: {
    isMyTurn: boolean
    prompt: string | null
  }
  votesSubmitted: number
  hasVoted: boolean
  resolution: {
    players: OneNightResolutionPlayer[]
    centerRoles: OneNightRole[]
  } | null
  legal: {
    canConfirmRole?: boolean
    canSubmitNightAction?: boolean
    nightRole?: string | null
    targetPlayerIds?: string[]
    centerSelectionCount?: number
    canStartVote?: boolean
    voteTargetPlayerIds?: string[]
  }
}
