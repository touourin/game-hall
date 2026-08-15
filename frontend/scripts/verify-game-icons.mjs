import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const iconDirectory = path.resolve(scriptDirectory, '../src/assets/game-hall/icons')
const expectedSize = 768
const allowedSupportFiles = new Set(['README.md'])

function readUint24LE(buffer, offset) {
  return buffer[offset] | (buffer[offset + 1] << 8) | (buffer[offset + 2] << 16)
}

function readWebpDimensions(buffer, filename) {
  if (
    buffer.length < 30
    || buffer.toString('ascii', 0, 4) !== 'RIFF'
    || buffer.toString('ascii', 8, 12) !== 'WEBP'
  ) {
    throw new Error(`${filename} is not a valid WebP file`)
  }

  let chunkOffset = 12
  while (chunkOffset + 8 <= buffer.length) {
    const chunkType = buffer.toString('ascii', chunkOffset, chunkOffset + 4)
    const chunkSize = buffer.readUInt32LE(chunkOffset + 4)
    const dataOffset = chunkOffset + 8

    if (chunkType === 'VP8 ' && dataOffset + 10 <= buffer.length) {
      return {
        width: buffer.readUInt16LE(dataOffset + 6) & 0x3fff,
        height: buffer.readUInt16LE(dataOffset + 8) & 0x3fff,
      }
    }

    if (chunkType === 'VP8L' && dataOffset + 5 <= buffer.length) {
      const bits = buffer.readUInt32LE(dataOffset + 1)
      return {
        width: (bits & 0x3fff) + 1,
        height: ((bits >>> 14) & 0x3fff) + 1,
      }
    }

    if (chunkType === 'VP8X' && dataOffset + 10 <= buffer.length) {
      return {
        width: readUint24LE(buffer, dataOffset + 4) + 1,
        height: readUint24LE(buffer, dataOffset + 7) + 1,
      }
    }

    chunkOffset = dataOffset + chunkSize + (chunkSize % 2)
  }

  throw new Error(`${filename} has no supported WebP image chunk`)
}

const entries = await readdir(iconDirectory, { withFileTypes: true })
const errors = []
const variantsBySlug = new Map()

for (const entry of entries) {
  if (!entry.isFile()) {
    errors.push(`unexpected directory: ${entry.name}`)
    continue
  }

  if (allowedSupportFiles.has(entry.name)) continue

  const match = /^(?<slug>[a-z0-9]+(?:-[a-z0-9]+)*)-(?<variant>dark|light)\.webp$/.exec(entry.name)
  if (!match?.groups) {
    errors.push(`unexpected file: ${entry.name}; only paired *-dark.webp and *-light.webp assets are allowed`)
    continue
  }

  const { slug, variant } = match.groups
  const variants = variantsBySlug.get(slug) ?? new Set()
  variants.add(variant)
  variantsBySlug.set(slug, variants)

  try {
    const buffer = await readFile(path.join(iconDirectory, entry.name))
    const { width, height } = readWebpDimensions(buffer, entry.name)
    if (width !== expectedSize || height !== expectedSize) {
      errors.push(`${entry.name} is ${width}x${height}; expected ${expectedSize}x${expectedSize}`)
    }
  } catch (error) {
    errors.push(error instanceof Error ? error.message : String(error))
  }
}

for (const [slug, variants] of variantsBySlug) {
  for (const requiredVariant of ['dark', 'light']) {
    if (!variants.has(requiredVariant)) errors.push(`${slug} is missing its ${requiredVariant} variant`)
  }
}

if (errors.length > 0) {
  console.error('Official game icon verification failed:')
  for (const error of errors) console.error(`- ${error}`)
  process.exitCode = 1
} else {
  console.log(`Verified ${variantsBySlug.size} official game icon pairs at ${expectedSize}x${expectedSize}.`)
}
