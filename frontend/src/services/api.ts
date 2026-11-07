import axios from 'axios'
import type { CraftTemplate, LandingImage, Product, SiteContact } from '../types/content'
import type { Job } from '../types/job'

const apiBase = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const ADMIN_TOKEN_KEY = 'galvin_admin_token'

const api = axios.create({
  baseURL: apiBase,
  timeout: 90_000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ADMIN_TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
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

export function getAdminToken(): string | null {
  return localStorage.getItem(ADMIN_TOKEN_KEY)
}

export function setAdminToken(token: string | null) {
  if (!token) localStorage.removeItem(ADMIN_TOKEN_KEY)
  else localStorage.setItem(ADMIN_TOKEN_KEY, token)
}

export async function uploadImage(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<Job> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<Job>('/api/images/upload', form, {
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) return
      onProgress(Math.min(99, Math.round((event.loaded / event.total) * 100)))
    },
  })
  onProgress?.(100)
  return data
}

export async function getJob(jobId: string): Promise<Job> {
  const { data } = await api.get<Job>(`/api/images/${jobId}`)
  return data
}

export async function prepareJob(
  jobId: string,
  options?: {
    mode?: string
    contrast?: number
    brightness?: number
    sharpness?: number
    denoise?: number
    invert?: boolean
    threshold?: number
    width_mm?: number | null
    height_mm?: number | null
    dpi?: number
  },
  opts?: { live?: boolean },
): Promise<Job> {
  const { data } = await api.post<Job>(`/api/images/${jobId}/prepare`, options ?? {}, {
    params: opts?.live ? { live: true } : undefined,
  })
  return data
}

export async function editJob(jobId: string, prompt: string): Promise<Job> {
  const { data } = await api.post<Job>(
    `/api/images/${jobId}/edit`,
    { prompt },
    { timeout: 150_000 },
  )
  return data
}

export async function fetchRecentJobs(limit = 6): Promise<Job[]> {
  const { data } = await api.get<Job[]>('/api/images/', { params: { limit } })
  return data
}

export async function fetchLandingImages(section?: string): Promise<LandingImage[]> {
  const { data } = await api.get<LandingImage[]>('/api/content/landing-images', {
    params: section ? { section } : undefined,
  })
  return data
}

export async function fetchTemplates(): Promise<CraftTemplate[]> {
  const { data } = await api.get<CraftTemplate[]>('/api/content/templates')
  return data
}

export async function fetchProducts(): Promise<Product[]> {
  const { data } = await api.get<Product[]>('/api/content/products')
  return data
}

export async function fetchContact(): Promise<SiteContact> {
  const { data } = await api.get<SiteContact>('/api/content/contact')
  return data
}

export function formatMoney(priceCents: number, currency = 'EUR'): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(priceCents / 100)
  } catch {
    return `${(priceCents / 100).toFixed(2)} ${currency.toUpperCase()}`
  }
}

export async function adminLogin(username: string, password: string): Promise<string> {
  const { data } = await api.post<{ token: string }>('/api/admin/login', { username, password })
  setAdminToken(data.token)
  return data.token
}

export async function adminListLandingImages(): Promise<LandingImage[]> {
  const { data } = await api.get<LandingImage[]>('/api/admin/landing-images')
  return data
}

export async function adminCreateLandingImage(input: {
  file: File
  title: string
  alt_text: string
  section: string
}): Promise<LandingImage> {
  const form = new FormData()
  form.append('file', input.file)
  form.append('title', input.title)
  form.append('alt_text', input.alt_text)
  form.append('section', input.section)
  const { data } = await api.post<LandingImage>('/api/admin/landing-images', form)
  return data
}

export async function adminUpdateLandingImage(
  id: string,
  payload: Partial<Pick<LandingImage, 'title' | 'alt_text' | 'section' | 'sort_order' | 'is_active'>>,
): Promise<LandingImage> {
  const { data } = await api.patch<LandingImage>(`/api/admin/landing-images/${id}`, payload)
  return data
}

export async function adminDeleteLandingImage(id: string): Promise<void> {
  await api.delete(`/api/admin/landing-images/${id}`)
}

export async function adminListTemplates(): Promise<CraftTemplate[]> {
  const { data } = await api.get<CraftTemplate[]>('/api/admin/templates')
  return data
}

