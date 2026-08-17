import { motion } from 'motion/react'
import { useReducedMotion } from '../../hooks/useReducedMotion'

interface BlurTextProps {
  text: string
  className?: string
}

/** Reveals hero copy word by word while preserving natural wrapping. */
export function BlurText({ text, className = '' }: BlurTextProps) {
  const reducedMotion = useReducedMotion().reduced
  const words = text.split(' ')
  return (
    <span className={className}>
      <span className="sr-only">{text}</span>
      <span aria-hidden="true">
        {words.map((word, index) => (
          <motion.span
            className="inline-block"
            initial={reducedMotion ? { opacity: 0 } : { opacity: 0, filter: 'blur(12px)', y: 34 }}
            animate={reducedMotion ? { opacity: 1 } : { opacity: 1, filter: 'blur(0px)', y: 0 }}
            transition={reducedMotion ? { duration: 0.2 } : { duration: 0.65, ease: [0.16, 1, 0.3, 1], delay: 0.35 + index * 0.07 }}
            key={`${word}-${index}`}
          >
            {word}{index < words.length - 1 ? '\u00a0' : ''}
          </motion.span>
        ))}
      </span>
    </span>
  )
}
