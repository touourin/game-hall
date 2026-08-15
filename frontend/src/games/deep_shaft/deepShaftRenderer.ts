import type { ThemeName } from '../../theme'
import {
  CEILING_DEPTH,
  CRUMBLE_DELAY_TICKS,
  PLATFORM_GAP,
  TARGET_FLOOR,
  VIEW_HEIGHT,
  WORLD_WIDTH,
  type ShaftPlatform,
  type ShaftState,
} from './deepShaftEngine'
import { deepShaftPalette, type DeepShaftPalette, type ShaftMaterial } from './deepShaftPalettes'

export interface DeepShaftRenderFrame {
  state: ShaftState
  platforms: ShaftPlatform[]
  theme: ThemeName
  reducedMotion?: boolean
}

interface RenderMetrics {
  width: number
  height: number
  scaleX: number
  scaleY: number
  unit: number
}

function roundedRect(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  context.beginPath()
  context.roundRect(x, y, width, height, Math.min(radius, width / 2, height / 2))
}

function drawShaftBackground(
  context: CanvasRenderingContext2D,
  metrics: RenderMetrics,
  state: ShaftState,
  palette: DeepShaftPalette,
  reducedMotion: boolean,
) {
  const { width, height, unit } = metrics
  const background = context.createLinearGradient(0, 0, 0, height)
  background.addColorStop(0, palette.backgroundTop)
  background.addColorStop(.48, palette.backgroundCenter)
  background.addColorStop(1, palette.backgroundBottom)
  context.fillStyle = background
  context.fillRect(0, 0, width, height)

  const centerLight = context.createRadialGradient(
    width * .5,
    height * .34,
    0,
    width * .5,
    height * .34,
    width * .58,
  )
  centerLight.addColorStop(0, palette.fog)
  centerLight.addColorStop(1, 'rgba(0,0,0,0)')
  context.fillStyle = centerLight
  context.fillRect(0, 0, width, height)

  const wallWidth = width * .105
  const drawWall = (x: number, direction: 1 | -1) => {
    const wallGradient = context.createLinearGradient(
      x,
      0,
      x + wallWidth * direction,
      0,
    )
    wallGradient.addColorStop(0, palette.wall)
    wallGradient.addColorStop(1, 'rgba(0,0,0,0)')
    context.fillStyle = wallGradient
    context.fillRect(direction > 0 ? x : x - wallWidth, 0, wallWidth, height)
    context.strokeStyle = palette.wallEdge
    context.lineWidth = Math.max(1, unit)
    context.beginPath()
    context.moveTo(x, 0)
    context.lineTo(x, height)
    context.stroke()
  }
  drawWall(0, 1)
  drawWall(width, -1)

  context.strokeStyle = palette.grid
  context.lineWidth = Math.max(1, unit * .55)
  const columnWidth = width / 10
  for (let x = columnWidth; x < width; x += columnWidth) {
    context.beginPath()
    context.moveTo(x, 0)
    context.lineTo(x, height)
    context.stroke()
  }

  const sectionHeight = PLATFORM_GAP * metrics.scaleY
  let sectionY = -((state.cameraY % PLATFORM_GAP) * metrics.scaleY)
  while (sectionY < height) {
    context.beginPath()
    context.moveTo(0, sectionY)
    context.lineTo(width, sectionY)
    context.stroke()
    sectionY += sectionHeight
  }

  drawRails(context, metrics, state, palette)

  const drift = reducedMotion ? 0 : Math.sin(state.tick * .018) * height * .018
  for (const [index, yRatio] of [.22, .57, .84].entries()) {
    const fog = context.createLinearGradient(0, 0, width, 0)
    fog.addColorStop(0, 'rgba(0,0,0,0)')
    fog.addColorStop(.5, palette.fog)
    fog.addColorStop(1, 'rgba(0,0,0,0)')
    context.fillStyle = fog
    context.globalAlpha = .42 - index * .07
    context.fillRect(0, height * yRatio + drift * (index % 2 ? -1 : 1), width, height * .055)
  }
  context.globalAlpha = 1
}