export async function adminCreateTemplate(input: {
  name: string
  description: string
  category: string
  file?: File | null
}): Promise<CraftTemplate> {
  const form = new FormData()
  form.append('name', input.name)
  form.append('description', input.description)
  form.append('category', input.category)
  if (input.file) form.append('file', input.file)
  const { data } = await api.post<CraftTemplate>('/api/admin/templates', form)
  return data
}

export async function adminUpdateTemplate(
  id: string,
  input: {
    name?: string
    description?: string
    category?: string
    is_active?: boolean
    file?: File | null
  },
): Promise<CraftTemplate> {
  const form = new FormData()
  if (input.name != null) form.append('name', input.name)
  if (input.description != null) form.append('description', input.description)
  if (input.category != null) form.append('category', input.category)
  if (input.is_active != null) form.append('is_active', String(input.is_active))
  if (input.file) form.append('file', input.file)
  const { data } = await api.patch<CraftTemplate>(`/api/admin/templates/${id}`, form)
  return data
}

export async function adminDeleteTemplate(id: string): Promise<void> {
  await api.delete(`/api/admin/templates/${id}`)
}

export async function adminListProducts(): Promise<Product[]> {
  const { data } = await api.get<Product[]>('/api/admin/products')
  return data
}

export async function adminCreateProduct(input: {
  name: string
  description: string
  category: string
  price_cents: number
  currency?: string
  file?: File | null
}): Promise<Product> {
  const form = new FormData()
  form.append('name', input.name)
  form.append('description', input.description)
  form.append('category', input.category)
  form.append('price_cents', String(input.price_cents))
  form.append('currency', input.currency || 'EUR')
  if (input.file) form.append('file', input.file)
  const { data } = await api.post<Product>('/api/admin/products', form)
  return data
}

export async function adminUpdateProduct(
  id: string,
  input: {
    name?: string
    description?: string
    category?: string
    price_cents?: number
    currency?: string
    is_active?: boolean
    file?: File | null
  },
): Promise<Product> {
  const form = new FormData()
  if (input.name != null) form.append('name', input.name)
  if (input.description != null) form.append('description', input.description)
  if (input.category != null) form.append('category', input.category)
  if (input.price_cents != null) form.append('price_cents', String(input.price_cents))
  if (input.currency != null) form.append('currency', input.currency)
  if (input.is_active != null) form.append('is_active', String(input.is_active))
  if (input.file) form.append('file', input.file)
  const { data } = await api.patch<Product>(`/api/admin/products/${id}`, form)
  return data
}

export async function adminDeleteProduct(id: string): Promise<void> {
  await api.delete(`/api/admin/products/${id}`)
}

export async function adminGetContact(): Promise<SiteContact> {
  const { data } = await api.get<SiteContact>('/api/admin/contact')
  return data
}

export async function adminUpdateContact(
  payload: Partial<Omit<SiteContact, 'updated_at'>>,
): Promise<SiteContact> {
  const { data } = await api.put<SiteContact>('/api/admin/contact', payload)
  return data
}

export async function adminListJobs(params?: {
  limit?: number
  status?: string
}): Promise<Job[]> {
  const { data } = await api.get<Job[]>('/api/admin/jobs', { params })
  return data
}

export async function adminPrepareJob(
  jobId: string,
  options?: {
    mode?: string
    contrast?: number
    brightness?: number
    invert?: boolean
    threshold?: number
  },
): Promise<Job> {
  const { data } = await api.post<Job>(`/api/admin/jobs/${jobId}/prepare`, options ?? {})
  return data
}

export async function adminUpdateJobStatus(
  jobId: string,
  status: string,
  error_message?: string,
): Promise<Job> {
  const { data } = await api.patch<Job>(`/api/admin/jobs/${jobId}/status`, {
    status,
    error_message,
  })
  return data
}

export async function adminDeleteJob(jobId: string): Promise<void> {
  await api.delete(`/api/admin/jobs/${jobId}`)
}

export type DesktopInfo = {
  pairing_token: string
  api_base: string
  download_path: string
  instructions: string
}

export async function adminDesktopInfo(): Promise<DesktopInfo> {
  const { data } = await api.get<DesktopInfo>('/api/admin/desktop')
  return data
}

export async function adminDownloadDesktop(): Promise<Blob> {
  const { data } = await api.get<Blob>('/api/admin/desktop/download', {
    responseType: 'blob',
  })
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
