import { motion, type Variants } from 'motion/react'
import { siteConfig } from '../../config'
import { useReducedMotion } from '../../hooks/useReducedMotion'

/** Closes the landing page with product function, links, and attribution. */
export function Footer() {
  const demoDisabled = !siteConfig.demoUrl
  const reducedMotion = useReducedMotion().reduced
  const itemVariants: Variants = reducedMotion
    ? { hidden: { opacity: 0 }, shown: { opacity: 1, transition: { duration: 0.2 } } }
    : { hidden: { opacity: 0, filter: 'blur(10px)', y: 24 }, shown: { opacity: 1, filter: 'blur(0px)', y: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } } }
  return (
    <footer className="border-t border-[var(--border-default)] bg-[var(--bg-primary)] px-4 py-14 md:px-8 md:py-16 lg:px-12" data-modal-background>
      <motion.div className="mx-auto max-w-[1400px]" initial="hidden" whileInView="shown" viewport={{ once: false, amount: 0.1 }} variants={{ hidden: {}, shown: { transition: { staggerChildren: reducedMotion ? 0 : 0.06 } } }}>
        <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
          <motion.p className="max-w-[16ch] font-display text-[clamp(1.5rem,3vw,2.25rem)] font-bold uppercase leading-[0.95] text-[var(--text-primary)]" variants={itemVariants}>A flight recorder for agent traffic.</motion.p>
          <motion.div className="flex flex-col gap-2.5 font-mono text-[12px] uppercase tracking-[0.14em]" variants={itemVariants}>
            <a className="w-fit text-[var(--text-secondary)] transition-colors duration-[240ms] hover:text-[var(--accent)]" href={siteConfig.repositoryUrl} rel="noreferrer" target="_blank">View on GitHub</a>
            <a aria-disabled={demoDisabled} className={`w-fit text-[var(--text-secondary)] transition-colors duration-[240ms] hover:text-[var(--accent)] ${demoDisabled ? 'pointer-events-none opacity-50' : ''}`} href={demoDisabled ? undefined : siteConfig.demoUrl}>Watch the demo</a>
            <a className="w-fit text-[var(--text-secondary)] transition-colors duration-[240ms] hover:text-[var(--accent)]" href="/docs">Read the docs</a>
          </motion.div>
        </div>
        <motion.div className="mt-14 flex flex-col gap-3 border-t border-[var(--border-subtle)] pt-6 md:flex-row md:items-center md:justify-between" variants={itemVariants}>
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]"><span className="text-[var(--text-secondary)]">Ferric</span> · built with Kiro for the Ready, Spec, Ship Hackathon</p>
          <a className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-secondary)] transition-colors duration-[240ms] hover:text-[var(--accent)]" href="#top">Back to top</a>
        </motion.div>
      </motion.div>
    </footer>
  )
}
