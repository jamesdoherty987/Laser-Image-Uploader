import type { JobStatus } from '../types/job'

const LABELS: Record<JobStatus, string> = {
  uploaded: 'Uploaded',
  editing: 'Editing',
  edited: 'Edited',
  preparing: 'Preparing',
  ready: 'Laser ready',
  downloading: 'Sending',
  imported: 'In CorelDRAW',
  failed: 'Failed',
}

type Props = {
  status: JobStatus
}

export function StatusBadge({ status }: Props) {
  return (
    <span className={`status status--${status}`} data-status={status}>
      {LABELS[status]}
    </span>
  )
}
