export interface SquareCrop {
  x: number
  y: number
  size: number
}

const MIN_CROP_EDGE = 1

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(Math.max(value, minimum), maximum)
}

export function initialSquareCrop(
  imageWidth: number,
  imageHeight: number,
  ratio = 0.82,
): SquareCrop {
  const maximumSize = Math.max(
    MIN_CROP_EDGE,
    Math.min(imageWidth, imageHeight),
  )
  const size = clamp(maximumSize * ratio, MIN_CROP_EDGE, maximumSize)
  return {
    x: (imageWidth - size) / 2,
    y: (imageHeight - size) / 2,
    size,
  }
}

export function clampSquareCrop(
  crop: SquareCrop,
  imageWidth: number,
  imageHeight: number,
): SquareCrop {
  const maximumSize = Math.max(
    MIN_CROP_EDGE,
    Math.min(imageWidth, imageHeight),
  )
  const size = clamp(crop.size, MIN_CROP_EDGE, maximumSize)
  return {
    x: clamp(crop.x, 0, Math.max(0, imageWidth - size)),
    y: clamp(crop.y, 0, Math.max(0, imageHeight - size)),
    size,
  }
}

export function moveSquareCrop(
  crop: SquareCrop,
  deltaX: number,
  deltaY: number,
  imageWidth: number,
  imageHeight: number,
): SquareCrop {
  return clampSquareCrop(
    { ...crop, x: crop.x + deltaX, y: crop.y + deltaY },
    imageWidth,
    imageHeight,
  )
}

export function resizeSquareCrop(
  crop: SquareCrop,
  nextSize: number,
  imageWidth: number,
  imageHeight: number,
): SquareCrop {
  const centerX = crop.x + crop.size / 2
  const centerY = crop.y + crop.size / 2
  return clampSquareCrop(
    {
      x: centerX - nextSize / 2,
      y: centerY - nextSize / 2,
      size: nextSize,
    },
    imageWidth,
    imageHeight,
  )
}
