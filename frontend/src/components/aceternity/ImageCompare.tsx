/**
 * Adapted from aceternity/ui/compare.tsx
 */
import { useCallback, useRef, useState } from 'react'

type Props = {
  firstImage: string
  secondImage: string
  firstLabel?: string
  secondLabel?: string
  alt?: string
}

export function ImageCompare({
  firstImage,
  secondImage,
  firstLabel = 'Original',
  secondLabel = 'Laser ready',
  alt = 'Image comparison',
}: Props) {
  const [percent, setPercent] = useState(52)
  const [dragging, setDragging] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const updateFromClientX = useCallback((clientX: number) => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    if (rect.width <= 0) return
    const next = ((clientX - rect.left) / rect.width) * 100
    setPercent(Math.min(98, Math.max(2, next)))
  }, [])

  return (
    <div
      className={`compare${dragging ? ' is-dragging' : ''}`}
      ref={ref}
      role="slider"
      aria-label="Compare original and laser-ready image"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(percent)}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'ArrowLeft') setPercent((p) => Math.max(2, p - 4))
        if (e.key === 'ArrowRight') setPercent((p) => Math.min(98, p + 4))
      }}
      onMouseDown={(e) => {
        setDragging(true)
        updateFromClientX(e.clientX)
      }}
      onMouseMove={(e) => updateFromClientX(e.clientX)}
      onMouseUp={() => setDragging(false)}
      onMouseLeave={() => {
        setDragging(false)
        setPercent(52)
      }}
      onTouchStart={(e) => {
        setDragging(true)
        updateFromClientX(e.touches[0].clientX)
      }}
      onTouchMove={(e) => updateFromClientX(e.touches[0].clientX)}
      onTouchEnd={() => setDragging(false)}
    >
      <img className="compare__base" src={secondImage} alt={`${alt} — ${secondLabel}`} draggable={false} />
      <div className="compare__clip" style={{ width: `${percent}%` }}>
        <img src={firstImage} alt={`${alt} — ${firstLabel}`} draggable={false} />
      </div>
      <div className="compare__line" style={{ left: `${percent}%` }}>
        <span className="compare__handle" aria-hidden="true" />
      </div>
      <span className="compare__label compare__label--left">{firstLabel}</span>
      <span className="compare__label compare__label--right">{secondLabel}</span>
      <p className="compare__hint">Drag to compare</p>
    </div>
  )
}
