import { AnimatePresence, motion } from 'motion/react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { siteConfig } from '../config'
import { Nav } from '../components/layout/Nav'
import { CopyButton } from '../components/ui/CopyButton'
import { GrainOverlay } from '../components/ui/GrainOverlay'
import { allDocTopics, docGroups, type DocTopic } from '../docs/content'
import { useModalFocus } from '../hooks/useModalFocus'

/** Renders one documentation code sample with an accessible copy action. */
function CodeBlock({ code }: { code: NonNullable<DocTopic['code']> }) {
  return (
    <div className="mt-6 overflow-x-auto border border-[var(--border-default)] bg-[var(--bg-secondary)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] px-4 py-2">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]">{code.language}</span>
        <CopyButton value={code.value} />
      </div>
      <pre className="overflow-x-auto px-4 py-4"><code className="font-mono text-[13px] leading-[1.7] text-[var(--text-secondary)]">{code.value}</code></pre>
    </div>
  )
}

/** Renders grouped documentation links for desktop and mobile navigation. */
function DocsLinks({ active, onSelect }: { active?: string; onSelect?: () => void }) {
  return (
    <>
      {docGroups.map((group) => (
        <div className="mt-8 first:mt-0" key={group.slug}>
          <p className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]">{group.label}</p>
          {group.topics.map((topic) => <a className={`block py-1.5 font-body text-[14px] transition-colors duration-[240ms] hover:text-[var(--text-primary)] ${active === topic.slug ? '-ml-[2px] border-l-2 border-[var(--accent)] pl-3 text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}`} href={`#${topic.slug}`} onClick={onSelect} key={topic.slug}>{topic.title}</a>)}
        </div>
      ))}
    </>
  )
}

