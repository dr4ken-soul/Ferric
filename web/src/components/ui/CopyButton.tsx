import { useEffect, useState } from 'react'
import { Icon } from './Icon'

interface CopyButtonProps {
  value: string
}

/** Copies a code sample and announces the result to assistive technology. */
export function CopyButton({ value }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) return
    const timer = window.setTimeout(() => setCopied(false), 1600)
    return () => window.clearTimeout(timer)
  }, [copied])

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  return (
    <>
      <button
        aria-label={copied ? 'Copied' : 'Copy command'}
        className="inline-flex h-9 w-9 shrink-0 items-center justify-center border border-[var(--border-default)] text-[var(--text-secondary)] transition-colors duration-[240ms] hover:border-[var(--accent)] hover:text-[var(--accent)]"
        onClick={copy}
        type="button"
      >
        <Icon className="h-3.5 w-3.5" name={copied ? 'check' : 'copy'} />
      </button>
      <span aria-live="polite" className="sr-only">{copied ? 'Copied to clipboard' : ''}</span>
    </>
  )
}
