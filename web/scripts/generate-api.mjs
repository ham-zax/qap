import { spawnSync } from 'node:child_process'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const webRoot = dirname(dirname(fileURLToPath(import.meta.url)))
const arguments_ = process.argv.slice(2).filter((argument) => argument !== '--')
if (arguments_.length > 1) {
  console.error('usage: pnpm generate:api -- [openapi.json]')
  process.exit(2)
}
const input = resolve(arguments_[0] ?? join(webRoot, 'openapi.json'))
const output = join(webRoot, 'src/api/schema.d.ts')
const executable = join(webRoot, 'node_modules/.bin/openapi-typescript')

const result = spawnSync(executable, [input, '--output', output], {
  cwd: webRoot,
  stdio: 'inherit',
})

if (result.error) {
  console.error(result.error.message)
  process.exit(1)
}
process.exit(result.status ?? 1)
