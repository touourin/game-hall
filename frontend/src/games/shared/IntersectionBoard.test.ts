import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import IntersectionBoard from './IntersectionBoard.vue'

describe('IntersectionBoard', () => {
  it.each([9, 15, 19])(
    'draws a %i-line lattice only between the outer intersections',
    (size) => {
      const wrapper = mount(IntersectionBoard, {
        props: { size },
        slots: { default: '<button type="button">交叉点</button>' },
      })
      const lattice = wrapper.get('.intersection-board__lattice')
      const lines = lattice.findAll('line')
      const lastCoordinate = String(size - 0.5)

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
})
