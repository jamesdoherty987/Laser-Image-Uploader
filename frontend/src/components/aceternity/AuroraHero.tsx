/**
 * Adapted from aceternity/ui/aurora-background.tsx
 * Compact, centered, simple.
 */
import { motion } from 'framer-motion'
import type { ReactNode } from 'react'

type Props = {
  children: ReactNode
}

export function AuroraHero({ children }: Props) {
  return (
    <section className="aurora-hero" aria-label="Hero">
      <div className="aurora-hero__stage" aria-hidden="true">
        <div className="aurora-hero__aurora" />
      </div>
      <motion.div
        className="aurora-hero__content"
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.7, ease: 'easeInOut' }}
      >
        {children}
      </motion.div>
    </section>
  )
}
