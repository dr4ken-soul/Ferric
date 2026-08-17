import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { motion } from 'motion/react'
import { useLayoutEffect, useRef, useState } from 'react'
import { cassetteData, type DisplayEvent } from '../../data/cassettes.generated'
import { useReducedMotion } from '../../hooks/useReducedMotion'
import { EvidenceSourceBadge } from '../ui/EvidenceSourceBadge'
import { Skeleton } from '../ui/Skeleton'

interface PhasePanelProps {
  phase: 'record' | 'replay' | 'drift'
  events: DisplayEvent[]
}

const phases = [
  { key: 'record', number: '01', label: 'Record' },
  { key: 'replay', number: '02', label: 'Replay' },
  { key: 'drift', number: '03', label: 'Drift' },
] as const

/** Renders one recorder phase using generated cassette evidence. */
function PhasePanel({ phase, events }: PhasePanelProps) {
  const drift = cassetteData.drift
  const replay = cassetteData.replay
  const copy = {
    record: {
      label: 'Capture mode',
      heading: 'One line, then it listens',
      body: 'Wrap the client you already have. Every request is forwarded untouched and the normalised event log is captured on the way back. Secrets are stripped before anything reaches disk.',
      command: 'client = ferric.wrap(client)',
      accent: 'ferric.wrap',
    },
    replay: {
      label: 'In CI',
      heading: 'Same events, no network',
      body: 'Replay serves the recorded response and never opens a socket to a provider. An unmatched request fails loudly with the nearest cassette printed. It never falls through to the live model.',
      command: 'FERRIC_MODE=replay pytest',
      accent: 'replay',
    },
    drift: {
      label: 'Drift comparison',
      heading: 'The upgrade that would have shipped',
      body: 'Run the whole cassette library against a new model version. Each cassette is classified as unchanged, reworded, or behaviourally changed, with the moved dimension named.',
      command: 'ferric drift --to <model>',
      accent: 'drift',
    },
  }[phase]

  const commandParts = copy.command.split(copy.accent)

  return (
    <div className="grid border border-[var(--border-default)] bg-[var(--bg-secondary)] lg:grid-cols-2 lg:divide-x lg:divide-[var(--border-default)]">
      <div className="flex min-h-64 flex-col px-6 py-6 md:px-8">
        <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]">{copy.label}</p>
        <h3 className="mt-3 font-body text-[18px] font-medium text-[var(--text-primary)]">{copy.heading}</h3>
        <p className="mt-3 max-w-[46ch] font-body text-[14px] leading-[1.6] text-[var(--text-secondary)]">{copy.body}</p>
        <code className="mt-auto border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-3 font-mono text-[12px] text-[var(--text-secondary)]">{commandParts[0]}<span className="text-[var(--accent)]">{copy.accent}</span>{commandParts[1]}</code>
      </div>
      <div className="relative min-h-64 border-t border-[var(--border-default)] px-6 py-6 font-mono text-[12px] lg:border-t-0 md:px-8">
        {phase === 'record' && <EvidenceSourceBadge className="mb-5" source={cassetteData.hero.evidenceSource} />}
        {phase === 'replay' && <EvidenceSourceBadge className="mb-5" source={replay.evidenceSource} />}
        {phase === 'drift' && <EvidenceSourceBadge className="mb-5" source={drift.evidenceSource} />}
        {phase === 'record' && <span aria-hidden="true" className="absolute right-6 top-6 h-1.5 w-1.5 rounded-full bg-[var(--accent)] animate-record-pulse" />}
        {phase === 'replay' && <span className="absolute right-6 top-5 border border-[var(--border-default)] px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-secondary)]">Replay</span>}
        {phase !== 'drift' && cassetteData.hero.available ? (
          <div className="pr-16">
            {events.slice(0, 6).map((event) => (
              <div className="flex gap-3 border-b border-[var(--border-subtle)] py-1.5 last:border-0" key={`${phase}-${event.index}`}><span className="w-5 text-[var(--text-muted)] tabular-nums">{String(event.index).padStart(2, '0')}</span><span className="truncate text-[var(--text-secondary)]">{event.role} {event.summary}</span></div>
            ))}
          </div>
        ) : phase !== 'drift' ? <Skeleton className="mt-8" lines={6} /> : null}

        {phase === 'replay' && (replay.available ? (
          <p className="absolute inset-x-6 bottom-3 border-t border-[var(--border-subtle)] py-2.5 text-[11px] text-[var(--text-muted)]">{replay.networkCalls} network calls · {replay.tokens} tokens · {replay.durationMs}ms</p>
        ) : <Skeleton className="absolute inset-x-6 bottom-5" lines={1} />)}

        {phase === 'drift' && (drift.available && drift.divergence ? (
          <div>
            {drift.rows.slice(0, 3).map((row) => {
              const diverged = row.classification === 'diverged'
              return (
                <div className={`grid grid-cols-[1fr_auto] items-baseline gap-4 border-b border-[var(--border-subtle)] py-2 last:border-0 ${diverged ? 'border-l-2 border-l-[var(--signal-fail)] bg-[var(--signal-fail-soft)] pl-3' : ''}`} key={row.cassetteId}>
                  <span className={diverged ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}>cassette {row.cassetteId} · {row.dimension || 'interaction shape'}</span>
                  <span className={`text-[10px] uppercase tracking-[0.2em] ${diverged ? 'text-[var(--signal-fail)]' : 'text-[var(--text-muted)]'}`}>{diverged ? 'Diverged' : 'Match'}</span>
                </div>
              )
            })}
            <div className="mt-6 text-[var(--text-muted)]"><p>expected&nbsp; {drift.divergence.expected}</p><p>observed&nbsp; {drift.divergence.observed}</p></div>
            <p className="absolute inset-x-6 bottom-3 border-t border-[var(--border-subtle)] py-2.5 text-[11px] text-[var(--signal-fail)]">{drift.regressionCount} behavioural regression across {drift.cassetteCount} cassettes</p>
          </div>
        ) : <Skeleton className="mt-5" lines={5} />)}
      </div>
    </div>
  )
}

