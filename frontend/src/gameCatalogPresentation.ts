const CATALOG_TONE_COLORS: Readonly<Record<string, string>> = Object.freeze({
  red: '#b36f69',
  chess: '#9b8b72',
  jade: '#6f9b88',
  blue: '#748faa',
  ink: '#88969c',
  army: '#8f9872',
  pulse: '#66a499',
  focus: '#738fa3',
  barrage: '#c96678',
  mine: '#a77689',
  tower: '#8d7da3',
  blocks: '#7299a1',
  poker: '#aa7074',
  fortune: '#a58a61',
  suspicion: '#9d7961',
  moon: '#7f89a5',
})

const DEFAULT_CATALOG_TONE = '#a58a61'

export function gameCatalogToneColor(tone: string): string {
  return CATALOG_TONE_COLORS[tone] ?? DEFAULT_CATALOG_TONE
}
