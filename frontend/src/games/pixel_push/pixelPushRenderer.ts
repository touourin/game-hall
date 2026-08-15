import type { ThemeName } from '../../theme'
import { pixelPushPalette, type PixelPushPalette } from './pixelPushPalettes'
import type {
  PixelPushEvent,
  PixelPushMapKey,
  PixelPushPlayerState,
} from './types'

export interface PixelPushRenderFrame {
  worldWidth: number
  worldHeight: number
  map: PixelPushMapKey
  shrinkProgress: number
  tick: number
  timestamp: number
  players: PixelPushPlayerState[]
  events: PixelPushEvent[]
  theme: ThemeName
  dpr?: number
  reducedMotion?: boolean
}

interface ArenaDimensions {
  halfWidth: number
  halfHeight: number
  radius: number
}

function roundedRectPath(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  const right = x + width
  const bottom = y + height
  context.beginPath()
  context.moveTo(x + radius, y)
  context.lineTo(right - radius, y)
  context.quadraticCurveTo(right, y, right, y + radius)
  context.lineTo(right, bottom - radius)
  context.quadraticCurveTo(right, bottom, right - radius, bottom)
  context.lineTo(x + radius, bottom)
  context.quadraticCurveTo(x, bottom, x, bottom - radius)
  context.lineTo(x, y + radius)
  context.quadraticCurveTo(x, y, x + radius, y)
  context.closePath()
}

export function pixelPushArenaDimensions(
  map: PixelPushMapKey,
  progress: number,
): ArenaDimensions {
  if (map === 'moon_station') {
    return {
      halfWidth: 4_200 - progress * 2_150 / 1_000,
      halfHeight: 2_700 - progress * 1_150 / 1_000,
      radius: 760,
    }
  }
  return {
    halfWidth: 4_250 - progress * 1_050 / 1_000,
    halfHeight: 2_450 - progress * 1_150 / 1_000,
    radius: 420,
  }
}

function arenaPath(
  context: CanvasRenderingContext2D,
  map: PixelPushMapKey,
  progress: number,
) {
  if (map !== 'cross_bridge') {
    const dimensions = pixelPushArenaDimensions(map, progress)
    roundedRectPath(
      context,
      5_000 - dimensions.halfWidth,
      3_500 - dimensions.halfHeight,
      dimensions.halfWidth * 2,
      dimensions.halfHeight * 2,
      dimensions.radius,
    )
    return
  }

  const centreX = 5_000
  const centreY = 3_500
  const centreHalfWidth = 1_900
  const centreHalfHeight = 1_450
  const armHalfThickness = 720
  const armX = 2_250 * (1_000 - progress) / 1_000
  const armY = 1_100 * (1_000 - progress) / 1_000
  const points: Array<[number, number]> = [
    [-armHalfThickness, -centreHalfHeight - armY],
    [armHalfThickness, -centreHalfHeight - armY],
    [armHalfThickness, -centreHalfHeight],
    [centreHalfWidth, -centreHalfHeight],
    [centreHalfWidth, -armHalfThickness],
    [centreHalfWidth + armX, -armHalfThickness],
    [centreHalfWidth + armX, armHalfThickness],
    [centreHalfWidth, armHalfThickness],
    [centreHalfWidth, centreHalfHeight],
    [armHalfThickness, centreHalfHeight],
    [armHalfThickness, centreHalfHeight + armY],
    [-armHalfThickness, centreHalfHeight + armY],
    [-armHalfThickness, centreHalfHeight],
    [-centreHalfWidth, centreHalfHeight],
    [-centreHalfWidth, armHalfThickness],
    [-centreHalfWidth - armX, armHalfThickness],
    [-centreHalfWidth - armX, -armHalfThickness],
    [-centreHalfWidth, -armHalfThickness],
    [-centreHalfWidth, -centreHalfHeight],
    [-armHalfThickness, -centreHalfHeight],
  ]
  context.beginPath()
  context.moveTo(centreX + points[0]![0], centreY + points[0]![1])
  for (const [x, y] of points.slice(1)) {
    context.lineTo(centreX + x, centreY + y)
  }
  context.closePath()
}

