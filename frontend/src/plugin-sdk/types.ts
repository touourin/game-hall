export type PluginButtonVariant = 'primary' | 'secondary' | 'danger'
export type PluginButtonType = 'button' | 'submit' | 'reset'

export interface PluginButtonProps {
  variant?: PluginButtonVariant
  type?: PluginButtonType
  block?: boolean
  compact?: boolean
  disabled?: boolean
}

export interface PluginIconButtonProps {
  label: string
  type?: PluginButtonType
  compact?: boolean
  disabled?: boolean
}

export type PluginPlayingCardSize = (
  'table' | 'mini' | 'compact' | 'bottom' | 'hand'
)

export interface PluginPlayingCardProps {
  rank?: string
  suit?: string
  red?: boolean
  faceDown?: boolean
  empty?: boolean
  selected?: boolean
  wild?: boolean
  joker?: boolean
  interactive?: boolean
  disabled?: boolean
  size?: PluginPlayingCardSize
  ariaLabel?: string
}

export type PluginMetricTone = 'default' | 'success' | 'warning' | 'danger'

export interface PluginMetricItem {
  label: string
  value: string | number
  tone?: PluginMetricTone
}

export type PluginResultTone = 'success' | 'danger' | 'neutral'

export interface PluginResultCardProps {
  eyebrow: string
  title: string
  description?: string | null
  score?: string | number | null
  scoreUnit?: string
  metrics?: PluginMetricItem[]
  restartLabel?: string
  canRestart?: boolean
  busy?: boolean
  tone?: PluginResultTone
}

export interface PluginRevealArtworkFraming {
  scale: number
  originXPercent: number
  originYPercent: number
}

export interface PluginRevealCardProps {
  title: string
  subtitle?: string
  hint?: string
  artwork?: string | null
  artworkLabel?: string
  artworkFraming?: PluginRevealArtworkFraming
}
