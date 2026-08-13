import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const distAssets = join(process.cwd(), 'dist', 'assets')
const css = readdirSync(distAssets)
  .filter((file) => file.endsWith('.css'))
  .map((file) => readFileSync(join(distAssets, file), 'utf8'))
  .join('\n')

const unsafeRootThemeRules = [...css.matchAll(
  /(^|\})([^{}]*:root\[data-theme=[^\]]+\][^{}]*)\{/g,
)]
  .map(([, , selector]) => selector.trim())
  .filter((selector) => (
    selector.includes(',')
    && selector
      .split(',')
      .some((part) => /:root\[data-theme=[^\]]+\]\s*$/.test(part.trim()))
  ))

if (unsafeRootThemeRules?.length) {
  throw new Error(
    `检测到主题样式直接作用于根节点：${[...new Set(unsafeRootThemeRules)].join(' | ')}`,
  )
}

console.log('主题选择器检查通过')
