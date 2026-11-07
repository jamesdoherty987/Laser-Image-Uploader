/**
 * Adapted from aceternity/ui/flip-words.tsx
 */
import { AnimatePresence, motion } from 'framer-motion'
import { useCallback, useEffect, useState } from 'react'

type Props = {
  words: string[]
  duration?: number
}

export function FlipWords({ words, duration = 2600 }: Props) {
  const [index, setIndex] = useState(0)
  const [animating, setAnimating] = useState(false)
  const current = words[index] ?? words[0]

  const next = useCallback(() => {
    setIndex((prev) => (prev + 1) % words.length)
    setAnimating(true)
  }, [words.length])

  useEffect(() => {
    if (animating) return
    const timer = window.setTimeout(next, duration)
    return () => window.clearTimeout(timer)
  }, [animating, duration, next])

  return (
    <span className="flip-words">
      <AnimatePresence
        mode="wait"
        onExitComplete={() => {
          setAnimating(false)
        }}
      >
        <motion.span
          key={current}
          className="flip-words__word"
          initial={{ opacity: 0, y: 12, filter: 'blur(6px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          exit={{ opacity: 0, y: -18, filter: 'blur(6px)' }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
        >
          {current}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}
