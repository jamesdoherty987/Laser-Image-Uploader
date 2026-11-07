import { useEffect, useState } from 'react'
import { FileUpload } from '../components/FileUpload'
import { StatusBadge } from '../components/StatusBadge'
import { getErrorMessage, mediaUrl, uploadImage } from '../services/api'
import type { Job } from '../types/job'

export function HomePage() {
  const [job, setJob] = useState<Job | null>(null)
  const [localPreview, setLocalPreview] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    return () => {
      if (localPreview) URL.revokeObjectURL(localPreview)
    }
  }, [localPreview])

  async function handleFile(file: File) {
    setError(null)
    setJob(null)
    if (localPreview) URL.revokeObjectURL(localPreview)
    const preview = URL.createObjectURL(file)
    setLocalPreview(preview)
    setUploading(true)
    try {
      const created = await uploadImage(file)
      setJob(created)
      URL.revokeObjectURL(preview)
      setLocalPreview(null)
    } catch (err) {
      setJob(null)
      setError(getErrorMessage(err))
    } finally {
      setUploading(false)
    }
  }

  function reset() {
    if (localPreview) URL.revokeObjectURL(localPreview)
    setLocalPreview(null)
    setJob(null)
    setError(null)
  }

  const previewSrc = job ? mediaUrl(job.current_url) : localPreview
  const showPreview = Boolean(previewSrc)

  return (
    <main className="page">
      <header className="page__header">
        <h1 className="brand">Laser Image Uploader</h1>
        <p className="page__sub">Drop a photo to get started.</p>
      </header>

      {!showPreview ? (
        <section className="stage" aria-label="Upload">
          <FileUpload onFile={handleFile} disabled={uploading} />
          {error ? (
            <p className="banner banner--error" role="alert">
              {error}
            </p>
          ) : null}
        </section>
      ) : (
        <section className="stage" aria-label="Preview">
          <div className="preview">
            <div className="preview__meta">
              {job ? <StatusBadge status={job.status} /> : null}
              {uploading ? (
                <span className="preview__busy" role="status" aria-live="polite">
                  Uploading…
                </span>
              ) : (
                <span className="preview__name">
                  {job?.original_filename ?? 'Your photo'}
                </span>
              )}
            </div>

            <div className={`preview__frame${uploading ? ' preview__frame--busy' : ''}`}>
              <img
                src={previewSrc!}
                alt={job ? `Preview of ${job.original_filename}` : 'Selected photo preview'}
              />
            </div>

            {error ? (
              <p className="banner banner--error" role="alert">
                {error}
              </p>
            ) : null}

            <div className="actions">
              <button type="button" className="btn btn--ghost" onClick={reset} disabled={uploading}>
                Choose a different photo
              </button>
            </div>
          </div>
        </section>
      )}
    </main>
  )
}
