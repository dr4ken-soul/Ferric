import type { EvidenceSource } from '../../data/cassettes.generated'

interface EvidenceSourceBadgeProps {
  source: EvidenceSource
  className?: string
}

/** Makes cassette origin explicit wherever generated evidence is shown. */
export function EvidenceSourceBadge({ source, className = '' }: EvidenceSourceBadgeProps) {
  if (!source.available) return null
  return (
    <div className={`border-l border-[var(--accent)] pl-3 ${className}`}>
      <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--accent)]">{source.label}</p>
      <p className="mt-1 font-mono text-[10px] text-[var(--text-secondary)]">{source.source}</p>
      <p className="mt-1 font-mono text-[10px] text-[var(--text-secondary)]">provenance: {source.provenance}</p>
    </div>
  )
}
