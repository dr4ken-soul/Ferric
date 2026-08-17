import { AnimatePresence, motion } from 'motion/react'
import { useCallback, useRef, useState } from 'react'
import { siteConfig } from '../../config'
import { useSessionTimecode } from '../../hooks/useSessionTimecode'
import { useModalFocus } from '../../hooks/useModalFocus'

interface NavProps {
  docs?: boolean
  onDocsMenu?: () => void
  onSearch?: () => void
  docsMenuOpen?: boolean
}

const landingLinks = [
  { label: 'Recorder', href: '/#recorder' },
  { label: 'Assertions', href: '/#assertions' },
  { label: 'Docs', href: '/docs' },
]

/** Renders the fixed dual-pill navigation and its accessible mobile overlay. */
export function Nav({ docs = false, docsMenuOpen = false, onDocsMenu, onSearch }: NavProps) {
  const timecodeRef = useRef<HTMLSpanElement>(null)
  const overlayRef = useRef<HTMLDivElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  const [open, setOpen] = useState(false)
  useSessionTimecode(timecodeRef)

  const mobileLinks = landingLinks

  const close = useCallback(() => setOpen(false), [])
  useModalFocus(open, overlayRef, closeRef, close)

  return (
    <>
      <header className="pointer-events-none fixed inset-x-0 top-0 z-[var(--z-nav)] flex items-start justify-between px-4 pt-4 md:px-8 md:pt-6 lg:px-12" data-modal-background>
        <motion.a
          aria-label="Session elapsed time 00 hours, 00 minutes, 00 seconds. Return to top."
          className="pointer-events-auto flex items-center gap-2.5 rounded-full border border-[var(--border-default)] bg-[var(--bg-primary)]/70 px-4 py-2.5 backdrop-blur-xl"
          href={docs ? '/docs' : '#top'}
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
        >
          <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--accent)] animate-record-pulse" />
          <span className="font-mono text-[12px] leading-none tracking-[0.14em] text-[var(--text-primary)] tabular-nums" ref={timecodeRef}>00:00:00</span>
        </motion.a>

        <motion.nav
          aria-label="Primary navigation"
          className="pointer-events-auto hidden items-center gap-1 rounded-full border border-[var(--border-default)] bg-[var(--bg-primary)]/70 px-1.5 py-1.5 backdrop-blur-xl md:flex"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.18 }}
        >
          {docs ? (
            <>
              <button aria-expanded={docsMenuOpen} className="rounded-full px-3.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--text-secondary)] transition-colors duration-[240ms] hover:text-[var(--text-primary)] lg:hidden" onClick={onDocsMenu} type="button">Contents</button>
              <button className="flex items-center gap-2.5 rounded-full px-3.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--text-secondary)] transition-colors duration-[240ms] hover:text-[var(--text-primary)]" onClick={onSearch} type="button">Search <span className="rounded-full border border-[var(--border-default)] px-1.5 py-0.5 text-[9px]">/</span></button>
            </>
          ) : landingLinks.map((link) => (
            <a className="rounded-full px-3.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--text-secondary)] transition-colors duration-[240ms] hover:text-[var(--text-primary)]" href={link.href} key={link.label}>{link.label}</a>
          ))}
          <a className="ml-1 rounded-full bg-[var(--accent)] px-3.5 py-1.5 font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--bg-primary)] transition-colors duration-[240ms] hover:bg-[var(--accent-hover)]" href={siteConfig.repositoryUrl} rel="noreferrer" target="_blank">GitHub</a>
        </motion.nav>

        <motion.button
          aria-expanded={docs ? docsMenuOpen : open}
          aria-label={docs ? 'Open documentation contents' : open ? 'Close navigation' : 'Open navigation'}
          className="pointer-events-auto flex flex-col gap-[5px] rounded-full border border-[var(--border-default)] bg-[var(--bg-primary)]/70 p-3.5 backdrop-blur-xl md:hidden"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={() => docs ? onDocsMenu?.() : setOpen((value) => !value)}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.18 }}
          type="button"
        >
          <span className={`h-[1.5px] w-4 bg-[var(--text-primary)] transition-all duration-[240ms] ${open ? 'translate-y-[6.5px] rotate-45' : ''}`} />
          <span className={`h-[1.5px] w-4 bg-[var(--text-primary)] transition-all duration-[240ms] ${open ? 'opacity-0' : ''}`} />
          <span className={`h-[1.5px] w-4 bg-[var(--text-primary)] transition-all duration-[240ms] ${open ? '-translate-y-[6.5px] -rotate-45' : ''}`} />
        </motion.button>
      </header>

      <AnimatePresence>
        {open && (
          <motion.div
            aria-label="Mobile navigation"
            aria-modal="true"
            className="fixed inset-0 z-[var(--z-overlay)] flex flex-col justify-end bg-[var(--bg-primary)] px-6 pb-20 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            ref={overlayRef}
            role="dialog"
          >
            <button className="absolute right-6 top-6 rounded-full border border-[var(--border-default)] px-4 py-2 font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--text-primary)]" onClick={close} ref={closeRef} type="button">Close</button>
            {mobileLinks.map((link, index) => (
              <motion.a
                className="border-b border-[var(--border-subtle)] py-2 font-display text-5xl font-bold uppercase text-[var(--text-primary)]"
                href={link.href}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                onClick={close}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1], delay: index * 0.06 + 0.08 }}
                key={link.label}
              >
                {link.label}
              </motion.a>
            ))}
            <motion.a
              className="mt-8 w-fit bg-[var(--accent)] px-5 py-3 font-mono text-[12px] font-medium uppercase tracking-[0.14em] text-[var(--bg-primary)]"
              href={siteConfig.repositoryUrl}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              rel="noreferrer"
              target="_blank"
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1], delay: 0.26 }}
            >
              View on GitHub
            </motion.a>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
