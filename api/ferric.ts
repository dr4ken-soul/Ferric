import { handleDemoRequest } from '../web/server/demo.js'

interface VercelRequest {
  method?: string
  body: unknown
}

interface VercelResponse {
  status(code: number): VercelResponse
  json(value: unknown): VercelResponse
}

/** Record one live Groq interaction when the repository root is the Vercel root. */
export default async function handler(request: VercelRequest, response: VercelResponse) {
  if (request.method !== 'POST') return response.status(405).json({ error: 'POST required.' })
  try {
    return response.status(200).json(await handleDemoRequest(request.body, process.env))
  } catch (error) {
    const message = error instanceof Error ? error.message : 'The hosted demo failed.'
    return response.status(400).json({ error: message })
  }
}
