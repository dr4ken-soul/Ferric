import { mkdir, readFile, writeFile } from 'node:fs/promises'

const distRoot = new URL('../dist/', import.meta.url)
const entry = await readFile(new URL('index.html', distRoot), 'utf8')
await mkdir(new URL('docs/', distRoot), { recursive: true })
await writeFile(new URL('docs/index.html', distRoot), entry, 'utf8')
