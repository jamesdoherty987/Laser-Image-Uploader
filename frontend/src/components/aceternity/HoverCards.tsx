/**
 * Adapted from aceternity/ui/card-hover-effect.tsx
 */
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'

type Item = {
  title: string
  description: string
}

type Props = {
  items: Item[]
}

export function HoverCards({ items }: Props) {
  const [hovered, setHovered] = useState<number | null>(null)

  return (
    <div className="hover-cards">
      {items.map((item, idx) => (
        <article
          key={item.title}
          className="hover-cards__item"
          onMouseEnter={() => setHovered(idx)}
          onMouseLeave={() => setHovered(null)}
        >
          <AnimatePresence>
            {hovered === idx ? (
              <motion.span
                className="hover-cards__bg"
                layoutId="hoverBackground"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1, transition: { duration: 0.15 } }}
                exit={{ opacity: 0, transition: { duration: 0.15, delay: 0.1 } }}
              />
            ) : null}
          </AnimatePresence>
          <div className="hover-cards__card">
            <h3 className="hover-cards__title">{item.title}</h3>
            <p className="hover-cards__body">{item.description}</p>
          </div>
        </article>
      ))}
    </div>
  )
}