/** Runs the desktop pinned recorder narrative and renders a mobile or reduced-motion fallback. */
export function Recorder() {
  const sectionRef = useRef<HTMLElement>(null)
  const stageRef = useRef<HTMLDivElement>(null)
  const panelRefs = useRef<Array<HTMLDivElement | null>>([])
  const progressRefs = useRef<Array<HTMLSpanElement | null>>([])
  const [activePhase, setActivePhase] = useState(0)
  const preference = useReducedMotion()
  const fallback = !preference.ready || preference.reduced || preference.mobile

  useLayoutEffect(() => {
    if (fallback || !sectionRef.current || !stageRef.current) return
    gsap.registerPlugin(ScrollTrigger)
    const panels = panelRefs.current
    const bars = progressRefs.current
    gsap.set(panels[0], { opacity: 1, y: 0 })
    gsap.set(panels.slice(1), { opacity: 0, y: 28 })
    gsap.set(bars, { scaleX: 0, transformOrigin: 'left center' })

    const timeline = gsap.timeline({
      scrollTrigger: {
        trigger: sectionRef.current,
        start: 'top top',
        end: 'bottom bottom',
        scrub: 1,
        pin: stageRef.current,
        anticipatePin: 1,
        toggleActions: 'play none none reverse',
      },
    })
    phases.forEach((_, index) => {
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: () => `top+=${(sectionRef.current!.scrollHeight - window.innerHeight) * (index / 3)} top`,
        end: () => `top+=${(sectionRef.current!.scrollHeight - window.innerHeight) * ((index + 1) / 3)} top`,
        onEnter: () => setActivePhase(index),
        onEnterBack: () => setActivePhase(index),
      })
    })
    timeline
      .to(bars[0], { scaleX: 1, duration: 0.85 }, 0)
      .to(panels[0], { opacity: 0, y: -22, duration: 0.15 }, 0.85)
      .to(panels[1], { opacity: 1, y: 0, duration: 0.15 }, 0.85)
      .to(bars[1], { scaleX: 1, duration: 0.85 }, 1)
      .to(panels[1], { opacity: 0, y: -22, duration: 0.15 }, 1.85)
      .to(panels[2], { opacity: 1, y: 0, duration: 0.15 }, 1.85)
      .to(bars[2], { scaleX: 1, duration: 0.7 }, 2)
      .to({}, { duration: 0.3 }, 2.7)

    return () => {
      timeline.kill()
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill())
    }
  }, [fallback])

  if (fallback) {
    return (
      <section className="bg-[var(--bg-primary)] px-4 py-24 md:px-8 lg:px-12" id="recorder" ref={sectionRef}>
        <div className="mx-auto max-w-[1400px]">
          <h2 className="font-display text-[clamp(1.75rem,3.5vw,3rem)] font-bold uppercase leading-[0.95] text-[var(--text-primary)]">The recorder</h2>
          <motion.div className="mt-10 flex flex-col gap-6" initial="hidden" whileInView="shown" viewport={{ once: false, amount: 0.1 }} variants={{ hidden: {}, shown: { transition: { staggerChildren: preference.reduced ? 0 : 0.12 } } }}>
            {phases.map((phase) => (
              <motion.div variants={preference.reduced ? { hidden: { opacity: 0 }, shown: { opacity: 1, transition: { duration: 0.2 } } } : { hidden: { opacity: 0, filter: 'blur(10px)', y: 24 }, shown: { opacity: 1, filter: 'blur(0px)', y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } } }} key={phase.key}>
                <p className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)]">{phase.number} {phase.label}</p>
                <PhasePanel events={cassetteData.hero.events} phase={phase.key} />
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>
    )
  }

  return (
    <section className="relative h-[400vh] bg-[var(--bg-primary)]" id="recorder" ref={sectionRef}>
      <div className="sticky top-0 flex h-[100dvh] flex-col justify-center overflow-hidden px-4 md:px-8 lg:px-12" ref={stageRef}>
        <div aria-hidden="true" className="scanlines absolute inset-0 z-[var(--z-grid)]" />
        <div className="relative z-[var(--z-content)] mx-auto mb-10 w-full max-w-[1400px] md:mb-14">
          <h2 className="font-display text-[clamp(1.75rem,3.5vw,3rem)] font-bold uppercase leading-[0.95] text-[var(--text-primary)]">The recorder</h2>
          <div className="mt-6 flex border-t border-[var(--border-subtle)]">
            {phases.map((phase, index) => (
              <div className="relative flex-1 border-r border-[var(--border-subtle)] pt-4 last:border-r-0" data-active={activePhase === index} key={phase.key}>
                <span className="absolute inset-x-0 top-0 h-px origin-left bg-[var(--accent)]" ref={(node) => { progressRefs.current[index] = node }} />
                <p className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)]">{phase.number}</p>
                <p className={`mt-1.5 font-mono text-[11px] uppercase tracking-[0.16em] transition-colors duration-[240ms] ${activePhase === index ? 'text-[var(--accent)]' : 'text-[var(--text-muted)]'}`}>{phase.label}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="relative z-[var(--z-content)] mx-auto h-[min(52vh,460px)] w-full max-w-[1400px]">
          {phases.map((phase, index) => (
            <div className="absolute inset-0" ref={(node) => { panelRefs.current[index] = node }} key={phase.key}><PhasePanel events={cassetteData.hero.events} phase={phase.key} /></div>
          ))}
        </div>
      </div>
    </section>
  )
}
