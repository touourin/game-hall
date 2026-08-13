export function formatRecordDuration(milliseconds: number | null | undefined): string {
  if (milliseconds === null || milliseconds === undefined) return '—'
  const seconds = Math.floor(milliseconds / 1000)
  const tenths = Math.floor(milliseconds % 1000 / 100)
  return `${seconds}.${tenths} 秒`
}

export function difficultyRecordLabel(value: string | undefined): string {
  if (value === 'expert') return '高级'
  if (value === 'intermediate') return '中级'
  if (value === 'beginner') return '初级'
  return ''
}

export function tetrisRecordModeLabel(value: string | undefined): string {
  if (value?.startsWith('timed_')) {
    return `${Number(value.slice(6)) / 60} 分钟限时`
  }
  return '无限挑战'
}
