import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const css = readFileSync(join(process.cwd(), 'src', 'styles.css'), 'utf8')
const themeDefinitions = [
  { id: 'emerald', name: '极光雾舱', colorScheme: 'dark' },
  { id: 'midnight', name: '曜石黑钛', colorScheme: 'dark' },
  { id: 'royal', name: '月白陶瓷', colorScheme: 'light' },
  { id: 'amber', name: '橙釉象牙', colorScheme: 'light' },
]

function parseHexVariables(block, label) {
  if (!block) throw new Error(`未找到${label}主题变量`)
  return Object.fromEntries(
    [...block.matchAll(/--([\w-]+):\s*(#[\da-f]{6})/gi)]
      .map(([, name, value]) => [name, value]),
  )
}

const baseVariables = parseHexVariables(
  css.match(/^:root\s*\{([^}]+)\}/)?.[1],
  '默认',
)

function luminance(hex) {
  const channels = [1, 3, 5]
    .map((offset) => Number.parseInt(hex.slice(offset, offset + 2), 16) / 255)
    .map((channel) => (
      channel <= 0.04045
        ? channel / 12.92
        : ((channel + 0.055) / 1.055) ** 2.4
    ))
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
}

function contrast(foreground, background) {
  const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a)
  return (values[0] + 0.05) / (values[1] + 0.05)
}

const commonChecks = [
  ['强调色文字', 'accent-contrast', 'accent'],
  ['主操作按钮起点', 'primary-text', 'primary-start'],
  ['主操作按钮终点', 'primary-text', 'primary-end'],
  ['正文', 'text', 'surface-strong'],
  ['辅助文字', 'muted', 'surface-strong'],
  ['页面辅助文字', 'muted', 'bg'],
]

const failures = themeDefinitions.flatMap((theme) => {
  const themeBlock = theme.id === 'emerald'
    ? ''
    : css.match(new RegExp(`:root\\[data-theme="${theme.id}"\\]\\s*\\{([^}]+)\\}`))?.[1]
  const variables = {
    ...baseVariables,
    ...(theme.id === 'emerald' ? {} : parseHexVariables(themeBlock, theme.name)),
  }
  const checks = theme.colorScheme === 'light'
    ? [...commonChecks, ['禁用按钮', 'disabled-text', 'disabled-bg-end']]
    : commonChecks

  return checks.flatMap(([label, foregroundName, backgroundName]) => {
    const foreground = variables[foregroundName]
    const background = variables[backgroundName]
    if (!foreground || !background) {
      return [`${theme.name}的${label}缺少颜色变量`]
    }
    const ratio = contrast(foreground, background)
    return ratio < 4.5
      ? [`${theme.name}的${label}对比度 ${ratio.toFixed(2)}:1 低于 4.5:1`]
      : []
  })
})

if (failures.length) throw new Error(failures.join('；'))

console.log('四套大厅主题对比度检查通过')
