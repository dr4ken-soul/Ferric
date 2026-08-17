import { useMotionValue, useSpring } from 'motion/react'
import type { PointerEvent } from 'react'

/** Supplies bounded spring motion for the primary hero action. */
export function useMagneticHover(disabled: boolean) {
  const rawX = useMotionValue(0)
  const rawY = useMotionValue(0)
  const x = useSpring(rawX, { stiffness: 220, damping: 18 })
  const y = useSpring(rawY, { stiffness: 220, damping: 18 })

  const onPointerMove = (event: PointerEvent<HTMLElement>) => {
    if (disabled) return
    const bounds = event.currentTarget.getBoundingClientRect()
    rawX.set(((event.clientX - bounds.left) / bounds.width - 0.5) * 10)
    rawY.set(((event.clientY - bounds.top) / bounds.height - 0.5) * 10)
  }

  const onPointerLeave = () => {
    rawX.set(0)
    rawY.set(0)
  }

  return { x, y, onPointerMove, onPointerLeave }
}