function drawRails(
  context: CanvasRenderingContext2D,
  metrics: RenderMetrics,
  state: ShaftState,
  palette: DeepShaftPalette,
) {
  const { width, height, unit } = metrics
  const railWidth = Math.max(8 * unit, width * .022)
  const railPositions = [width * .055, width * .945]

  for (const railX of railPositions) {
    const rail = context.createLinearGradient(
      railX - railWidth,
      0,
      railX + railWidth,
      0,
    )
    rail.addColorStop(0, palette.rail)
    rail.addColorStop(.48, palette.railEdge)
    rail.addColorStop(.62, palette.rail)
    rail.addColorStop(1, palette.rail)
    context.fillStyle = rail
    roundedRect(context, railX - railWidth / 2, 0, railWidth, height, railWidth / 2)
    context.fill()
    context.strokeStyle = palette.wallEdge
    context.lineWidth = Math.max(1, unit * .65)
    context.stroke()

    const jointGap = Math.max(70 * unit, height * .16)
    let jointY = -((state.cameraY * metrics.scaleY) % jointGap)
    while (jointY < height + jointGap) {
      context.fillStyle = palette.railJoint
      context.shadowColor = palette.fog
      context.shadowBlur = 5 * unit
      context.beginPath()
      context.arc(railX, jointY, railWidth * .43, 0, Math.PI * 2)
      context.fill()
      context.shadowBlur = 0
      jointY += jointGap
    }
  }
}

function drawPlatformSide(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  deckHeight: number,
  depth: number,
  material: ShaftMaterial,
) {
  context.fillStyle = material.side
  context.beginPath()
  context.moveTo(x + deckHeight * .3, y + deckHeight)
  context.lineTo(x + width - deckHeight * .3, y + deckHeight)
  context.lineTo(x + width - deckHeight * .8, y + deckHeight + depth)
  context.lineTo(x + deckHeight * .8, y + deckHeight + depth)
  context.closePath()
  context.fill()

  context.strokeStyle = material.edge
  context.globalAlpha = .34
  context.beginPath()
  context.moveTo(x + deckHeight * .8, y + deckHeight + depth - 1)
  context.lineTo(x + width - deckHeight * .8, y + deckHeight + depth - 1)
  context.stroke()
  context.globalAlpha = 1
}

function drawPlatformDetail(
  context: CanvasRenderingContext2D,
  platform: ShaftPlatform,
  state: ShaftState,
  x: number,
  y: number,
  width: number,
  deckHeight: number,
  material: ShaftMaterial,
) {
  context.save()
  context.strokeStyle = material.detail
  context.fillStyle = material.detail
  context.lineWidth = Math.max(1, deckHeight * .12)
  context.lineCap = 'round'
  context.lineJoin = 'round'

  if (platform.kind === 'spikes') {
    const spikeWidth = Math.max(deckHeight * .86, width / 11)
    for (let spikeX = x + spikeWidth * .25; spikeX < x + width - spikeWidth; spikeX += spikeWidth) {
      const spikeGradient = context.createLinearGradient(spikeX, y - deckHeight, spikeX + spikeWidth, y)
      spikeGradient.addColorStop(0, material.edge)
      spikeGradient.addColorStop(1, material.detail)
      context.fillStyle = spikeGradient
      context.beginPath()
      context.moveTo(spikeX, y + deckHeight * .08)
      context.lineTo(spikeX + spikeWidth * .5, y - deckHeight * .88)
      context.lineTo(spikeX + spikeWidth, y + deckHeight * .08)
      context.closePath()
      context.fill()
    }
  } else if (platform.kind === 'crumble') {
    const due = state.crumbleDue.get(platform.floor)
    const progress = due === undefined
      ? 0
      : Math.min(1, 1 - Math.max(0, due - state.tick) / CRUMBLE_DELAY_TICKS)
    context.globalAlpha = .64 + progress * .36
    const cracks = [.2, .44, .7]
    for (const ratio of cracks) {
      context.beginPath()
      context.moveTo(x + width * ratio, y + deckHeight * .08)
      context.lineTo(x + width * (ratio + .04), y + deckHeight * .45)
      context.lineTo(x + width * (ratio - .015), y + deckHeight * .82)
      context.stroke()
    }
  } else if (platform.kind === 'spring') {
    const padWidth = Math.min(width * .34, deckHeight * 4.4)
    const center = x + width / 2
    context.strokeStyle = material.edge
    context.lineWidth = Math.max(1.5, deckHeight * .14)
    context.beginPath()
    for (let index = 0; index <= 7; index += 1) {
      const coilX = center - padWidth / 2 + padWidth * index / 7
      const coilY = y - deckHeight * (.08 + (index % 2 ? .5 : .12))
      if (index === 0) context.moveTo(coilX, coilY)
      else context.lineTo(coilX, coilY)
    }
    context.stroke()
    context.fillStyle = material.detail
    roundedRect(context, center - padWidth * .58, y - deckHeight * .76, padWidth * 1.16, deckHeight * .25, deckHeight * .13)
    context.fill()
  } else if (platform.kind.startsWith('conveyor')) {
    const direction = platform.kind === 'conveyor_left' ? -1 : 1
    const rollerRadius = Math.max(2, deckHeight * .18)
    const rollerGap = Math.max(rollerRadius * 3, width / 9)
    for (let rollerX = x + rollerGap * .55; rollerX < x + width - rollerGap * .4; rollerX += rollerGap) {
      context.beginPath()
      context.arc(rollerX, y + deckHeight * .5, rollerRadius, 0, Math.PI * 2)
      context.stroke()
      context.beginPath()
      context.moveTo(rollerX - direction * rollerRadius * .55, y + deckHeight * .5)
      context.lineTo(rollerX + direction * rollerRadius * .55, y + deckHeight * .5)
      context.stroke()
    }
  } else {
    context.globalAlpha = .5
    for (let groove = x + width * .2; groove < x + width * .9; groove += width * .2) {
      context.beginPath()
      context.moveTo(groove, y + deckHeight * .22)
      context.lineTo(groove, y + deckHeight * .74)
      context.stroke()
    }
  }
  context.restore()
}

