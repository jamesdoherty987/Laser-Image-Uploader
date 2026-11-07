/**
 * Adapted from aceternity/ui/infinite-moving-cards.tsx
 */
import { useEffect, useRef, useState } from 'react'

type Props = {
  items: string[]
}

export function InfiniteMarquee({ items }: Props) {
  const scrollerRef = useRef<HTMLUListElement>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const scroller = scrollerRef.current
    if (!scroller || scroller.dataset.cloned === 'true') {
      setReady(true)
      return
    }
    const children = Array.from(scroller.children)
    children.forEach((child) => {
      scroller.appendChild(child.cloneNode(true))
    })
    scroller.dataset.cloned = 'true'
    setReady(true)
  }, [])

  return (
    <div className={`marquee${ready ? ' marquee--ready' : ''}`}>
      <ul className="marquee__track" ref={scrollerRef}>
        {items.map((item) => (
          <li key={item} className="marquee__item">
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
