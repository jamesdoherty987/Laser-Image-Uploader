/**
 * Adapted from aceternity/ui/lamp.tsx
 */
import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { Meteors } from './Meteors'

type Props = {
  children: ReactNode
}

export function LampHero({ children }: Props) {
  return (
    <section className="lamp" aria-label="Hero">
      <div className="lamp__stage" aria-hidden="true">
        <motion.div
          className="lamp__cone lamp__cone--left"
          initial={{ opacity: 0.45, width: '15rem' }}
          whileInView={{ opacity: 1, width: '30rem' }}
          transition={{ delay: 0.2, duration: 0.85, ease: 'easeInOut' }}
          viewport={{ once: true }}
        />
        <motion.div
          className="lamp__cone lamp__cone--right"
          initial={{ opacity: 0.45, width: '15rem' }}
          whileInView={{ opacity: 1, width: '30rem' }}
          transition={{ delay: 0.2, duration: 0.85, ease: 'easeInOut' }}
          viewport={{ once: true }}
        />
        <div className="lamp__glow" />
        <motion.div
          className="lamp__core"
          initial={{ width: '8rem' }}
          whileInView={{ width: '16rem' }}
          transition={{ delay: 0.2, duration: 0.85, ease: 'easeInOut' }}
          viewport={{ once: true }}
        />
        <motion.div
          className="lamp__line"
          initial={{ width: '15rem' }}
          whileInView={{ width: '30rem' }}
          transition={{ delay: 0.2, duration: 0.85, ease: 'easeInOut' }}
          viewport={{ once: true }}
        />
        <div className="lamp__shade" />
        <Meteors number={14} />
      </div>
      <div className="lamp__content">{children}</div>
    </section>
  )
}
