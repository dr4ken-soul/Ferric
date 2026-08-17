import { motion } from 'motion/react'
import { useReducedMotion } from '../../hooks/useReducedMotion'
import { Reveal } from '../ui/Reveal'

const statement = 'Every other layer of your stack has tests. The model call does not.'

/** Renders the typographic problem statement with a progressive weight shift. */
export function Untested() {
  const reducedMotion = useReducedMotion().reduced
  return (
    <section className="bg-[var(--bg-secondary)] px-4 py-24 md:px-8 md:py-36 lg:px-12 lg:py-40">
      <div className="mx-auto w-full max-w-[1400px]">
        <h2 className="kinetic-statement max-w-[18ch] text-balance font-display text-[clamp(2.5rem,7vw,6.5rem)] font-bold uppercase leading-[0.92] text-[var(--text-primary)]">
          {statement.split(' ').map((word, index) => (
            <motion.span className="inline-block" initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 40 }} whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }} viewport={{ once: false, amount: 0.2 }} transition={reducedMotion ? { duration: 0.2 } : { duration: 0.55, ease: [0.16, 1, 0.3, 1], delay: index * 0.045 }} key={`${word}-${index}`}>{word}{' '}</motion.span>
          ))}
        </h2>
        <Reveal className="mt-10 max-w-[60ch] font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)] md:mt-14" transition={{ delay: 0.3 }}>Non-deterministic output. No assertion vocabulary. Live calls in CI cost money and flake.</Reveal>
      </div>
    </section>
  )
}
