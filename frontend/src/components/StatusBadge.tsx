import type { JobStatus } from '../types/job'

const LABELS: Record<JobStatus, string> = {
  uploaded: 'Uploaded',
  editing: 'Processing',
  edited: 'Edited',
  preparing: 'Preparing',
  ready: 'Ready',
  downloading: 'Sending',
  imported: 'Sent',
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
