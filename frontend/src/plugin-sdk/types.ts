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

export type PluginModalSize = 'small' | 'medium' | 'large'

export interface PluginModalProps {
  title?: string
  description?: string
  ariaLabel?: string
  size?: PluginModalSize
  closeOnBackdrop?: boolean
  closeLabel?: string
  mobileSheet?: boolean
  inline?: boolean
}

export interface PluginConfirmDialogProps {
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  closeLabel?: string
  size?: PluginModalSize
  busy?: boolean
  tone?: 'default' | 'danger'
  mobileSheet?: boolean
  inline?: boolean
}

export interface PluginMetricGridProps {
  items: PluginMetricItem[]
  columns?: 1 | 2 | 3 | 4
  ariaLabel?: string
  valueFirst?: boolean
}

export interface PluginRuleGuideContent {
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

export interface PluginRuleGuideProps {
  content: PluginRuleGuideContent
}

export type PluginTextFieldType = 'text' | 'search' | 'email' | 'url' | 'tel' | 'password'
export type PluginTextInputMode = 'text' | 'search' | 'email' | 'url' | 'tel' | 'numeric' | 'decimal'

export interface PluginTextFieldProps {
  modelValue: string
  label: string
  id?: string
  name?: string
  type?: PluginTextFieldType
  inputmode?: PluginTextInputMode
  autocomplete?: string
  placeholder?: string
  description?: string
  error?: string
  maxlength?: number
  disabled?: boolean
  required?: boolean
}

export interface PluginNumberFieldProps {
  modelValue: number | null
  label: string
  id?: string
  name?: string
  min?: number
  max?: number
  step?: number | 'any'
  inputmode?: 'numeric' | 'decimal'
  placeholder?: string
  description?: string
  error?: string
  disabled?: boolean
  required?: boolean
}

export interface PluginSelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface PluginSelectProps {
  modelValue: string
  label: string
  options: PluginSelectOption[]
  id?: string
  name?: string
  placeholder?: string
  description?: string
  error?: string
  disabled?: boolean
  required?: boolean
}

export type PluginStateTone = 'info' | 'loading' | 'empty' | 'error'

export interface PluginStatePanelProps {
  title: string
  description?: string
  tone?: PluginStateTone
  actionLabel?: string
  busy?: boolean
}

export interface PluginFeedbackStateProps {
  title?: string
  description?: string
  actionLabel?: string
  busy?: boolean
}

export interface PluginDurationFormatOptions {
  style?: 'timer' | 'readable'
  fractionDigits?: 0 | 1 | 2
  empty?: string
}

export interface PluginScoreFormatOptions {
  unit?: string
  empty?: string
  minimumFractionDigits?: number
  maximumFractionDigits?: number
}

export type PluginThemeName = 'emerald' | 'midnight' | 'royal' | 'amber'

type PluginMaterialGroup<T extends string> = Readonly<Record<T, string>>

export interface PluginThemeMaterials {
  readonly scene: PluginMaterialGroup<'top' | 'center' | 'bottom' | 'glow' | 'grid' | 'fog' | 'particle'>
  readonly stage: PluginMaterialGroup<'top' | 'bottom' | 'edge' | 'innerEdge' | 'detail' | 'glow' | 'shadow'>
  readonly metal: PluginMaterialGroup<'body' | 'side' | 'edge' | 'glass' | 'core' | 'glow'>
  readonly copy: PluginMaterialGroup<'primary' | 'secondary' | 'onStage' | 'onStageOutline'>
  readonly semantic: PluginMaterialGroup<
    'danger' | 'dangerStrong' | 'dangerGlow'
    | 'warning' | 'warningStrong' | 'warningGlow'
    | 'success' | 'successStrong' | 'successGlow'
  >
}
