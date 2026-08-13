import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = dirname(fileURLToPath(import.meta.url))
const projectRoot = resolve(scriptDirectory, '../..')
const pluginRoot = join(projectRoot, 'third_party_games')
const output = join(projectRoot, 'frontend/src/generated/thirdPartyGameModules.ts')
const pluginId = /^plugin-[a-z0-9][a-z0-9-]{0,24}$/

const modules = []
if (existsSync(pluginRoot)) {
  for (const directory of readdirSync(pluginRoot, { withFileTypes: true })) {
    if (!directory.isDirectory()) continue
    const manifestPath = join(pluginRoot, directory.name, 'manifest.json')
    if (!existsSync(manifestPath)) continue
    try {
      const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
      if (manifest.enabled !== true) continue
      const players = manifest.players
      if (
        manifest.apiVersion !== 1
        || manifest.id !== directory.name
        || !pluginId.test(manifest.id)
        || typeof manifest.name !== 'string'
        || !manifest.name.trim()
        || manifest.name.length > 24
        || typeof manifest.description !== 'string'
        || !manifest.description.trim()
        || manifest.description.length > 80
        || typeof manifest.category !== 'string'
        || !manifest.category.trim()
        || manifest.category.length > 16
        || typeof manifest.tone !== 'string'
        || !/^[a-z0-9][a-z0-9-]{0,23}$/.test(manifest.tone)
        || (manifest.roomLayout !== undefined && (
          !['standard', 'wide', 'immersive'].includes(manifest.roomLayout)
        ))
        || !Number.isInteger(players?.min)
        || !Number.isInteger(players?.max)
        || players.min < 1
        || players.max < players.min
        || players.max > 20
        || (players.label !== undefined && (
          typeof players.label !== 'string'
          || !players.label.trim()
          || players.label.length > 16
        ))
        || (manifest.defaultOptions !== undefined && (
          !manifest.defaultOptions
          || typeof manifest.defaultOptions !== 'object'
          || Array.isArray(manifest.defaultOptions)
        ))
        || (manifest.ruleLabels !== undefined && (
          !Array.isArray(manifest.ruleLabels)
          || manifest.ruleLabels.length > 6
          || manifest.ruleLabels.some((label) => (
            typeof label !== 'string' || !label.trim() || label.length > 24
          ))
        ))
      ) throw new Error('manifest.json 字段不符合插件 API v1')
      const viewPath = join(pluginRoot, directory.name, 'frontend/GameView.vue')
      if (!existsSync(viewPath)) throw new Error('缺少 frontend/GameView.vue')
      modules.push({ directory: directory.name, manifest })
    }
    catch (error) {
      const reason = error instanceof Error ? error.message : String(error)
      console.warn(`[game-hall plugins] 已跳过 ${directory.name}：${reason}`)
    }
  }
}

modules.sort((left, right) => left.directory.localeCompare(right.directory))
const entries = modules.map(({ directory, manifest }) => `  {
    directory: ${JSON.stringify(directory)},
    manifest: ${JSON.stringify(manifest, null, 2).split('\n').join('\n    ')},
    loadView: () => import(${JSON.stringify(`../../../third_party_games/${directory}/frontend/GameView.vue`)}),
  }`)
const source = `// 此文件由 scripts/generate-plugin-registry.mjs 自动生成，请勿手动修改。\nexport const GENERATED_THIRD_PARTY_GAME_MODULES = [\n${entries.join(',\n')}\n] as const\n`

mkdirSync(dirname(output), { recursive: true })
if (!existsSync(output) || readFileSync(output, 'utf8') !== source) {
  writeFileSync(output, source, 'utf8')
}
