import { useEffect, useState } from 'react'

/** Reports reduced motion and whether the viewport is below the desktop pin breakpoint. */
export function useReducedMotion() {
  const [preference, setPreference] = useState({ reduced: true, mobile: true, ready: false })

  useEffect(() => {
    const reducedQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    const mobileQuery = window.matchMedia('(max-width: 1023px)')
    const update = () => setPreference({ reduced: reducedQuery.matches, mobile: mobileQuery.matches, ready: true })
    update()
    reducedQuery.addEventListener('change', update)
    mobileQuery.addEventListener('change', update)
    return () => {
      reducedQuery.removeEventListener('change', update)
      mobileQuery.removeEventListener('change', update)
    }
  }, [])

  return preference
}
