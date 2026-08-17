import { motion } from 'motion/react'
import { cassetteData } from '../../data/cassettes.generated'
import { useMagneticHover } from '../../hooks/useMagneticHover'
import { useReducedMotion } from '../../hooks/useReducedMotion'
import { BlurText } from '../ui/BlurText'
import { EvidenceSourceBadge } from '../ui/EvidenceSourceBadge'
import { Icon } from '../ui/Icon'
import { Skeleton } from '../ui/Skeleton'

/** Renders the asymmetric first viewport and live cassette readout. */
export function Hero() {
  const motionPreference = useReducedMotion()
  const magnetic = useMagneticHover(motionPreference.reduced || motionPreference.mobile)
  const reducedMotion = motionPreference.reduced
  const data = cassetteData.hero
  const visibleEvents = data.events.slice(0, 5)

  return (
    <section className="relative flex min-h-[100dvh] flex-col overflow-hidden bg-[var(--bg-primary)]" id="top">
      <div aria-hidden="true" className="tech-grid hero-grid-mask absolute inset-0 z-[var(--z-grid)]" />
      <div className="relative z-[var(--z-content)] grid flex-1 grid-cols-1 gap-y-12 px-4 pb-10 pt-[8.5rem] md:px-8 md:pb-14 md:pt-[9.5rem] lg:grid-cols-12 lg:px-12">
        <div className="self-start lg:col-span-7 lg:col-start-1">
          <motion.p className="mb-6 font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)] md:mb-8" initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 10 }} animate={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }} transition={reducedMotion ? { duration: 0.2 } : { duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.25 }}>Record. Replay. Prove it still works.</motion.p>
          <h1 className="max-w-[14ch] text-balance font-display text-[clamp(2.75rem,12vw,8rem)] font-extrabold uppercase leading-[0.86] text-[var(--text-primary)] lg:text-[clamp(3.5rem,9vw,8rem)]">
            <BlurText text="Your AI feature has no test suite" />
          </h1>
          <motion.p className="mt-7 max-w-[52ch] text-pretty font-body text-[15px] leading-[1.6] text-[var(--text-secondary)] md:mt-8 md:text-[17px]" initial={reducedMotion ? { opacity: 0 } : { opacity: 0, filter: 'blur(8px)', y: 18 }} animate={reducedMotion ? { opacity: 1 } : { opacity: 1, filter: 'blur(0px)', y: 0 }} transition={reducedMotion ? { duration: 0.2 } : { duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.72 }}>Record every prompt, tool call and response your agent makes, then replay them in CI with no network and no API spend. Assertions run on the shape of the interaction, not the wording.</motion.p>
          <motion.div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-4" initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 16 }} animate={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }} transition={reducedMotion ? { duration: 0.2 } : { duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.92 }}>
            <motion.a
              className="group relative inline-flex items-center gap-2.5 bg-[var(--accent)] py-1.5 pl-5 pr-1.5 font-mono text-[12px] font-medium uppercase tracking-[0.14em] text-[var(--bg-primary)] transition-colors duration-[240ms] hover:bg-[var(--accent-hover)]"
              href="#recorder"
              onPointerLeave={magnetic.onPointerLeave}
              onPointerMove={magnetic.onPointerMove}
              style={{ x: magnetic.x, y: magnetic.y }}
            >
              See it catch a regression
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[var(--bg-primary)]/10 transition-transform duration-200 group-hover:-translate-y-px group-hover:translate-x-0.5"><Icon className="h-[13px] w-[13px]" name="arrow-up-right" /></span>
            </motion.a>
            <a className="inline-flex items-center gap-2 border-b border-[var(--border-default)] pb-1 font-mono text-[12px] uppercase tracking-[0.14em] text-[var(--text-secondary)] transition-colors duration-[240ms] hover:border-[var(--accent)] hover:text-[var(--text-primary)]" href="/docs">Read the docs</a>
          </motion.div>
        </div>

        <motion.div className="w-full max-w-[420px] self-end justify-self-end lg:col-span-5 lg:col-start-8 lg:mt-auto" initial={reducedMotion ? { opacity: 0 } : { opacity: 0, filter: 'blur(10px)', y: 26 }} animate={reducedMotion ? { opacity: 1 } : { opacity: 1, filter: 'blur(0px)', y: 0 }} transition={reducedMotion ? { duration: 0.2 } : { duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 1.05 }}>
          <div className="border border-[var(--border-strong)] bg-[var(--bg-secondary)]/90">
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] px-4 py-2.5">
              <div className="flex items-center gap-2.5"><span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] animate-record-pulse" /><span className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-secondary)]">Evidence</span></div>
              {data.available ? <span className="font-mono text-[10px] text-[var(--text-muted)]">cassette {data.cassetteId}</span> : <span className="h-2 w-20 bg-[var(--bg-elevated)]" />}
            </div>
            {data.available ? (
              <>
                <EvidenceSourceBadge className="border-b border-[var(--border-subtle)] px-4 py-2.5" source={data.evidenceSource} />
                <div className="grid grid-cols-2 divide-x divide-[var(--border-subtle)] border-b border-[var(--border-subtle)] sm:grid-cols-3">
                  {[['Provider', data.provider], ['Model', data.model], ['Events', data.eventCount]].map(([label, value], index) => (
                    <div className={`px-4 py-3 ${index === 2 ? 'hidden sm:block' : ''}`} key={label}>
                      <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]">{label}</p>
                      <p className="mt-1.5 truncate font-mono text-[13px] text-[var(--text-primary)] tabular-nums">{value}</p>
                    </div>
                  ))}
                </div>
                <div>
                  {visibleEvents.map((event, index) => (
                    <motion.div className={`items-baseline gap-3 border-b border-[var(--border-subtle)] px-4 py-2 last:border-0 ${index > 2 ? 'hidden sm:flex' : 'flex'}`} initial={reducedMotion ? { opacity: 0 } : { opacity: 0, x: -10 }} animate={reducedMotion ? { opacity: 1 } : { opacity: 1, x: 0 }} transition={reducedMotion ? { duration: 0.2 } : { duration: 0.34, delay: 1.35 + index * 0.11 }} key={`${event.index}-${event.role}`}>
                      <span className="w-5 shrink-0 font-mono text-[10px] text-[var(--text-muted)] tabular-nums">{String(event.index).padStart(2, '0')}</span>
                      <span className={`truncate font-mono text-[12px] ${index === visibleEvents.length - 1 ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}`}>{event.role} {event.summary}</span>
                    </motion.div>
                  ))}
                </div>
                <div className="flex items-center justify-between border-t border-[var(--border-subtle)] px-4 py-2.5 font-mono text-[10px] text-[var(--text-secondary)]"><span>written to tests/cassettes/</span><span>{data.redactionCount} recorded redactions</span></div>
              </>
            ) : <Skeleton className="p-4" lines={5} />}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
