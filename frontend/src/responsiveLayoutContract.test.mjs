import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const globalStyles = readFileSync(resolve(process.cwd(), 'src/styles.css'), 'utf8')

describe('responsive layout contract', () => {
  it('defines reusable container, action-stack, and dialog primitives', () => {
    expect(globalStyles).toContain('.adaptive-layout-root')
    expect(globalStyles).toContain('container-type: inline-size')
    expect(globalStyles).toContain('.adaptive-action-stack')
    expect(globalStyles).toContain('gap: var(--adaptive-action-gap, var(--layout-section-gap))')
    expect(globalStyles).toContain('.adaptive-action-push')
    expect(globalStyles).toContain('margin-block-start: auto')
    expect(globalStyles).toContain('.adaptive-dialog')
    expect(globalStyles).toContain('.adaptive-scroll-region')
    expect(globalStyles).toContain('.adaptive-touch-target')
  })

  it('keeps narrow viewports fluid and gives shared modals one scroll owner', () => {
    const bodyRule = globalStyles.match(/body\s*\{[^}]+\}/)?.[0] ?? ''
    const backdropRule = globalStyles.match(/\.modal-backdrop\s*\{[^}]+\}/)?.[0] ?? ''
    const cardRule = globalStyles.match(/\.modal-card\s*\{[^}]+\}/)?.[0] ?? ''

    expect(bodyRule).toContain('min-width: 0')
    expect(bodyRule).not.toMatch(/min-width:\s*\d+px/)
    expect(backdropRule).toContain('overflow-y: auto')
    expect(backdropRule).toContain('overscroll-behavior: contain')
    expect(cardRule).toContain('max-height: calc(100dvh')
    expect(cardRule).toContain('overflow-x: hidden')
    expect(cardRule).toContain('overflow-y: auto')
  })
})
