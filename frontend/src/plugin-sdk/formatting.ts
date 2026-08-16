import type { PluginDurationFormatOptions, PluginScoreFormatOptions } from './types'

const SECOND_MS = 1_000

function normalizeFractionDigits(value: number, fallback: number): number {
  return Number.isFinite(value)
    ? Math.min(20, Math.max(0, Math.trunc(value)))
    : fallback
}

export function formatPluginDuration(
  milliseconds: number | null | undefined,
  options: PluginDurationFormatOptions = {},
): string {
  const {
    style = 'timer',
    fractionDigits = 1,
    empty = '—',
  } = options

  if (milliseconds == null || !Number.isFinite(milliseconds)) return empty

  const precision = 10 ** fractionDigits
  const safeMilliseconds = Math.max(0, milliseconds)
  const totalUnits = Math.floor(safeMilliseconds * precision / SECOND_MS)
  const minutes = Math.floor(totalUnits / (60 * precision))
  const secondUnits = totalUnits - minutes * 60 * precision
  const seconds = Math.floor(secondUnits / precision)
  const fraction = secondUnits % precision
  const decimal = fractionDigits > 0
    ? `.${String(fraction).padStart(fractionDigits, '0')}`
    : ''

  if (style === 'readable') {
    return minutes > 0
      ? `${minutes} 分 ${String(seconds).padStart(2, '0')}${decimal} 秒`
      : `${seconds}${decimal} 秒`
  }

  return minutes > 0
    ? `${minutes}:${String(seconds).padStart(2, '0')}${decimal}`
    : `${seconds}${decimal} 秒`
}

export function formatPluginScore(
  value: string | number | null | undefined,
  options: PluginScoreFormatOptions = {},
): string {
  const {
    unit = '',
    empty = '—',
    minimumFractionDigits = 0,
    maximumFractionDigits = 2,
  } = options

  if (value == null || value === '' || (typeof value === 'number' && !Number.isFinite(value))) {
    return empty
  }

  const safeMinimumFractionDigits = normalizeFractionDigits(minimumFractionDigits, 0)
  const safeMaximumFractionDigits = Math.max(
    safeMinimumFractionDigits,
    normalizeFractionDigits(maximumFractionDigits, 2),
  )
  const formatted = typeof value === 'number'
    ? new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: safeMinimumFractionDigits,
        maximumFractionDigits: safeMaximumFractionDigits,
      }).format(value)
    : value

  return unit ? `${formatted} ${unit}` : formatted
}
