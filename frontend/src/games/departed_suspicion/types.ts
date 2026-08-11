export type IntegrityKind = 'honest' | 'crooked' | 'agent' | 'kingpin'
export type IntegrityKnowledge = 'own' | 'public' | 'known' | 'hidden'

export interface IntegrityView {
  index: number
  knowledgeKey: string | null
  kind: IntegrityKind | null
  label: string
  revealed: boolean
  knowledge: IntegrityKnowledge
  wounded: boolean
}

export interface EffectView {
  id: string
  name: string
  grenadeStage?: number | null
}

export interface PlayerBoardView {
  playerId: string
  seat: number
  alive: boolean
  gun: boolean
  aimPlayerId: string | null
  equipmentCount: number
  effects: EffectView[]
  restrictedToEquip: boolean
  cards: IntegrityView[]
  team: 'honest' | 'crooked' | null
}

export interface EquipmentView {
  id: string
  number: number
  name: string
  englishName: string
  expansion: string
  timing: string
  description: string
  persistent: boolean
  requiresCover: boolean
  available?: boolean
}

export interface EquipmentSelectOption {
  value: number
  label: string
}

export interface EquipmentFieldView {
  key: string
  label: string
  kind: 'player' | 'card' | 'boolean'
  required: boolean
  default?: boolean | number | null
  options?: EquipmentSelectOption[]
  dependsOn?: string
  optionsByValue?: Record<string, EquipmentSelectOption[]>
  distinctFrom?: string
  visibleWhen?: { field: string; equals: boolean | number | string }
  distinctLocationFrom?: {
    seatField: string
    cardField: string
    ownSeatField: string
  }
}

export interface EquipmentPlayOptionView {
  cardId: string
  fields: EquipmentFieldView[]
}

export interface SuspicionGameView {
  turnPlayerId: string | null
  turnNumber: number
  direction: 'clockwise' | 'counterclockwise'
  centralGuns: number
  actionDone: boolean
  extraInvestigationDone: boolean
  players: PlayerBoardView[]
  selfTeam: 'honest' | 'crooked' | null
  equipmentHand: EquipmentView[]
  equipmentCatalog: EquipmentView[]
  pendingAction: null | {
    actorPlayerId: string
    action: string
    actionLabel: string
    targetPlayerId: string | null
    targetCardIndex: number | null
    responsePlayerId: string | null
    isMyResponse: boolean
  }
  pendingShot: null | {
    targetPlayerId: string
    source: string
    scannerPlayerId: string | null
    isMyDecision: boolean
  }
  choice: null | {
    kind: string
    isMyDecision: boolean
    cards?: EquipmentView[]
    shooterPlayerId?: string
    targetPlayerIds?: string[]
  }
  postShot: null | { kind: string; isMyDecision: boolean; targetPlayerIds: string[] }
  waiting: null | { kind: string; playerId: string }
  currentPrompt: null | {
    kind: string
    title: string
    detail: string
    decisionPlayerId: string | null
    isMyDecision: boolean
    actorPlayerId: string | null
    targetPlayerId: string | null
    targetCardIndex: number | null
    sourceCardId: string | null
  }
  legal: {
    canTakeNormalAction: boolean
    normalActionIds: Array<'investigate' | 'equip' | 'arm' | 'shoot'>
    canPassNormalAction: boolean
    investigationTargetPlayerIds: string[]
    canTakeExtraInvestigation: boolean
    canEndTurn: boolean
    canRespond: boolean
    responseEquipmentIds: string[]
    playableEquipmentIds: string[]
    equipmentOptions: EquipmentPlayOptionView[]
  }
  history: Array<{ event: string; text: string }>
  rulesNotice: string
}