function drawVoid(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  palette: PixelPushPalette,
) {
  const backdrop = context.createLinearGradient(0, 0, 0, height)
  backdrop.addColorStop(0, palette.voidTop)
  backdrop.addColorStop(.52, palette.voidCenter)
  backdrop.addColorStop(1, palette.voidBottom)
  context.fillStyle = backdrop
  context.fillRect(0, 0, width, height)

  const atmosphere = context.createRadialGradient(
    width * .5,
    height * .44,
    0,
    width * .5,
    height * .44,
    Math.max(width, height) * .64,
  )
  atmosphere.addColorStop(0, palette.voidGlow)
  atmosphere.addColorStop(1, 'rgba(0,0,0,0)')
  context.fillStyle = atmosphere
  context.fillRect(0, 0, width, height)

  context.fillStyle = palette.particle
  for (let index = 0; index < 72; index += 1) {
    const x = (index * 2_137 % 9_973) / 9_973 * width
    const y = (index * 3_791 % 9_941) / 9_941 * height
    const size = index % 9 === 0 ? 3 : 1
    context.fillRect(Math.round(x), Math.round(y), size, size)
  }
}

function drawArena(
  context: CanvasRenderingContext2D,
  map: PixelPushMapKey,
  progress: number,
  tick: number,
  palette: PixelPushPalette,
) {
  context.save()
  context.shadowColor = progress > 0 ? palette.dangerGlow : palette.arenaGlow
  context.shadowBlur = progress > 0 ? 180 : 110
  const surface = context.createLinearGradient(0, 800, 0, 6_200)
  surface.addColorStop(0, palette.arenaTop)
  surface.addColorStop(1, palette.arenaBottom)
  context.fillStyle = surface
  context.strokeStyle = progress > 0 ? palette.dangerEdge : palette.arenaEdge
  context.lineWidth = 52
  arenaPath(context, map, progress)
  context.fill()
  context.shadowBlur = 0
  context.stroke()

  context.save()
  arenaPath(context, map, progress)
  context.clip()
  context.strokeStyle = palette.arenaGrid
  context.lineWidth = 14
  const tile = 500
  for (let x = 750; x < 9_500; x += tile) {
    context.beginPath()
    context.moveTo(x, 650)
    context.lineTo(x, 6_350)
    context.stroke()
  }
  for (let y = 750; y < 6_500; y += tile) {
    context.beginPath()
    context.moveTo(650, y)
    context.lineTo(9_350, y)
    context.stroke()
  }

  context.strokeStyle = palette.arenaInnerEdge
  context.globalAlpha = .74
  context.lineWidth = 18
  arenaPath(context, map, progress)
  context.stroke()
  context.globalAlpha = 1

  if (map === 'pulse_factory') {
    const cycleTicks = 8 * 30
    const cycleTick = tick % cycleTicks
    const start = 2 * 30
    const travel = 3 * 30
    if (cycleTick >= start && cycleTick < start + travel) {
      const pulseX = 1_050 + (cycleTick - start) / travel * 7_900
      const pulse = context.createLinearGradient(
        pulseX - 310,
        0,
        pulseX + 310,
        0,
      )
      pulse.addColorStop(0, 'rgba(0,0,0,0)')
      pulse.addColorStop(.5, palette.pulseGlow)
      pulse.addColorStop(1, 'rgba(0,0,0,0)')
      context.fillStyle = pulse
      context.fillRect(pulseX - 310, 950, 620, 5_100)
      context.fillStyle = palette.pulseCore
      context.globalAlpha = .72
      context.fillRect(pulseX - 26, 950, 52, 5_100)
      context.globalAlpha = 1
    }
  }
  context.restore()
  context.restore()
}

