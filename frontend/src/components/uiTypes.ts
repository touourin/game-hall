export interface MissionProgressItem {
  number: number
  requirement: number
  status: 'pending' | 'current' | 'success' | 'failed'
  note?: string
  replayable?: boolean
  label: string
}

export interface RevealArtworkFraming {
  scale: number
  originXPercent: number
  originYPercent: number
}

export interface RoleSkinChoiceOption {
  id: string
  name: string
  description: string
  tier: string
  artwork: string
  framing: RevealArtworkFraming
  unlocked: boolean
  remainingWins: number
}

export interface RoleSkinLoadoutRoleOption {
  code: string
  name: string
  group: string
  wins: number
  currentSkinName: string
  currentArtwork: string
  currentFraming: RevealArtworkFraming
  legacyAllUnlocked: boolean
  eventAllUnlocked: boolean
  upgradeWinsRequired: number
  ultimateWinsRequired: number
  choices: RoleSkinChoiceOption[]
}

export interface ModeGuideContent {
  ariaLabel: string
  eyebrow: string
  title: string
  story: string
  quickStart: {
    label: string
    title: string
    description: string
    steps: Array<{ title: string; text: string }>
  }
  feature: {
    label: string
    title: string
    description: string
    details: Array<{ label: string; text: string }>
  }
  flowTitle: string
  steps: Array<{ title: string; text: string }>
  ruleSections: Array<{
    title: string
    description?: string
    bullets?: Array<{ label?: string; text: string }>
    table?: {
      headers: string[]
      rows: string[][]
    }
  }>
  background: {
    label: string
    title: string
    paragraphs: string[]
  }
  footer: string
}

export interface GameMetricItem {
  label: string
  value: string | number
  tone?: 'default' | 'success' | 'warning' | 'danger'
}
