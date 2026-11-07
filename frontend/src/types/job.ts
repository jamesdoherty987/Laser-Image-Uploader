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
  edited_url: string | null
  prepared_url: string | null
  error_message: string | null
  width: number | null
  height: number | null
  dpi: number | null
  width_mm: number | null
  height_mm: number | null
  created_at: string
  updated_at: string
}

export type PrepMode =
  | 'floyd'
  | 'jarvis'
  | 'stucki'
  | 'atkinson'
  | 'ordered'
  | 'threshold'
  | 'grayscale'

export type PrepareOptions = {
  mode: PrepMode
  contrast: number
  brightness: number
  sharpness: number
  denoise: number
  invert: boolean
  threshold: number
  width_mm: number | null
  height_mm: number | null
  dpi: number
}

export type StudioStep = 'upload' | 'review' | 'prepare' | 'ready'
