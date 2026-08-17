import { useEffect, type RefObject } from 'react'

/** Updates a timecode node from one animation frame loop without React renders. */
export function useSessionTimecode(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const startedAt = performance.now()
    let frame = 0
    let lastSecond = -1

    const update = (now: number) => {
      const elapsed = Math.floor((now - startedAt) / 1000)
      if (elapsed !== lastSecond && ref.current) {
        const hours = Math.floor(elapsed / 3600)
        const minutes = Math.floor((elapsed % 3600) / 60)
        const seconds = elapsed % 60
        ref.current.textContent = [hours, minutes, seconds]
          .map((part) => String(part).padStart(2, '0'))
          .join(':')
        ref.current.parentElement?.setAttribute('aria-label', `Session elapsed time ${hours} hours, ${minutes} minutes, ${seconds} seconds. Return to top.`)
        lastSecond = elapsed
      }
      frame = requestAnimationFrame(update)
    }

    frame = requestAnimationFrame(update)
    return () => cancelAnimationFrame(frame)
  }, [ref])
}
