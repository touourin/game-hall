import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  expectedGameIconSize,
  verifyGameIconBuffer,
} from './game-icon-utils.mjs'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const iconDirectory = path.resolve(scriptDirectory, '../src/assets/game-hall/icons')
const allowedSupportFiles = new Set(['README.md'])

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
    verifyGameIconBuffer(buffer, entry.name)
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
  console.log(
    `Verified ${variantsBySlug.size} official game icon pairs at `
    + `${expectedGameIconSize}x${expectedGameIconSize}.`,
  )
}
