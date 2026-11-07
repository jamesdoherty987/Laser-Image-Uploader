/**
 * Adapted from aceternity/ui/background-beams.tsx + spotlight.tsx
 * Clean image-forward hero for Galvin Crafts.
 */
import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { mediaUrl } from '../../services/api'
import type { LandingImage } from '../../types/content'

const PATHS = [
  'M-380 -189C-380 -189 -312 216 152 343C616 470 684 875 684 875',
  'M-345 -229C-345 -229 -277 176 187 303C651 430 719 835 719 835',
  'M-310 -269C-310 -269 -242 136 222 263C686 390 754 795 754 795',
  'M-275 -309C-275 -309 -207 96 257 223C721 350 789 755 789 755',
  'M-240 -349C-240 -349 -172 56 292 183C756 310 824 715 824 715',
  'M-205 -389C-205 -389 -137 16 327 143C791 270 859 675 859 675',
  'M-170 -429C-170 -429 -102 -24 362 103C826 230 894 635 894 635',
  'M-135 -469C-135 -469 -67 -64 397 63C861 190 929 595 929 595',
  'M-100 -509C-100 -509 -32 -104 432 23C896 150 964 555 964 555',
  'M-65 -549C-65 -549 3 -144 467 -17C931 110 999 515 999 515',
  'M-30 -589C-30 -589 38 -184 502 -57C966 70 1034 475 1034 475',
  'M5 -629C5 -629 73 -224 537 -97C1001 30 1069 435 1069 435',
]

type Props = {
  children: ReactNode
  images?: LandingImage[]
}

export function BeamsHero({ children, images = [] }: Props) {
  const showcase = images.slice(0, 4)

  return (
    <section className="beams-hero" aria-label="Hero">
      <div className="beams-hero__media" aria-hidden="true">
        <svg className="beams-hero__svg" viewBox="0 0 696 316" fill="none" preserveAspectRatio="xMidYMid slice">
          {PATHS.map((d, index) => (
            <motion.path
              key={d}
              d={d}
              stroke={`url(#galvin-beam-${index})`}
              strokeOpacity="0.55"
              strokeWidth="0.7"
              fill="none"
            />
          ))}
          <defs>
            {PATHS.map((_, index) => (
              <motion.linearGradient
                key={`grad-${index}`}
                id={`galvin-beam-${index}`}
                initial={{ x1: '0%', x2: '0%', y1: '0%', y2: '0%' }}
                animate={{
                  x1: ['0%', '100%'],
                  x2: ['0%', '95%'],
                  y1: ['0%', '100%'],
                  y2: ['0%', `${90 + (index % 5)}%`],
                }}
                transition={{
                  duration: 12 + (index % 5),
                  ease: 'easeInOut',
                  repeat: Infinity,
                  delay: index * 0.35,
                }}
              >
                <stop stopColor="#99f6e4" stopOpacity="0" />
                <stop stopColor="#5eead4" />
                <stop offset="100%" stopColor="#0f766e" stopOpacity="0" />
              </motion.linearGradient>
            ))}
          </defs>
        </svg>
        <div className="beams-hero__glow" />
      </div>

      <div className="beams-hero__layout">
        <div className="beams-hero__copy">{children}</div>

        <div className="beams-hero__gallery" aria-label="Featured work">
          {showcase.length > 0 ? (
            showcase.map((image, index) => (
              <motion.figure
                key={image.id}
                className={`beams-hero__shot beams-hero__shot--${index + 1}`}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + index * 0.08, duration: 0.55 }}
              >
                <img src={mediaUrl(image.image_url)} alt={image.alt_text || image.title || 'Galvin Crafts work'} />
              </motion.figure>
            ))
          ) : (
            <div className="beams-hero__placeholder">
              <p>Add hero images in Admin to showcase your crafts here.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
