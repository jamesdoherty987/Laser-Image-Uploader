import axios from 'axios'
import type { Job } from '../types/job'

const apiBase = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

const api = axios.create({
  baseURL: apiBase,
  timeout: 60_000,
})

api.interceptors.request.use((config) => {
  if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
    const headers = config.headers
    if (headers && typeof (headers as { delete?: (k: string) => void }).delete === 'function') {
      ;(headers as { delete: (k: string) => void }).delete('Content-Type')
    } else if (headers) {
      delete (headers as Record<string, unknown>)['Content-Type']
    }
  }
  return config
})

export function mediaUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  if (!apiBase) return path
  return `${apiBase}${path.startsWith('/') ? path : `/${path}`}`
}

export async function uploadImage(file: File): Promise<Job> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<Job>('/api/images/upload', form)
  return data
}

export async function getJob(jobId: string): Promise<Job> {
  const { data } = await api.get<Job>(`/api/images/${jobId}`)
  return data
}

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (err.message) return err.message
  }
  if (err instanceof Error) return err.message
  return 'Something went wrong. Please try again.'
}
