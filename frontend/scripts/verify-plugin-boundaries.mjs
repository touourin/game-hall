import {
  existsSync,
  readFileSync,
  readdirSync,
  statSync,
} from 'node:fs'
import { dirname, extname, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const scriptDirectory = dirname(fileURLToPath(import.meta.url))
const projectRoot = resolve(scriptDirectory, '../..')
const pluginRoot = resolve(projectRoot, 'game-hall-community-games')
const productionDependencies = new Set([
  '@game-hall/plugin-sdk',
  '@lucide/vue',
  'vue',
])
const testDependencies = new Set([
  ...productionDependencies,
  '@vue/test-utils',
  'pinia',
  'vitest',
])
const sourceExtensions = new Set([
  '.cjs',
  '.css',
  '.js',
  '.jsx',
  '.mjs',
  '.scss',
  '.ts',
  '.tsx',
  '.vue',
])

function pluginRepositoryAvailable() {
  if (!existsSync(pluginRoot)) return false
  if (!statSync(pluginRoot).isDirectory()) {
    throw new Error('社区游戏路径必须是目录')
  }
  if (existsSync(resolve(pluginRoot, 'registry.json'))) return true
  if (readdirSync(pluginRoot).length) {
    throw new Error('社区仓库缺少 registry.json')
  }
  return false
}

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = resolve(directory, entry.name)
    if (entry.isDirectory()) return walk(path)
    return entry.isFile() && sourceExtensions.has(extname(entry.name))
      ? [path]
      : []
  })
}

function lineNumber(source, position) {
  let line = 1
  for (let index = 0; index < position; index += 1) {
    if (source.charCodeAt(index) === 10) line += 1
  }
  return line
}

function isTestFile(path) {
  return /\.(?:spec|test)\.[^.]+$/.test(path)
}

function isInside(root, candidate) {
  const path = relative(root, candidate)
  return path !== '..' && !path.startsWith(`..${process.platform === 'win32' ? '\\' : '/'}`)
}

function scriptBlocks(source, path) {
  if (extname(path) !== '.vue') {
    return [{ source, offset: 0 }]
  }
  return [...source.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)]
    .map((match) => {
      const content = match[1] ?? ''
      const contentOffset = (match.index ?? 0) + match[0].indexOf(content)
      return { source: content, offset: contentOffset }
    })
}

function styleBlocks(source, path) {
  if (extname(path) === '.css' || extname(path) === '.scss') {
    return [{ source, offset: 0 }]
  }
  if (extname(path) !== '.vue') return []
  return [...source.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)]
    .map((match) => {
      const content = match[1] ?? ''
      const contentOffset = (match.index ?? 0) + match[0].indexOf(content)
      return { source: content, offset: contentOffset }
    })
}

function moduleSpecifiers(source, path) {
  const specifiers = []
  for (const block of scriptBlocks(source, path)) {
    const parsed = ts.createSourceFile(
      path,
      block.source,
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TSX,
    )
    const visit = (node) => {
      if (
        (ts.isImportDeclaration(node) || ts.isExportDeclaration(node))
        && node.moduleSpecifier
        && ts.isStringLiteralLike(node.moduleSpecifier)
      ) {
        specifiers.push({
          value: node.moduleSpecifier.text,
          position: block.offset + node.moduleSpecifier.getStart(parsed),
        })
      } else if (ts.isCallExpression(node) && node.arguments.length) {
        const [argument] = node.arguments
        const isDynamicImport = node.expression.kind === ts.SyntaxKind.ImportKeyword
        const isRequire = ts.isIdentifier(node.expression)
          && node.expression.text === 'require'
        const isMock = ts.isPropertyAccessExpression(node.expression)
          && node.expression.name.text === 'mock'
        if (
          (isDynamicImport || isRequire || isMock)
          && argument
          && ts.isStringLiteralLike(argument)
        ) {
          specifiers.push({
            value: argument.text,
            position: block.offset + argument.getStart(parsed),
          })
        }
      }
      ts.forEachChild(node, visit)
    }
    visit(parsed)
  }
  for (const block of styleBlocks(source, path)) {
    for (const match of block.source.matchAll(
      /@import\s+(?:url\(\s*)?["']([^"']+)["']/gi,
    )) {
      specifiers.push({
        value: match[1],
        position: block.offset + (match.index ?? 0),
      })
    }
  }
  return specifiers
}

function validateImport(path, pluginDirectory, source, specifier) {
  const label = `${relative(pluginRoot, path)}:${lineNumber(source, specifier.position)}`
  const cleanSpecifier = specifier.value.split(/[?#]/, 1)[0]
  if (cleanSpecifier.startsWith('.')) {
    const target = resolve(dirname(path), cleanSpecifier)
    return isInside(pluginDirectory, target)
      ? null
      : `${label} 相对导入越过插件目录：${specifier.value}`
  }
  const allowed = isTestFile(path) ? testDependencies : productionDependencies
  return allowed.has(cleanSpecifier)
    ? null
    : `${label} 只能导入公开依赖，禁止使用：${specifier.value}`
}

if (pluginRepositoryAvailable()) {
  const pluginDirectories = readdirSync(pluginRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith('plugin-'))
    .map((entry) => resolve(pluginRoot, entry.name))
  const issues = []
  let checkedFiles = 0
  for (const pluginDirectory of pluginDirectories) {
    const frontendDirectory = resolve(pluginDirectory, 'frontend')
    if (!existsSync(frontendDirectory)) continue
    for (const path of walk(frontendDirectory)) {
      checkedFiles += 1
      const source = readFileSync(path, 'utf8')
      for (const specifier of moduleSpecifiers(source, path)) {
        const issue = validateImport(path, pluginDirectory, source, specifier)
        if (issue) issues.push(issue)
      }
    }
  }
  if (issues.length) {
    throw new Error(
      `社区插件前端导入边界校验失败：\n- ${issues.join('\n- ')}`,
    )
  }
  console.log(`社区插件前端导入边界检查通过：${checkedFiles} 个文件`)
}
