import { AnimatePresence, motion, type Variants } from 'motion/react'
import { useRef, useState } from 'react'
import { cassetteData, type AssertionFamily } from '../../data/cassettes.generated'
import { useReducedMotion } from '../../hooks/useReducedMotion'
import { EvidenceSourceBadge } from '../ui/EvidenceSourceBadge'
import { Skeleton } from '../ui/Skeleton'

const assertionCopy: Record<AssertionFamily, { label: string; title: string; body: string; catches: string }> = {
  sequence: { label: 'Sequence', title: 'Tool call order', body: 'Compares the observed sequence of tool names against the expected sequence and reports the first point of divergence, not just that something differed.', catches: 'an agent that calls tools in a new order after a prompt edit' },
  arguments: { label: 'Arguments', title: 'Critical field matching', body: 'Exact match on the argument fields you declare as critical, with everything else ignored. A reworded query string does not fail the test, but a wrong account identifier does.', catches: 'an argument that silently changed type or lost a field' },
  schema: { label: 'Schema', title: 'Structured output validity', body: 'Validates the response against the JSON schema you declared and reports the failing path rather than a bare boolean.', catches: 'a model that starts wrapping its JSON in prose' },
  leakage: { label: 'Leakage', title: 'Redaction enforcement', body: 'Fails the test if any declared pattern appears in an outbound request. It also runs on the write path, so a secret never reaches a cassette on disk.', catches: 'a prompt template that started interpolating a raw key' },
}

/** Renders all four live assertion families as an accessible tab interface. */
export function Assertions() {
  const [active, setActive] = useState<AssertionFamily>('sequence')
  const reducedMotion = useReducedMotion().reduced
  const tabRefs = useRef<Record<AssertionFamily, HTMLButtonElement | null>>({ sequence: null, arguments: null, schema: null, leakage: null })
  const selected = assertionCopy[active]
  const result = cassetteData.assertions[active]
  const tabKeys = Object.keys(assertionCopy) as AssertionFamily[]
  const itemVariants: Variants = reducedMotion
    ? { hidden: { opacity: 0 }, shown: { opacity: 1, transition: { duration: 0.2 } } }
    : { hidden: { opacity: 0, filter: 'blur(10px)', y: 24 }, shown: { opacity: 1, filter: 'blur(0px)', y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } } }

  const moveTab = (index: number) => {
    const next = tabKeys[(index + tabKeys.length) % tabKeys.length]
    setActive(next)
    requestAnimationFrame(() => tabRefs.current[next]?.focus())
  }

  return (
    <section className="bg-[var(--bg-primary)] px-4 py-24 md:px-8 md:py-32 lg:px-12" id="assertions">
      <div className="mx-auto max-w-[1400px]">
        <motion.div initial="hidden" whileInView="shown" viewport={{ once: false, amount: 0.1 }} variants={{ hidden: {}, shown: { transition: { staggerChildren: reducedMotion ? 0 : 0.08 } } }}>
          {[
            <p className="mb-5 font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)]" key="eyebrow">Assertions</p>,
            <h2 className="max-w-[20ch] text-balance font-display text-[clamp(2rem,4.5vw,3.75rem)] font-bold uppercase leading-[0.94] text-[var(--text-primary)]" key="heading">String equality was never going to work</h2>,
            <p className="mt-5 max-w-[58ch] font-body text-[15px] leading-[1.6] text-[var(--text-secondary)] md:text-[16px]" key="body">Four assertion families that survive non-determinism. Each one fails on a real regression and stays quiet when the model simply reworded itself.</p>,
          ].map((element) => <motion.div variants={itemVariants} key={element.key}>{element}</motion.div>)}
        </motion.div>
        <div className="mobile-tab-mask mt-12 flex overflow-x-auto border-b border-[var(--border-default)] md:mt-16 lg:[mask-image:none]" role="tablist" aria-label="Assertion families">
          {tabKeys.map((key, index) => (
            <button aria-controls="assertion-panel" aria-selected={active === key} className={`relative whitespace-nowrap border-r border-[var(--border-subtle)] px-5 py-4 font-mono text-[11px] uppercase tracking-[0.16em] transition-colors duration-[240ms] last:border-r-0 md:px-7 ${active === key ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`} id={`assertion-${key}`} onClick={() => setActive(key)} onKeyDown={(event) => { if (event.key === 'ArrowRight' || event.key === 'ArrowDown') { event.preventDefault(); moveTab(index + 1) } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') { event.preventDefault(); moveTab(index - 1) } else if (event.key === 'Home') { event.preventDefault(); moveTab(0) } else if (event.key === 'End') { event.preventDefault(); moveTab(tabKeys.length - 1) } }} ref={(node) => { tabRefs.current[key] = node }} role="tab" tabIndex={active === key ? 0 : -1} type="button" key={key}>
              {assertionCopy[key].label}
              {active === key && <motion.span className="absolute bottom-[-1px] left-0 right-0 h-[2px] bg-[var(--accent)]" layoutId="assertTab" transition={{ type: 'spring', stiffness: 380, damping: 32 }} />}
            </button>
          ))}
        </div>
        <AnimatePresence mode="wait">
          <motion.div aria-labelledby={`assertion-${active}`} className="grid grid-cols-1 divide-y divide-[var(--border-default)] border border-t-0 border-[var(--border-default)] lg:grid-cols-[5fr_7fr] lg:divide-x lg:divide-y-0" id="assertion-panel" initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 12 }} animate={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }} exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: -8 }} role="tabpanel" transition={reducedMotion ? { duration: 0.2 } : { duration: 0.26, ease: [0.16, 1, 0.3, 1] }} key={active}>
            <div className="flex flex-col px-6 py-8 md:px-10 md:py-12">
              <h3 className="font-body text-[19px] font-medium text-[var(--text-primary)]">{selected.title}</h3>
              <p className="mt-4 max-w-[46ch] font-body text-[14px] leading-[1.65] text-[var(--text-secondary)]">{selected.body}</p>
              <div className="mt-auto pt-8"><p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]">Catches</p><p className="mt-2 font-mono text-[13px] text-[var(--text-primary)]">{selected.catches}</p></div>
            </div>
            <div className="bg-[var(--bg-secondary)] px-6 py-8 font-mono text-[12px] md:px-10 md:py-12">
              <EvidenceSourceBadge className="mb-8" source={result.evidenceSource} />
              {result.available ? result.lines.map((line, index) => (
                <p className={`py-1.5 ${line.kind === 'fail' ? 'border-l-2 border-l-[var(--signal-fail)] bg-[var(--signal-fail-soft)] pl-3 text-[var(--text-primary)]' : line.kind === 'detail' ? 'pl-8 text-[var(--text-muted)]' : 'text-[var(--text-secondary)]'}`} key={`${line.text}-${index}`}><span className={line.kind === 'fail' ? 'text-[var(--signal-fail)]' : 'text-[var(--text-muted)]'}>{line.kind === 'pass' ? '  ok  ' : line.kind === 'fail' ? ' fail ' : '      '}</span>{line.text}</p>
              )) : <Skeleton lines={5} />}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  )
}