function drawPlayer(
  context: CanvasRenderingContext2D,
  player: PixelPushPlayerState,
  palette: PixelPushPalette,
) {
  const color = player.color ?? '#5ce1e6'
  const angle = Math.atan2(player.facingY, player.facingX)
  context.save()
  context.translate(player.x, player.y)
  context.globalAlpha = player.alive ? 1 : .22

  context.fillStyle = palette.playerShadow
  context.beginPath()
  context.ellipse(40, 170, 330, 150, 0, 0, Math.PI * 2)
  context.fill()

  if (player.dashing) {
    context.save()
    context.rotate(angle)
    context.fillStyle = `${color}22`
    context.fillRect(-840, -210, 650, 420)
    context.fillStyle = `${color}55`
    context.fillRect(-620, -140, 420, 280)
    context.restore()
  }

  if (player.bracing) {
    context.save()
    context.rotate(angle)
    context.strokeStyle = palette.brace
    context.lineWidth = 64
    context.beginPath()
    context.arc(0, 0, 430, -.88, .88)
    context.stroke()
    context.strokeStyle = palette.braceSoft
    context.lineWidth = 18
    context.beginPath()
    context.arc(0, 0, 475, -.72, .72)
    context.stroke()
    context.restore()
  }

  context.rotate(angle)
  context.fillStyle = palette.robotOutline
  context.fillRect(-255, -255, 510, 510)
  context.fillStyle = color
  context.fillRect(-220, -220, 440, 440)
  context.fillStyle = palette.robotHighlight
  context.fillRect(-180, -180, 360, 72)
  context.fillStyle = palette.robotFace
  context.fillRect(50, -92, 108, 76)
  context.fillRect(50, 34, 108, 76)
  context.fillStyle = palette.robotEye
  context.fillRect(76, -72, 54, 38)
  context.fillRect(76, 54, 54, 38)
  context.fillStyle = palette.robotFace
  context.fillRect(-205, -24, 130, 48)
  context.fillStyle = color
  context.fillRect(-315, -160, 95, 120)
  context.fillRect(-315, 40, 95, 120)
  context.restore()

  context.save()
  context.translate(player.x, player.y - 470)
  context.textAlign = 'center'
  context.font = '800 180px ui-monospace, monospace'
  context.lineWidth = 38
  context.strokeStyle = palette.playerNameOutline
  context.strokeText(player.name ?? `P${(player.seat ?? 0) + 1}`, 0, 0)
  context.fillStyle = palette.playerName
  context.fillText(player.name ?? `P${(player.seat ?? 0) + 1}`, 0, 0)
  context.restore()
}

function drawEventEffects(
  context: CanvasRenderingContext2D,
  players: PixelPushPlayerState[],
  events: PixelPushEvent[],
  tick: number,
  palette: PixelPushPalette,
) {
  const playerById = new Map(players.map(player => [player.id, player]))
  for (const event of events) {
    const age = tick - event.tick
    if (age < 0 || age > 10 || !event.targetId) continue
    const target = playerById.get(event.targetId)
    if (!target) continue
    const progress = age / 10
    context.save()
    context.translate(target.x, target.y)
    context.globalAlpha = 1 - progress
    context.strokeStyle = event.kind === 'braced' ? palette.brace : palette.impact
    context.lineWidth = 38
    for (let index = 0; index < 8; index += 1) {
      const angle = index * Math.PI / 4 + event.id * .37
      const inner = 300 + progress * 180
      const outer = 480 + progress * 360
      context.beginPath()
      context.moveTo(Math.cos(angle) * inner, Math.sin(angle) * inner)
      context.lineTo(Math.cos(angle) * outer, Math.sin(angle) * outer)
      context.stroke()
    }
    context.restore()
  }
}

export function renderPixelPush(
  canvas: HTMLCanvasElement,
  frame: PixelPushRenderFrame,
) {
  const context = canvas.getContext('2d')
  if (!context) return
  const width = canvas.width
  const height = canvas.height
  const palette = pixelPushPalette(frame.theme)
  context.clearRect(0, 0, width, height)
  context.imageSmoothingEnabled = false
  drawVoid(context, width, height, palette)

  const scale = Math.min(
    width / frame.worldWidth,
    height / frame.worldHeight,
  )
  const offsetX = (width - frame.worldWidth * scale) / 2
  const offsetY = (height - frame.worldHeight * scale) / 2
  const recentImpact = frame.events.some(event => (
    ['hit', 'braced', 'ring_out'].includes(event.kind)
    && frame.tick - event.tick >= 0
    && frame.tick - event.tick <= 2
  ))
  const shake = recentImpact && !frame.reducedMotion
    ? Math.sin(frame.timestamp * .08) * 5 * (frame.dpr ?? 1)
    : 0

  context.save()
  context.translate(offsetX + shake, offsetY - shake * .45)
  context.scale(scale, scale)
  drawArena(
    context,
    frame.map,
    frame.shrinkProgress,
    frame.tick,
    palette,
  )
  for (const player of frame.players.filter(item => item.alive)) {
    drawPlayer(context, player, palette)
  }
  drawEventEffects(
    context,
    frame.players,
    frame.events,
    frame.tick,
    palette,
  )
  context.restore()
}
