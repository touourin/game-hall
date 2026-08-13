import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const css = readFileSync(join(process.cwd(), 'src', 'styles.css'), 'utf8')
const lightTheme = css.match(/:root\[data-theme="royal"\]\s*\{([^}]+)\}/)?.[1]

if (!lightTheme) throw new Error('未找到月白陶瓷主题变量')

const variables = Object.fromEntries(
  [...lightTheme.matchAll(/--([\w-]+):\s*(#[\da-f]{6})/gi)]
    .map(([, name, value]) => [name, value]),
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

const checks = [
  ['主操作按钮', 'accent-contrast', 'gold'],
  ['禁用按钮', 'disabled-text', 'disabled-bg-end'],
  ['正文', 'text', 'surface-strong'],
  ['辅助文字', 'muted', 'surface-strong'],
  ['页面辅助文字', 'muted', 'bg'],
]

const failures = checks.flatMap(([label, foregroundName, backgroundName]) => {
  const foreground = variables[foregroundName]
  const background = variables[backgroundName]
  if (!foreground || !background) return [`${label}缺少颜色变量`]
  const ratio = contrast(foreground, background)
  return ratio < 4.5 ? [`${label}对比度 ${ratio.toFixed(2)}:1 低于 4.5:1`] : []
})

if (failures.length) throw new Error(failures.join('；'))

console.log('月白陶瓷对比度检查通过')
