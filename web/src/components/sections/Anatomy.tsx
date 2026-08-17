import { motion, type Variants } from 'motion/react'
import type { ReactNode } from 'react'
import { cassetteData } from '../../data/cassettes.generated'
import { useReducedMotion } from '../../hooks/useReducedMotion'
import { Skeleton } from '../ui/Skeleton'
import { Reveal } from '../ui/Reveal'

const bands = ['metadata', 'fingerprint', 'request', 'tool calls', 'response', 'redactions']

/** Renders the generated cassette anatomy and its six-cell blueprint grid. */
export function Anatomy() {
  const hero = cassetteData.hero
  const library = cassetteData.library
  const reducedMotion = useReducedMotion().reduced
  const cellVariant: Variants = reducedMotion
    ? { hidden: { opacity: 0 }, shown: { opacity: 1, transition: { duration: 0.2 } } }
    : { hidden: { opacity: 0, filter: 'blur(8px)', y: 20 }, shown: { opacity: 1, filter: 'blur(0px)', y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } } }
  const cellClass = 'relative bg-[var(--bg-primary)] p-6 transition-colors duration-[240ms] hover:bg-[var(--bg-surface)] md:p-8'

  return (
    <section className="relative overflow-hidden bg-[var(--bg-secondary)] px-4 py-24 md:px-8 md:py-36 lg:px-12">
      <div aria-hidden="true" className="tech-grid anatomy-grid-mask absolute inset-0 z-[var(--z-grid)]" />
      <div className="relative z-[var(--z-content)] mx-auto max-w-[1400px]">
        <Reveal><h2 className="max-w-[22ch] text-balance font-display text-[clamp(2rem,4.5vw,3.75rem)] font-bold uppercase leading-[0.94] text-[var(--text-primary)]">A cassette is a file you can read in a pull request</h2></Reveal>
        <motion.div className="mt-12 grid grid-cols-1 gap-px border border-[var(--border-default)] bg-[var(--border-default)] md:mt-16 lg:grid-cols-12" initial="hidden" whileInView="shown" viewport={{ once: false, amount: 0.1 }} variants={{ hidden: {}, shown: { transition: { staggerChildren: reducedMotion ? 0 : 0.07 } } }}>
          <motion.div className={`${cellClass} lg:col-span-7 lg:row-span-2`} variants={cellVariant}>
            <CornerTick />
            {hero.available ? (
              <>
                <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]">Cassette {hero.cassetteId}</p>
                <svg aria-labelledby="cassette-diagram-title" className="mt-6 h-auto w-full" viewBox="0 0 600 420">
                  <title id="cassette-diagram-title">Annotated cassette event structure</title>
                  <line stroke="var(--border-default)" x1="35" x2="35" y1="58" y2="354" />
                  <line stroke="var(--border-default)" x1="26" x2="44" y1="58" y2="58" />
                  <line stroke="var(--border-default)" x1="26" x2="44" y1="354" y2="354" />
                  <text fill="var(--text-muted)" fontFamily="Martian Mono" fontSize="10" transform="rotate(-90 18 235)" x="18" y="235">{hero.eventCount} EVENTS</text>
                  {bands.map((band, index) => {
                    const y = 58 + index * 50
                    const highlighted = band === 'fingerprint'
                    return (
                      <g key={band}>
                        <rect fill="var(--bg-surface)" height="36" stroke={highlighted ? 'var(--accent)' : 'var(--border-default)'} width="330" x="64" y={y} />
                        <text fill={highlighted ? 'var(--accent)' : 'var(--text-secondary)'} fontFamily="Martian Mono" fontSize="10" letterSpacing="1.6" x="80" y={y + 22}>{String(index + 1).padStart(2, '0')} {band.toUpperCase()}</text>
                        <motion.path className="cassette-leader" d={`M394 ${y + 18} H455 L475 ${y + 9}`} fill="none" initial={{ strokeDashoffset: reducedMotion ? 0 : 120 }} stroke="var(--accent)" strokeDasharray="120" strokeOpacity="0.5" strokeWidth="1" whileInView={reducedMotion ? undefined : { strokeDashoffset: 0 }} viewport={{ once: false, amount: 0.3 }} transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: index * 0.08 }} />
                        <g className="diagram-side-label"><text fill="var(--text-muted)" fontFamily="Martian Mono" fontSize="9" letterSpacing="1.3" x="480" y={y + 12}>{band.toUpperCase()}</text></g>
                      </g>
                    )
                  })}
                </svg>
                <div className="diagram-band-list mt-4 hidden grid-cols-2 gap-x-4 gap-y-2 border-t border-[var(--border-subtle)] pt-4 sm:hidden">
                  {bands.map((band, index) => <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[var(--text-secondary)]" key={band}>{String(index + 1).padStart(2, '0')} {band}</p>)}
                </div>
              </>
            ) : <Skeleton className="mt-6" lines={8} />}
          </motion.div>
          <AnatomyCell className="lg:col-span-5" label="On disk" variant={cellVariant}><p>One interaction per file, plain JSON, content-hashed identifier. A cassette diff is readable in review, which is the reason it is not a binary format.</p></AnatomyCell>
          <AnatomyCell className="lg:col-span-5" label="Matching" variant={cellVariant}><p>The request fingerprint is built from the model, normalised messages, and tool definitions in scope. Volatile timestamps and request identifiers are excluded.</p></AnatomyCell>
          <AnatomyCell className="lg:col-span-4" label="Redaction" variant={cellVariant}>{library.available ? <><p className="font-mono text-[clamp(1.5rem,2.5vw,2rem)] text-[var(--text-primary)] tabular-nums">{library.redactionRuleCount} recorded rule classes</p><p className="mt-2 text-[13px]">Derived from redaction records in the cassette library.</p></> : <Skeleton lines={2} />}</AnatomyCell>
          <AnatomyCell className="lg:col-span-4" label="Adapters" variant={cellVariant}>{library.available ? <><p className="font-mono text-[clamp(1.5rem,2.5vw,2rem)] text-[var(--text-primary)] tabular-nums">{library.providerCount}</p><p className="mt-2 text-[13px]">{library.providers.join(', ')}</p></> : <Skeleton lines={2} />}</AnatomyCell>
          <AnatomyCell className="lg:col-span-4" label="Not yet built" variant={cellVariant}><p className="text-[13px]">Streaming is coalesced into a single assistant message rather than recorded token by token. Embeddings, image and audio endpoints are out of scope.</p></AnatomyCell>
        </motion.div>
      </div>
    </section>
  )
}

/** Draws the hard-corner registration mark shared by anatomy cells. */
function CornerTick() {
  return <><span aria-hidden="true" className="absolute left-0 top-0 h-px w-2 bg-[var(--border-strong)]" /><span aria-hidden="true" className="absolute left-0 top-0 h-2 w-px bg-[var(--border-strong)]" /></>
}

interface AnatomyCellProps {
  label: string
  className: string
  children: ReactNode
  variant: Variants
}

/** Renders one flat anatomy cell without introducing a nested card. */
function AnatomyCell({ label, className, children, variant }: AnatomyCellProps) {
  return (
    <motion.div className={`relative bg-[var(--bg-primary)] p-6 transition-colors duration-[240ms] hover:bg-[var(--bg-surface)] md:p-8 ${className}`} variants={variant}>
      <CornerTick />
      <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]">{label}</p>
      <div className="mt-4 max-w-[42ch] font-body text-[14px] leading-[1.65] text-[var(--text-secondary)]">{children}</div>
    </motion.div>
  )
}