function drawPlatform(
  context: CanvasRenderingContext2D,
  metrics: RenderMetrics,
  platform: ShaftPlatform,
  state: ShaftState,
  palette: DeepShaftPalette,
) {
  if (state.brokenFloors.has(platform.floor)) return
  const y = (platform.y - state.cameraY) * metrics.scaleY
  if (y < -metrics.height * .08 || y > metrics.height * 1.05) return
  const x = platform.x * metrics.scaleX
  const width = platform.width * metrics.scaleX
  const deckHeight = Math.max(11 * metrics.unit, metrics.height * .018)
  const depth = deckHeight * .62
  const material = palette.platforms[platform.kind]

  context.save()
  context.shadowColor = material.glow
  context.shadowBlur = deckHeight * 1.35
  drawPlatformSide(context, x, y, width, deckHeight, depth, material)

  const top = context.createLinearGradient(x, y, x, y + deckHeight)
  top.addColorStop(0, material.edge)
  top.addColorStop(.16, material.top)
  top.addColorStop(1, material.side)
  context.fillStyle = top
  roundedRect(context, x, y, width, deckHeight, deckHeight * .34)
  context.fill()
  context.shadowBlur = 0
  context.strokeStyle = material.edge
  context.globalAlpha = .72
  context.lineWidth = Math.max(1, metrics.unit)
  context.stroke()
  context.globalAlpha = 1

  context.strokeStyle = material.edge
  context.globalAlpha = .23
  context.lineWidth = Math.max(1, metrics.unit * .65)
  roundedRect(
    context,
    x + deckHeight * .22,
    y + deckHeight * .2,
    width - deckHeight * .44,
    deckHeight * .52,
    deckHeight * .2,
  )
  context.stroke()
  context.globalAlpha = 1

  drawPlatformDetail(context, platform, state, x, y, width, deckHeight, material)

  const labelSize = Math.max(8 * metrics.unit, metrics.width * .012)
  context.fillStyle = palette.depthText
  context.font = `800 ${labelSize}px ui-monospace, SFMono-Regular, monospace`
  context.textBaseline = 'middle'
  context.globalAlpha = .8
  context.fillText(`${String(platform.floor).padStart(2, '0')}F`, x + deckHeight * .55, y + deckHeight + depth * .5)
  context.globalAlpha = 1
  context.restore()
}

function drawPressureCeiling(
  context: CanvasRenderingContext2D,
  metrics: RenderMetrics,
  state: ShaftState,
  palette: DeepShaftPalette,
) {
  const ceilingHeight = Math.max(8 * metrics.unit, CEILING_DEPTH * metrics.scaleY)
  const pressure = Math.max(0, Math.min(1, 1 - (
    state.playerY - state.cameraY - CEILING_DEPTH
  ) / 1_250))
  const warning = context.createLinearGradient(0, 0, 0, ceilingHeight * 2.7)
  warning.addColorStop(0, palette.pressureGlow)
  warning.addColorStop(1, 'rgba(0,0,0,0)')
  context.fillStyle = warning
  context.globalAlpha = .34 + pressure * .5
  context.fillRect(0, 0, metrics.width, ceilingHeight * 2.7)
  context.globalAlpha = 1

  const chevronWidth = Math.max(22 * metrics.unit, metrics.width * .055)
  context.fillStyle = palette.pressure
  context.shadowColor = palette.pressureGlow
  context.shadowBlur = 9 * metrics.unit
  for (let x = -chevronWidth; x < metrics.width + chevronWidth; x += chevronWidth) {
    context.beginPath()
    context.moveTo(x, 0)
    context.lineTo(x + chevronWidth * .5, ceilingHeight)
    context.lineTo(x + chevronWidth, 0)
    context.closePath()
    context.fill()
  }
  context.shadowBlur = 0
}

