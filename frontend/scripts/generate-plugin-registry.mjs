import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync,
} from 'node:fs'
import { dirname, isAbsolute, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = dirname(fileURLToPath(import.meta.url))
const projectRoot = resolve(scriptDirectory, '../..')
const pluginRoot = join(projectRoot, 'third_party_games')
const output = join(projectRoot, 'frontend/src/generated/thirdPartyGameModules.ts')
const pluginRegistryApiVersion = 1
const pluginManifestApiVersion = 1
const pluginId = /^plugin-[a-z0-9][a-z0-9-]{0,24}$/
const pluginVersion = /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$/
const actionName = /^[a-z][a-z0-9_]*$/
const registryFields = new Set(['$schema', 'apiVersion', 'plugins'])
const registryEntryFields = new Set(['id', 'path', 'status', 'order'])
const manifestFields = new Set([
  '$schema',
  'apiVersion',
  'version',
  'author',
  'license',
  'id',
  'name',
  'description',
  'category',
  'tone',
  'roomLayout',
  'players',
  'capabilities',
  'records',
  'defaultOptions',
  'ruleLabels',
])
const playerFields = new Set(['min', 'max', 'label'])
const capabilityFields = new Set([
  'guests',
  'spectators',
  'spectatorFrames',
  'firstPlayer',
  'undoActions',
  'drawRequests',
  'replay',
  'ai',
])
const recordFields = new Set(['scoreKind'])
const registryStatuses = new Set(['enabled', 'deprecated', 'disabled'])
const scoreKinds = new Set(['outcome', 'time_trial', 'high_score'])

function readJson(path, label) {
  try {
    return JSON.parse(readFileSync(path, 'utf8'))
  }
  catch (error) {
    const reason = error instanceof Error ? error.message : String(error)
    throw new Error(`${label} 无法读取：${reason}`)
  }
}

function assertObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} 必须是对象`)
  }
  return value
}

function rejectUnknownFields(value, allowed, label) {
  const unexpected = Object.keys(value).filter((field) => !allowed.has(field))
  if (unexpected.length) {
    throw new Error(`${label} 包含未知字段：${unexpected.sort().join('、')}`)
  }
}

function validateRegistry() {
  const path = join(pluginRoot, 'registry.json')
  if (!existsSync(path)) throw new Error('第三方仓库缺少 registry.json')
  const registry = assertObject(readJson(path, 'registry.json'), 'registry.json')
  rejectUnknownFields(registry, registryFields, 'registry.json')
  if (registry.$schema !== undefined && typeof registry.$schema !== 'string') {
    throw new Error('registry.json 的 $schema 必须是字符串')
  }
  if (registry.apiVersion !== pluginRegistryApiVersion) {
    throw new Error(`registry API 版本必须为 ${pluginRegistryApiVersion}`)
  }
  if (!Array.isArray(registry.plugins)) {
    throw new Error('registry.json 的 plugins 必须是数组')
  }

  const ids = new Set()
  const paths = new Set()
  const orders = new Set()
  return registry.plugins.map((candidate, index) => {
    const label = `registry.plugins[${index}]`
    const entry = assertObject(candidate, label)
    rejectUnknownFields(entry, registryEntryFields, label)
    if (typeof entry.id !== 'string' || !pluginId.test(entry.id)) {
      throw new Error(`${label}.id 不是有效的插件 ID`)
    }
    if (typeof entry.path !== 'string' || !entry.path.length) {
      throw new Error(`${label}.path 必须是相对目录`)
    }
    const directory = resolve(pluginRoot, entry.path)
    const relativePath = relative(pluginRoot, directory)
    if (
      isAbsolute(entry.path)
      || !relativePath
      || relativePath === '..'
      || relativePath.startsWith(`..${process.platform === 'win32' ? '\\' : '/'}`)
    ) throw new Error(`${label}.path 必须是安全的相对目录`)
    if (!registryStatuses.has(entry.status)) {
      throw new Error(`${label}.status 只能是 enabled、deprecated 或 disabled`)
    }
    if (!Number.isInteger(entry.order) || entry.order < 1 || entry.order > 9999) {
      throw new Error(`${label}.order 必须是 1–9999 的整数`)
    }
    if (ids.has(entry.id)) throw new Error(`registry.json 存在重复 id：${entry.id}`)
    if (paths.has(directory)) throw new Error(`registry.json 存在重复 path：${entry.path}`)
    if (orders.has(entry.order)) throw new Error(`registry.json 存在重复 order：${entry.order}`)
    ids.add(entry.id)
    paths.add(directory)
    orders.add(entry.order)
    return { ...entry, directory }
  }).sort((left, right) => left.order - right.order)
}

function pluginRepositoryAvailable() {
  if (!existsSync(pluginRoot)) return false
  if (!statSync(pluginRoot).isDirectory()) {
    throw new Error('第三方游戏路径必须是目录')
  }
  if (existsSync(join(pluginRoot, 'registry.json'))) return true
  if (readdirSync(pluginRoot).length) {
    throw new Error('第三方仓库缺少 registry.json')
  }
  return false
}

function validateManifest(candidate, entry) {
  const manifest = assertObject(candidate, `${entry.id}/manifest.json`)
  rejectUnknownFields(manifest, manifestFields, `${entry.id}/manifest.json`)
  if (manifest.$schema !== undefined && typeof manifest.$schema !== 'string') {
    throw new Error(`${entry.id}: manifest.$schema 必须是字符串`)
  }
  const strings = {
    id: [32, pluginId],
    name: [24],
    description: [80],
    category: [16],
    tone: [24, /^[a-z0-9][a-z0-9-]{0,23}$/],
    version: [48, pluginVersion],
    author: [80],
    license: [32],
  }
  if (manifest.apiVersion !== pluginManifestApiVersion) {
    throw new Error(
      `${entry.id}: 插件 API 版本必须为 ${pluginManifestApiVersion}`,
    )
  }
  for (const [field, [maximum, pattern]] of Object.entries(strings)) {
    const value = manifest[field]
    if (
      typeof value !== 'string'
      || !value.trim()
      || value.length > maximum
      || (pattern && !pattern.test(value))
    ) throw new Error(`${entry.id}: manifest.${field} 不符合约束`)
  }
  if (manifest.id !== entry.id) {
    throw new Error(`${entry.id}: registry id 必须与 manifest id 完全一致`)
  }
  if (
    manifest.roomLayout !== undefined
    && !['standard', 'wide', 'immersive'].includes(manifest.roomLayout)
  ) throw new Error(`${entry.id}: roomLayout 不符合约束`)

  const players = assertObject(manifest.players, `${entry.id}/players`)
  rejectUnknownFields(players, playerFields, `${entry.id}/players`)
  if (
    !Number.isInteger(players.min)
    || !Number.isInteger(players.max)
    || players.min < 1
    || players.max < players.min
    || players.max > 20
    || (players.label !== undefined && (
      typeof players.label !== 'string'
      || !players.label.trim()
      || players.label.length > 16
    ))
  ) throw new Error(`${entry.id}: players 不符合约束`)

  const capabilities = assertObject(
    manifest.capabilities,
    `${entry.id}/capabilities`,
  )
  rejectUnknownFields(capabilities, capabilityFields, `${entry.id}/capabilities`)
  const missingCapabilities = [...capabilityFields].filter(
    (field) => !(field in capabilities),
  )
  if (missingCapabilities.length) {
    throw new Error(`${entry.id}: capabilities 缺少 ${missingCapabilities.join('、')}`)
  }
  for (const field of [...capabilityFields].filter((item) => item !== 'undoActions')) {
    if (typeof capabilities[field] !== 'boolean') {
      throw new Error(`${entry.id}: capabilities.${field} 必须是布尔值`)
    }
  }
  if (
    !Array.isArray(capabilities.undoActions)
    || capabilities.undoActions.length > 12
    || new Set(capabilities.undoActions).size !== capabilities.undoActions.length
    || capabilities.undoActions.some((action) => (
      typeof action !== 'string'
      || action.length > 32
      || !actionName.test(action)
    ))
  ) throw new Error(`${entry.id}: capabilities.undoActions 不符合约束`)
  if (capabilities.spectatorFrames && !capabilities.spectators) {
    throw new Error(`${entry.id}: spectatorFrames 依赖 spectators`)
  }

  const records = assertObject(manifest.records, `${entry.id}/records`)
  rejectUnknownFields(records, recordFields, `${entry.id}/records`)
  if (!scoreKinds.has(records.scoreKind)) {
    throw new Error(`${entry.id}: records.scoreKind 不符合约束`)
  }
  if (
    manifest.defaultOptions !== undefined
    && (!manifest.defaultOptions
      || typeof manifest.defaultOptions !== 'object'
      || Array.isArray(manifest.defaultOptions))
  ) throw new Error(`${entry.id}: defaultOptions 必须是对象`)
  if (
    manifest.ruleLabels !== undefined
    && (!Array.isArray(manifest.ruleLabels)
      || manifest.ruleLabels.length > 6
      || manifest.ruleLabels.some((label) => (
        typeof label !== 'string' || !label.trim() || label.length > 24
      )))
  ) throw new Error(`${entry.id}: ruleLabels 不符合约束`)
  return manifest
}

const modules = []
if (pluginRepositoryAvailable()) {
  for (const entry of validateRegistry()) {
    if (entry.status === 'disabled') continue
    const manifestPath = join(entry.directory, 'manifest.json')
    const manifest = validateManifest(
      readJson(manifestPath, `${entry.id}/manifest.json`),
      entry,
    )
    for (const required of ['README.md', 'backend/plugin.py', 'frontend/GameView.vue']) {
      if (!existsSync(join(entry.directory, required))) {
        throw new Error(`${entry.id}: 缺少 ${required}`)
      }
    }
    modules.push({ entry, manifest })
  }
}

const entries = modules.map(({ entry, manifest }) => `  {
    directory: ${JSON.stringify(entry.path)},
    status: ${JSON.stringify(entry.status)},
    order: ${entry.order},
    manifest: ${JSON.stringify(manifest, null, 2).split('\n').join('\n    ')},
    loadView: () => import(${JSON.stringify(`../../../third_party_games/${entry.path}/frontend/GameView.vue`)}),
  }`)
const source = `// 此文件由 scripts/generate-plugin-registry.mjs 自动生成，请勿手动修改。\nexport const GENERATED_THIRD_PARTY_GAME_MODULES = [\n${entries.join(',\n')}\n] as const\n`

mkdirSync(dirname(output), { recursive: true })
if (!existsSync(output) || readFileSync(output, 'utf8') !== source) {
  writeFileSync(output, source, 'utf8')
}
