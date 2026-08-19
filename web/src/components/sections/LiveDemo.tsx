import { useState } from 'react'
import { Icon } from '../ui/Icon'

interface DemoEvent {
  index: number
  role: string
  payload: { content?: unknown; refusal?: boolean }
}

interface DemoCassette {
  id: string
  model: string
  events: DemoEvent[]
  response: { choices?: Array<{ message?: { content?: unknown } }> }
  redactions: Array<{ ruleClass: string }>
}

/** Render the live Groq recording and browser-local replay demonstration. */
export function LiveDemo() {
  const [prompt, setPrompt] = useState('Explain why a model upgrade should be tested before release.')
  const [cassette, setCassette] = useState<DemoCassette | null>(null)
  const [status, setStatus] = useState<'idle' | 'recording' | 'replayed' | 'error'>('idle')
  const [message, setMessage] = useState('No cassette recorded in this session.')
  const [replayText, setReplayText] = useState<string | null>(null)

  /** Send one prompt to the server-side Groq recorder. */
  async function recordInteraction() {
    setStatus('recording')
    setMessage('Calling Groq through the Ferric recorder...')
    setReplayText(null)
    try {
      const response = await fetch('/api/ferric', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ prompt }),
      })
      const payload = await response.json() as { cassette?: DemoCassette; error?: string }
      if (!response.ok || !payload.cassette) throw new Error(payload.error || 'The recorder returned no cassette.')
      setCassette(payload.cassette)
      setStatus('idle')
      setMessage(`Recorded ${payload.cassette.events.length} events in cassette ${payload.cassette.id.slice(0, 8)}.`)
    } catch (error) {
      setStatus('error')
      setMessage(error instanceof Error ? error.message : 'The live recorder failed.')
    }
  }

  /** Replay the stored response without making a second network request. */
  function replayInteraction() {
    if (!cassette) return
    const content = cassette.response.choices?.[0]?.message?.content
    setReplayText(typeof content === 'string' ? content : JSON.stringify(content))
    setStatus('replayed')
    setMessage(`Replayed cassette ${cassette.id.slice(0, 8)} locally. Groq was not called.`)
  }

  const assistantContent = cassette?.events.find((event) => event.role === 'assistant')?.payload.content
  const visibleResponse = replayText || (typeof assistantContent === 'string' ? assistantContent : null)

  return (
    <section className="border-y border-[var(--border-default)] bg-[var(--bg-secondary)] px-4 py-24 md:px-8 md:py-32 lg:px-12" id="live-demo">
      <div className="mx-auto max-w-[1400px]">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)]">Live recorder</p>
            <h2 className="mt-5 max-w-[16ch] font-display text-[clamp(2.25rem,5vw,4.5rem)] font-extrabold uppercase leading-[0.9] text-[var(--text-primary)]">Record it once. Replay it here.</h2>
          </div>
          <p className="max-w-[48ch] font-body text-[15px] leading-[1.6] text-[var(--text-secondary)]">This deployed demo calls Groq on record, returns a readable cassette, then replays the stored response in your browser without calling the model again.</p>
        </div>

        <div className="mt-12 grid border border-[var(--border-default)] lg:grid-cols-[5fr_7fr] lg:divide-x lg:divide-[var(--border-default)]">
          <div className="p-6 md:p-8">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]" htmlFor="live-prompt">Prompt sent to Groq</label>
            <textarea className="mt-4 min-h-36 w-full resize-y border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 font-body text-[15px] leading-[1.6] text-[var(--text-primary)] outline-none transition-colors placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]" id="live-prompt" maxLength={1000} onChange={(event) => setPrompt(event.target.value)} value={prompt} />
            <div className="mt-5 flex flex-wrap gap-3">
              <button className="inline-flex items-center gap-2.5 bg-[var(--accent)] px-5 py-3 font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--bg-primary)] transition-colors duration-[240ms] hover:bg-[var(--accent-hover)] disabled:cursor-wait disabled:opacity-60" disabled={status === 'recording' || !prompt.trim()} onClick={recordInteraction} type="button">
                {status === 'recording' ? 'Recording' : 'Record with Groq'} <Icon className="h-3.5 w-3.5" name="record" />
              </button>
              <button className="inline-flex items-center gap-2.5 border border-[var(--border-default)] px-5 py-3 font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--text-secondary)] transition-colors duration-[240ms] hover:border-[var(--accent)] hover:text-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-40" disabled={!cassette || status === 'recording'} onClick={replayInteraction} type="button">
                Replay locally <Icon className="h-3.5 w-3.5" name="play" />
              </button>
            </div>
            <p aria-live="polite" className={`mt-5 font-mono text-[11px] leading-[1.5] ${status === 'error' ? 'text-[var(--signal-fail)]' : 'text-[var(--text-secondary)]'}`}>{message}</p>
          </div>

          <div className="border-t border-[var(--border-default)] bg-[var(--bg-primary)] p-6 md:p-8 lg:border-t-0">
            {cassette ? (
              <>
                <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--text-muted)]"><span>Cassette {cassette.id.slice(0, 8)}</span><span>{cassette.model}</span></div>
                <div className="py-4 font-mono text-[12px]">
                  {cassette.events.map((event) => <div className="flex gap-3 border-b border-[var(--border-subtle)] py-2 last:border-0" key={event.index}><span className="w-5 shrink-0 text-[var(--text-muted)]">{String(event.index).padStart(2, '0')}</span><span className="text-[var(--text-secondary)]">{event.role} {typeof event.payload.content === 'string' ? event.payload.content : ''}</span></div>)}
                </div>
                {visibleResponse && <div className="border-l-2 border-[var(--accent)] bg-[var(--accent-glow)] px-4 py-3 font-body text-[14px] leading-[1.6] text-[var(--text-primary)]">{visibleResponse}</div>}
                <div className="mt-5 flex justify-between border-t border-[var(--border-subtle)] pt-4 font-mono text-[10px] text-[var(--text-secondary)]"><span>{cassette.redactions.length} redactions</span><span>{status === 'replayed' ? 'replay: no network' : 'recorded from Groq'}</span></div>
              </>
            ) : <div className="flex min-h-64 items-center justify-center border border-dashed border-[var(--border-default)] font-mono text-[11px] uppercase tracking-[0.16em] text-[var(--text-muted)]">Cassette appears after record</div>}
          </div>
        </div>
      </div>
    </section>
  )
}
