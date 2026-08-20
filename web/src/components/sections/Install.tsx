import { siteConfig } from '../../config'
import { CopyButton } from '../ui/CopyButton'
import { Icon } from '../ui/Icon'
import { Reveal } from '../ui/Reveal'

const installCommand = 'git clone https://github.com/dr4ken-soul/Ferric.git && cd Ferric\npython -m pip install -e .'

/** Renders installation commands and repository actions. */
export function Install() {
  const demoDisabled = !siteConfig.demoUrl
  return (
    <section className="border-t border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-24 md:px-8 md:py-32 lg:px-12">
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 items-end gap-10 lg:grid-cols-12 lg:gap-8">
        <Reveal className="lg:col-span-7">
          <h2 className="max-w-[16ch] text-balance font-display text-[clamp(2.25rem,5vw,4.5rem)] font-extrabold uppercase leading-[0.9] text-[var(--text-primary)]">Runs offline. No key required.</h2>
          <p className="mt-6 max-w-[52ch] font-body text-[15px] leading-[1.6] text-[var(--text-secondary)]">Run the offline suite with no provider account, or use the hosted interaction demo above with a Groq key configured on your own deployment.</p>
        </Reveal>
        <Reveal className="lg:col-span-5" transition={{ delay: 0.15 }}>
          <div className="group flex items-center justify-between gap-4 border border-[var(--border-strong)] bg-[var(--bg-secondary)] py-4 pl-5 pr-2">
            <code className="min-w-0 break-all whitespace-pre-wrap font-mono text-[13px] text-[var(--text-primary)] md:text-[14px]">git clone https://github.com/dr4ken-soul/Ferric.git && cd Ferric{`\n`}python -m pip install -e .</code>
            <CopyButton value={installCommand} />
          </div>
          <p className="mt-3 flex items-center gap-3 font-mono text-[12px] text-[var(--text-secondary)]">then&nbsp; FERRIC_MODE=replay pytest</p>
          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
            <a className="inline-flex items-center gap-2.5 bg-[var(--accent)] px-5 py-3 font-mono text-[12px] font-medium uppercase tracking-[0.14em] text-[var(--bg-primary)] transition-colors duration-[240ms] hover:bg-[var(--accent-hover)]" href={siteConfig.repositoryUrl} rel="noreferrer" target="_blank">View on GitHub <Icon className="h-3.5 w-3.5" name="arrow-up-right" /></a>
            <a aria-disabled={demoDisabled} className={`inline-flex items-center gap-2 border-b border-[var(--border-default)] pb-1 font-mono text-[12px] uppercase tracking-[0.14em] text-[var(--text-secondary)] transition-colors duration-[240ms] hover:border-[var(--accent)] hover:text-[var(--text-primary)] ${demoDisabled ? 'pointer-events-none opacity-50' : ''}`} href={demoDisabled ? undefined : siteConfig.demoUrl}>Watch the demo <Icon className="h-3.5 w-3.5" name="play" /></a>
          </div>
        </Reveal>
      </div>
    </section>
  )
}
