/**
 * Adapted from aceternity/ui/meteors.tsx
 */
import { useMemo } from 'react'

type Props = {
  number?: number
}

export function Meteors({ number = 16 }: Props) {
  const meteors = useMemo(
    () =>
      Array.from({ length: number }, (_, idx) => ({
        id: idx,
        left: `${(idx * (100 / number) + (idx % 3) * 2) % 100}%`,
        delay: `${(idx * 0.37) % 5}s`,
        duration: `${5 + (idx % 6)}s`,
      })),
    [number],
  )

  return (
    <div className="meteors" aria-hidden="true">
      {meteors.map((meteor) => (
        <span
          key={meteor.id}
          className="meteors__item"
          style={{
            left: meteor.left,
            animationDelay: meteor.delay,
            animationDuration: meteor.duration,
          }}
        />
      ))}
    </div>
  )
}
