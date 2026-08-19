/** Shared server logic for the browser recording demonstration. */

import { createHash } from 'node:crypto'

export interface DemoEvent {
  index: number
  role: 'user' | 'assistant' | 'tool_call' | 'error'
  payload: Record<string, unknown>
}

export interface DemoCassette {
  id: string
  provider: 'groq'
  model: string
  recordedAt: string
  fingerprint: string
  events: DemoEvent[]
  response: Record<string, unknown>
  redactions: Array<{ ruleClass: string; eventIndex: number; fieldPath: string }>
}

export interface DemoRequest {
  prompt: string
  model?: string
}

interface GroqEnvironment extends Record<string, string | undefined> {
  GROQ_API_KEY?: string
  FERRIC_DEMO_MODEL?: string
}

const MAX_PROMPT_LENGTH = 1000
const REDACTION_RULES: Array<[string, RegExp]> = [
  ['api_key', /(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]+/g],
  ['bearer_token', /Bearer\s+[A-Za-z0-9._~+/=-]+/gi],
  ['email', /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi],
  ['card', /(?<!\d)(?:\d[ -]?){16}(?!\d)/g],
]

/** Return a stable JSON representation for hashes and replay data. */
function stableJson(value: unknown): string {
  return JSON.stringify(value, (_key, nested) => {
    if (!nested || typeof nested !== 'object' || Array.isArray(nested)) return nested
    return Object.fromEntries(Object.entries(nested).sort(([left], [right]) => left.localeCompare(right)))
  })
}

/** Hash a normalised value with SHA-256. */
function hashValue(value: unknown): string {
  return createHash('sha256').update(stableJson(value)).digest('hex')
}

/** Redact known secret forms before they enter browser-visible cassette data. */
function redactText(value: string, eventIndex: number, fieldPath: string, redactions: DemoCassette['redactions']): string {
  return REDACTION_RULES.reduce((current, [ruleClass, pattern]) => {
    return current.replace(pattern, () => {
      redactions.push({ ruleClass, eventIndex, fieldPath })
      return `[REDACTED:${ruleClass}]`
    })
  }, value)
}

/** Validate and constrain user input before sending it to Groq. */
function validateRequest(input: unknown): DemoRequest {
  if (!input || typeof input !== 'object') throw new Error('Request body must be an object.')
  const value = input as Record<string, unknown>
  if (typeof value.prompt !== 'string' || !value.prompt.trim()) throw new Error('Prompt is required.')
  return {
    prompt: value.prompt.trim().slice(0, MAX_PROMPT_LENGTH),
    model: typeof value.model === 'string' && value.model.trim() ? value.model.trim() : undefined,
  }
}

/** Call Groq, normalise the interaction and return a browser replay cassette. */
export async function recordWithGroq(input: unknown, environment: GroqEnvironment): Promise<DemoCassette> {
  const request = validateRequest(input)
  const apiKey = environment.GROQ_API_KEY?.trim()
  if (!apiKey) throw new Error('The hosted demo is not configured. Add GROQ_API_KEY in Vercel Project Settings.')

  const model = request.model || environment.FERRIC_DEMO_MODEL || 'llama-3.3-70b-versatile'
  const upstream = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({
      model,
      temperature: 0,
      messages: [
        { role: 'system', content: 'You are a concise demo assistant. Answer in two short sentences.' },
        { role: 'user', content: request.prompt },
      ],
    }),
  })
  const response = await upstream.json() as Record<string, unknown>
  if (!upstream.ok) {
    const message = typeof response.error === 'object' && response.error && 'message' in response.error
      ? String((response.error as { message: unknown }).message)
      : 'Groq returned an error.'
    throw new Error(message)
  }

  const redactions: DemoCassette['redactions'] = []
  const safeResponse = JSON.parse(
    redactText(JSON.stringify(response), -1, 'response', redactions),
  ) as Record<string, unknown>
  const userContent = redactText(request.prompt, 0, 'messages[1].content', redactions)
  const message = ((safeResponse.choices as Array<{ message?: Record<string, unknown> }> | undefined)?.[0]?.message) || {}
  const assistantContent = typeof message.content === 'string'
    ? redactText(message.content, 1, 'response.choices[0].message.content', redactions)
    : message.content ?? null
  const events: DemoEvent[] = [
    { index: 0, role: 'user', payload: { content: userContent, sourceRole: 'user' } },
    { index: 1, role: 'assistant', payload: { content: assistantContent, refusal: Boolean(message.refusal) } },
  ]
  const fingerprint = hashValue({ model, messages: [{ role: 'user', content: userContent }] })
  const id = hashValue(events)
  return { id, provider: 'groq', model, recordedAt: new Date().toISOString(), fingerprint, events, response: safeResponse, redactions }
}

/** Handle the small JSON contract shared by Vite middleware and Vercel. */
export async function handleDemoRequest(input: unknown, environment: GroqEnvironment): Promise<{ cassette: DemoCassette }> {
  return { cassette: await recordWithGroq(input, environment) }
}
