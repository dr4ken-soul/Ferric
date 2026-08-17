import { motion, type HTMLMotionProps } from 'motion/react'
import { useReducedMotion } from '../../hooks/useReducedMotion'

/** Applies the standard replayable entrance animation to below-fold content. */
export function Reveal({ children, transition, ...props }: HTMLMotionProps<'div'>) {
  const reducedMotion = useReducedMotion().reduced
  return (
    <motion.div
      initial={reducedMotion ? { opacity: 0 } : { opacity: 0, filter: 'blur(10px)', y: 24 }}
      whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, filter: 'blur(0px)', y: 0 }}
      viewport={{ once: false, amount: 0.1 }}
      transition={reducedMotion ? { duration: 0.2 } : { duration: 0.7, ease: [0.16, 1, 0.3, 1], ...transition }}
      {...props}
    >
      {children}
    </motion.div>
  )
}
