/**
 * Adapted from aceternity/ui/hover-border-gradient.tsx
 */
import { motion } from 'framer-motion'
import { useEffect, useState, type ReactNode } from 'react'

type Direction = 'TOP' | 'LEFT' | 'BOTTOM' | 'RIGHT'

const movingMap: Record<Direction, string> = {
  TOP: 'radial-gradient(20.7% 50% at 50% 0%, hsl(0, 0%, 100%) 0%, rgba(255, 255, 255, 0) 100%)',
  LEFT: 'radial-gradient(16.6% 43.1% at 0% 50%, hsl(0, 0%, 100%) 0%, rgba(255, 255, 255, 0) 100%)',
  BOTTOM:
    'radial-gradient(20.7% 50% at 50% 100%, hsl(0, 0%, 100%) 0%, rgba(255, 255, 255, 0) 100%)',
  RIGHT:
    'radial-gradient(16.2% 41.2% at 100% 50%, hsl(0, 0%, 100%) 0%, rgba(255, 255, 255, 0) 100%)',
}

const highlight =
  'radial-gradient(75% 181% at 50% 50%, #5ec8be 0%, rgba(255, 255, 255, 0) 100%)'

const order: Direction[] = ['TOP', 'LEFT', 'BOTTOM', 'RIGHT']

type Props = {
  href: string
  children: ReactNode
}

export function HoverBorderButton({ href, children }: Props) {
  const [hovered, setHovered] = useState(false)
  const [direction, setDirection] = useState<Direction>('TOP')

  useEffect(() => {
    if (hovered) return
    const interval = window.setInterval(() => {
      setDirection((prev) => order[(order.indexOf(prev) + 1) % order.length])
    }, 1000)
    return () => window.clearInterval(interval)
  }, [hovered])

  return (
    <a
      href={href}
      className="hover-border"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <span className="hover-border__label">{children}</span>
      <motion.span
        className="hover-border__glow"
        animate={{
          background: hovered ? [movingMap[direction], highlight] : movingMap[direction],
        }}
        transition={{ ease: 'linear', duration: 1 }}
      />
      <span className="hover-border__fill" />
    </a>
  )
}
