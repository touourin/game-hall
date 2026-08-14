import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import IntersectionBoard from './IntersectionBoard.vue'
import componentSource from './IntersectionBoard.vue?raw'

describe('IntersectionBoard', () => {
  it.each([9, 15, 19])(
    'draws a %i-line lattice inside one coordinate stage',
    (size) => {
      const wrapper = mount(IntersectionBoard, {
        props: { size },
        slots: { default: '<button type="button">交叉点</button>' },
      })
      const stage = wrapper.get('.intersection-board__stage')
      const lattice = wrapper.get('.intersection-board__lattice')
      const lines = lattice.findAll('line')
      const lastCoordinate = String(size - 0.5)

      expect(wrapper.element.children).toHaveLength(1)
      expect(stage.element.contains(lattice.element)).toBe(true)
      expect(lattice.attributes('viewBox')).toBe(`0 0 ${size} ${size}`)
      expect(lines).toHaveLength(size * 2)
      expect(lines[0]?.attributes()).toMatchObject({
        x1: '0.5',
        x2: lastCoordinate,
        y1: '0.5',
        y2: '0.5',
      })
      expect(lines.at(-1)?.attributes()).toMatchObject({
        x1: lastCoordinate,
        x2: lastCoordinate,
        y1: '0.5',
        y2: lastCoordinate,
      })
    },
  )

  it('defines both axes explicitly and neutralizes native button sizing', () => {
    const stageRule = componentSource.match(
      /\.intersection-board__stage\s*\{[\s\S]*?\n\}/,
    )?.[0]
    const buttonRule = componentSource.match(
      /:slotted\(button\)\s*\{[\s\S]*?\n\}/,
    )?.[0]

    expect(stageRule).toContain('aspect-ratio: 1')
    expect(stageRule).toContain(
      'grid-template-columns: repeat(var(--board-size), minmax(0, 1fr))',
    )
    expect(stageRule).toContain(
      'grid-template-rows: repeat(var(--board-size), minmax(0, 1fr))',
    )
    expect(buttonRule).toContain('min-width: 0')
    expect(buttonRule).toContain('min-height: 0')
    expect(buttonRule).toContain('-webkit-appearance: none')
    expect(buttonRule).toContain('touch-action: manipulation')
  })
})
