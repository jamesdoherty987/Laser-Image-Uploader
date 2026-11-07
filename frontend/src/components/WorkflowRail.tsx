import type { StudioStep } from '../types/job'

const STEPS: { id: StudioStep; label: string }[] = [
  { id: 'upload', label: 'Upload' },
  { id: 'review', label: 'Review' },
  { id: 'prepare', label: 'Prepare' },
  { id: 'ready', label: 'Ready' },
]

type Props = {
  current: StudioStep
}

function stepIndex(step: StudioStep) {
  return STEPS.findIndex((item) => item.id === step)
}

export function WorkflowRail({ current }: Props) {
  const active = stepIndex(current)

  return (
    <ol className="workflow" aria-label="Job progress">
      {STEPS.map((step, index) => {
        const state = index < active ? 'done' : index === active ? 'active' : 'todo'
        return (
          <li key={step.id} className={`workflow__item workflow__item--${state}`}>
            <span className="workflow__dot" aria-hidden="true" />
            <span className="workflow__label">{step.label}</span>
          </li>
        )
      })}
    </ol>
  )
}
