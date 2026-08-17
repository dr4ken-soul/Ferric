interface SkeletonProps {
  lines?: number
  className?: string
}

/** Renders an honest, non-numeric loading state for missing cassette evidence. */
export function Skeleton({ lines = 3, className = '' }: SkeletonProps) {
  return (
    <div aria-label="Cassette evidence is not available" className={`flex flex-col gap-3 ${className}`} role="status">
      {Array.from({ length: lines }, (_, index) => (
        <div className="relative h-3 overflow-hidden bg-[var(--bg-elevated)]" key={index}>
          <div className="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/[0.06] to-transparent bg-[length:200%_100%]" />
        </div>
      ))}
      <span className="sr-only">Waiting for validated cassette data</span>
    </div>
  )
}
