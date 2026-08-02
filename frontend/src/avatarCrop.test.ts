import {
  clampSquareCrop,
  initialSquareCrop,
  moveSquareCrop,
  resizeSquareCrop,
} from './avatarCrop'

describe('avatar crop helpers', () => {
  it('centers a square crop inside landscape and portrait images', () => {
    expect(initialSquareCrop(1200, 800, 0.5)).toEqual({
      x: 400,
      y: 200,
      size: 400,
    })
    expect(initialSquareCrop(600, 1000, 1)).toEqual({
      x: 0,
      y: 200,
      size: 600,
    })
  })

  it('keeps dragged crops inside the image', () => {
    const crop = { x: 100, y: 80, size: 300 }

    expect(moveSquareCrop(crop, -500, 900, 800, 600)).toEqual({
      x: 0,
      y: 300,
      size: 300,
    })
  })

  it('resizes around the current center and clamps at image edges', () => {
    expect(resizeSquareCrop(
      { x: 300, y: 200, size: 200 },
      400,
      900,
      700,
    )).toEqual({ x: 200, y: 100, size: 400 })

    expect(clampSquareCrop(
      { x: 700, y: -20, size: 500 },
      800,
      600,
    )).toEqual({ x: 300, y: 0, size: 500 })
  })
})