/** Renders the complete documentation route with responsive navigation and heading tracking. */
export function DocsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeHeading, setActiveHeading] = useState(allDocTopics[0].slug)
  const drawerRef = useRef<HTMLDivElement>(null)
  const drawerCloseRef = useRef<HTMLButtonElement>(null)
  const searchRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const closeDrawer = useCallback(() => setDrawerOpen(false), [])
  const closeSearch = useCallback(() => setSearchOpen(false), [])
  useModalFocus(drawerOpen, drawerRef, drawerCloseRef, closeDrawer)
  useModalFocus(searchOpen, searchRef, searchInputRef, closeSearch)
  const normalisedQuery = query.trim().toLowerCase()
  const results = normalisedQuery ? allDocTopics.filter((topic) => `${topic.group} ${topic.title} ${topic.summary}`.toLowerCase().includes(normalisedQuery)) : allDocTopics

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === '/' && !searchOpen && !(event.target instanceof HTMLInputElement)) {
        event.preventDefault()
        setSearchOpen(true)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [searchOpen])

  useEffect(() => {
    const headings = document.querySelectorAll<HTMLElement>('[data-doc-heading]')
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.find((entry) => entry.isIntersecting)
      if (visible) setActiveHeading(visible.target.id)
    }, { rootMargin: '0px 0px -70% 0px' })
    headings.forEach((heading) => observer.observe(heading))
    return () => observer.disconnect()
  }, [])

  return (
    <div className="min-h-[100dvh] bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <Nav docs docsMenuOpen={drawerOpen} onDocsMenu={() => setDrawerOpen(true)} onSearch={() => setSearchOpen(true)} />
      <GrainOverlay />
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 px-4 pb-20 pt-28 md:px-8 lg:grid-cols-[240px_minmax(0,1fr)] lg:px-12 xl:grid-cols-[240px_minmax(0,1fr)_200px]" data-modal-background>
        <aside aria-label="Documentation sections" className="sticky top-[6.5rem] hidden h-[calc(100dvh-8rem)] overflow-y-auto border-r border-[var(--border-subtle)] pr-8 lg:block"><DocsLinks active={activeHeading} /></aside>
        <main className="min-w-0 max-w-[720px] px-0 py-12 lg:px-12 lg:py-16" id="docs-content">
          <h1 className="text-balance font-display text-[clamp(2rem,4vw,3rem)] font-bold uppercase leading-[0.95] text-[var(--text-primary)]">Documentation</h1>
          <p className="mt-4 max-w-[68ch] text-pretty font-body text-[15px] leading-[1.7] text-[var(--text-secondary)]">Record real model traffic, replay it offline, and assert on interaction behaviour. This reference covers the complete local workflow.</p>
          {docGroups.map((group) => (
            <section key={group.slug}>
              <h2 className="mt-16 border-t border-[var(--border-subtle)] pt-8 font-display text-[1.75rem] font-bold uppercase text-[var(--text-primary)]" id={group.slug}>{group.label}</h2>
              {group.topics.map((topic) => (
                <article className="scroll-mt-28" data-doc-heading id={topic.slug} key={topic.slug}>
                  <h3 className="mt-10 font-body text-[17px] font-medium text-[var(--text-primary)]">{topic.title}</h3>
                  <p className="mt-4 max-w-[68ch] text-pretty font-body text-[15px] font-medium leading-[1.7] text-[var(--text-primary)]">{topic.summary}</p>
                  {topic.paragraphs.map((paragraph) => <p className="mt-4 max-w-[68ch] text-pretty font-body text-[15px] leading-[1.7] text-[var(--text-secondary)]" key={paragraph}>{paragraph}</p>)}
                  {topic.code && <CodeBlock code={topic.code} />}
                  {topic.note && <div className="mt-6 border-l-2 border-[var(--accent)] bg-[var(--accent-glow)] px-5 py-4"><p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)]">Note</p><p className="mt-2 font-body text-[14px] leading-[1.6] text-[var(--text-secondary)]">{topic.note}</p></div>}
                </article>
              ))}
            </section>
          ))}
        </main>
        <aside aria-label="On this page" className="sticky top-[6.5rem] hidden h-fit border-l border-[var(--border-subtle)] pl-8 xl:block">
          <p className="mb-4 font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]">On this page</p>
          {allDocTopics.map((topic) => <a className={`block py-1.5 font-body text-[13px] transition-colors duration-[240ms] ${activeHeading === topic.slug ? 'text-[var(--accent)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`} href={`#${topic.slug}`} key={topic.slug}>{topic.title}</a>)}
        </aside>
      </div>
      <footer className="border-t border-[var(--border-default)] px-4 py-8 md:px-8 lg:px-12" data-modal-background><div className="mx-auto flex max-w-[1400px] flex-wrap justify-between gap-4 font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-secondary)]"><span>Local-first agent testing</span><a className="transition-colors duration-[240ms] hover:text-[var(--accent)]" href={siteConfig.repositoryUrl} rel="noreferrer" target="_blank">View on GitHub</a></div></footer>

      <AnimatePresence>
        {drawerOpen && (
          <motion.div aria-label="Documentation contents" aria-modal="true" className="fixed inset-0 z-[var(--z-modal)] bg-[var(--bg-primary)] px-6 pb-12 pt-24 lg:hidden" initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }} ref={drawerRef} role="dialog" transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}>
            <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-4"><p className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-secondary)]">Contents</p><button className="font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--text-primary)]" onClick={closeDrawer} ref={drawerCloseRef} type="button">Close</button></div>
            <nav aria-label="Mobile documentation sections" className="h-[calc(100dvh-10rem)] overflow-y-auto pt-6"><DocsLinks active={activeHeading} onSelect={closeDrawer} /></nav>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {searchOpen && (
          <motion.div aria-label="Search documentation" aria-modal="true" className="fixed inset-0 z-[var(--z-modal)] flex items-start justify-center bg-[var(--bg-primary)]/95 px-4 pt-24 md:pt-32" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} ref={searchRef} role="dialog" transition={{ duration: 0.2 }}>
            <div className="w-full max-w-[680px] border border-[var(--border-strong)] bg-[var(--bg-secondary)]">
              <div className="flex items-center border-b border-[var(--border-default)]"><label className="sr-only" htmlFor="docs-search">Search documentation</label><input className="min-w-0 flex-1 bg-transparent px-5 py-4 font-mono text-[13px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)]" id="docs-search" onChange={(event) => setQuery(event.target.value)} placeholder="Search topics" ref={searchInputRef} value={query} /><button className="border-l border-[var(--border-default)] px-5 py-4 font-mono text-[10px] uppercase tracking-[0.14em] text-[var(--text-secondary)] hover:text-[var(--text-primary)]" onClick={closeSearch} type="button">Close</button></div>
              <div className="max-h-[55dvh] overflow-y-auto p-2">
                {results.map((topic) => <a className="block border-b border-[var(--border-subtle)] px-4 py-3 transition-colors duration-[240ms] last:border-b-0 hover:bg-[var(--bg-surface)]" href={`#${topic.slug}`} onClick={() => { setSearchOpen(false); setQuery('') }} key={topic.slug}><span className="font-mono text-[9px] uppercase tracking-[0.18em] text-[var(--text-muted)]">{topic.group}</span><span className="mt-1 block font-body text-[14px] text-[var(--text-primary)]">{topic.title}</span></a>)}
                {results.length === 0 && <p className="px-4 py-8 font-body text-[14px] text-[var(--text-muted)]">No matching documentation topic.</p>}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