function drawDescentPod(
  context: CanvasRenderingContext2D,
  metrics: RenderMetrics,
  state: ShaftState,
  palette: DeepShaftPalette,
) {
  const x = state.playerX * metrics.scaleX
  const y = (state.playerY - state.cameraY) * metrics.scaleY
  const halfWidth = Math.max(metrics.width * .038, 14 * metrics.unit)
  const halfHeight = halfWidth * 1.15
  const danger = state.health <= 3

  context.save()
  context.translate(x, y)

  context.fillStyle = danger ? palette.pressureGlow : palette.podGlow
  context.globalAlpha = .18
  context.beginPath()
  context.arc(0, 0, halfWidth * 2.25, 0, Math.PI * 2)
  context.fill()
  context.globalAlpha = 1

  context.shadowColor = danger ? palette.pressureGlow : palette.podGlow
  context.shadowBlur = halfWidth * 1.25
  const hull = context.createLinearGradient(-halfWidth, -halfHeight, halfWidth, halfHeight)
  hull.addColorStop(0, palette.podEdge)
  hull.addColorStop(.38, palette.podBody)
  hull.addColorStop(1, palette.podSide)
  context.fillStyle = hull
  roundedRect(
    context,
    -halfWidth,
    -halfHeight,
    halfWidth * 2,
    halfHeight * 2,
    halfWidth * .62,
  )
  context.fill()
  context.shadowBlur = 0
  context.strokeStyle = danger ? palette.pressure : palette.podEdge
  context.lineWidth = Math.max(1.3, halfWidth * .08)
  context.stroke()

  context.fillStyle = palette.podSide
  roundedRect(
    context,
    -halfWidth * 1.25,
    -halfHeight * .2,
    halfWidth * .32,
    halfHeight * .82,
    halfWidth * .12,
  )
  context.fill()
  roundedRect(
    context,
    halfWidth * .93,
    -halfHeight * .2,
    halfWidth * .32,
    halfHeight * .82,
    halfWidth * .12,
  )
  context.fill()

  const glass = context.createRadialGradient(
    -halfWidth * .18,
    -halfHeight * .38,
    0,
    0,
    -halfHeight * .22,
    halfWidth * .7,
  )
  glass.addColorStop(0, palette.podEdge)
  glass.addColorStop(.26, palette.podGlass)
  glass.addColorStop(1, palette.podSide)
  context.fillStyle = glass
  context.beginPath()
  context.arc(0, -halfHeight * .27, halfWidth * .47, 0, Math.PI * 2)
  context.fill()
  context.strokeStyle = palette.podEdge
  context.globalAlpha = .74
  context.stroke()
  context.globalAlpha = 1

  context.fillStyle = danger ? palette.pressure : palette.podCore
  context.shadowColor = danger ? palette.pressureGlow : palette.podGlow
  context.shadowBlur = halfWidth * .8
  context.beginPath()
  context.arc(0, halfHeight * .43, halfWidth * .17, 0, Math.PI * 2)
  context.fill()
  context.shadowBlur = 0

  if (state.velocityY > 10) {
    context.strokeStyle = danger ? palette.pressure : palette.podCore
    context.globalAlpha = .42
    context.lineWidth = Math.max(1, halfWidth * .07)
    for (const offset of [-.46, .46]) {
      context.beginPath()
      context.moveTo(halfWidth * offset, halfHeight * 1.06)
      context.lineTo(halfWidth * offset, halfHeight * 1.58)
      context.stroke()
    }
    context.globalAlpha = 1
  }
  context.restore()
}

export function renderDeepShaft(
  canvas: HTMLCanvasElement,
  frame: DeepShaftRenderFrame,
) {
  const context = canvas.getContext('2d')
  if (!context) return
  const metrics: RenderMetrics = {
    width: canvas.width,
    height: canvas.height,
    scaleX: canvas.width / WORLD_WIDTH,
    scaleY: canvas.height / VIEW_HEIGHT,
    unit: Math.max(.7, canvas.width / 720),
  }
  const palette = deepShaftPalette(frame.theme)

  context.clearRect(0, 0, metrics.width, metrics.height)
  drawShaftBackground(
    context,
    metrics,
    frame.state,
    palette,
    Boolean(frame.reducedMotion),
  )
  for (const platform of frame.platforms) {
    drawPlatform(context, metrics, platform, frame.state, palette)
  }
  drawPressureCeiling(context, metrics, frame.state, palette)
  drawDescentPod(context, metrics, frame.state, palette)
}

export function deepShaftProgress(floor: number): number {
  return Math.max(0, Math.min(100, floor * 100 / TARGET_FLOOR))
}
