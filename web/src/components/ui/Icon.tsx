export type IconName = 'record' | 'play' | 'arrow-right' | 'arrow-up-right' | 'copy' | 'check'

interface IconProps {
  name: IconName
  className?: string
}

/** Renders one of the six hand-authored interface symbols. */
export function Icon({ name, className = 'h-6 w-6' }: IconProps) {
  const common = {
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    strokeWidth: 1.5,
  }

  return (
    <svg aria-hidden="true" className={className} viewBox="0 0 24 24">
      {name === 'record' && <circle cx="12" cy="12" fill="currentColor" r="5" stroke="none" />}
      {name === 'play' && <path {...common} d="M8.5 6.5 17 12l-8.5 5.5z" />}
      {name === 'arrow-right' && <path {...common} d="M5 12h14m-5-5 5 5-5 5" />}
      {name === 'arrow-up-right' && <path {...common} d="M7 17 17 7M8 7h9v9" />}
      {name === 'copy' && <><rect {...common} height="11" width="11" x="8" y="8" /><path {...common} d="M16 8V5H5v11h3" /></>}
      {name === 'check' && <path {...common} d="m5 12 4.5 4.5L19 7" />}
    </svg>
  )
}
