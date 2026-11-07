export type JobStatus =
  | 'uploaded'
  | 'editing'
  | 'edited'
  | 'preparing'
  | 'ready'
  | 'downloading'
  | 'imported'
  | 'failed'

export type Job = {
  id: string
  status: JobStatus
  original_filename: string
  content_type: string
  original_url: string
  current_url: string
  prepared_url: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}
