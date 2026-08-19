import { defineConfig } from 'vite'
import { existsSync, readFileSync } from 'node:fs'
import react from '@vitejs/plugin-react'
import { handleDemoRequest } from './server/demo'

/** Load the ignored root or web-local environment file for `npm run dev`. */
function loadLocalEnvironment() {
  const files = [new URL('../.env', import.meta.url), new URL('.env.local', import.meta.url), new URL('.env', import.meta.url)]
  for (const file of files) {
    if (!existsSync(file)) continue
    for (const rawLine of readFileSync(file, 'utf8').split(/\r?\n/)) {
      const line = rawLine.trim()
      if (!line || line.startsWith('#') || !line.includes('=')) continue
      const [key, ...rest] = line.split('=')
      if (key && !process.env[key.trim()]) process.env[key.trim()] = rest.join('=').trim().replace(/^['"]|['"]$/g, '')
    }
  }
}

loadLocalEnvironment()

/** Read a JSON request body for the local demo middleware. */
async function readBody(request: import('node:http').IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = []
  for await (const chunk of request) chunks.push(Buffer.from(chunk))
  return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')
}

export default defineConfig({
  plugins: [react(), {
    name: 'ferric-local-demo-api',
    configureServer(server) {
      server.middlewares.use('/api/ferric', async (request, response) => {
        if (request.method !== 'POST') {
          response.statusCode = 405
          response.end(JSON.stringify({ error: 'POST required.' }))
          return
        }
        try {
          const result = await handleDemoRequest(await readBody(request), process.env)
          response.setHeader('content-type', 'application/json')
          response.end(JSON.stringify(result))
        } catch (error) {
          response.statusCode = 400
          response.setHeader('content-type', 'application/json')
          response.end(JSON.stringify({ error: error instanceof Error ? error.message : 'The hosted demo failed.' }))
        }
      })
    },
  }],
})
