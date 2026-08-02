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
  preserveFrame?: boolean
  treatment?: 'codex-ink-wash'
}

export interface ArtworkSkinPreviewItem {
  id: string
  name: string
  group: string
  artwork: string
  framing: RevealArtworkFraming
}

export interface ArtworkSkinOption {
  id: string
  name: string
  description: string
  tier: string
  preview: string
  items: ArtworkSkinPreviewItem[]
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
