/**
 * Drag-and-drop upload, adapted from aceternity/ui/file-upload.tsx
 */
import { useCallback, useRef, useState, type MouseEvent } from 'react'
import { useDropzone } from 'react-dropzone'

const ACCEPT = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/webp': ['.webp'],
}

const MAX_BYTES = 10 * 1024 * 1024

type Props = {
  onFile: (file: File) => void
  disabled?: boolean
  demoUrl?: string
  demoLabel?: string
}

export function FileUpload({
  onFile,
  disabled,
  demoUrl = '/demo/wedding.jpeg',
  demoLabel = 'Try demo photo',
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [rejectMsg, setRejectMsg] = useState<string | null>(null)
  const [loadingDemo, setLoadingDemo] = useState(false)

  const handleFiles = useCallback(
    (files: File[]) => {
      const file = files[0]
      if (!file) return
      if (file.size > MAX_BYTES) {
        setRejectMsg('That file is over 10 MB. Please choose a smaller photo.')
        return
      }
      setRejectMsg(null)
      onFile(file)
    },
    [onFile],
  )

  const { getRootProps, isDragActive } = useDropzone({
    multiple: false,
    noClick: true,
    disabled,
    accept: ACCEPT,
    maxSize: MAX_BYTES,
    onDrop: handleFiles,
    onDropRejected: (rejections) => {
      const code = rejections[0]?.errors[0]?.code
      if (code === 'file-too-large') {
        setRejectMsg('That file is over 10 MB. Please choose a smaller photo.')
        return
      }
      setRejectMsg('Please choose a photo (JPG, PNG or WEBP).')
    },
  })

  async function loadDemo(event: MouseEvent) {
    event.preventDefault()
    event.stopPropagation()
    if (disabled || loadingDemo || !demoUrl) return
    setLoadingDemo(true)
    setRejectMsg(null)
    try {
      const res = await fetch(demoUrl)
      if (!res.ok) throw new Error('Demo photo missing')
      const blob = await res.blob()
      const name = demoUrl.split('/').pop() || 'demo.jpg'
      const file = new File([blob], name, { type: blob.type || 'image/jpeg' })
      onFile(file)
    } catch {
      setRejectMsg('Could not load the demo photo.')
    } finally {
      setLoadingDemo(false)
    }
  }

  return (
    <div className="upload" {...getRootProps()}>
      <button
        type="button"
        className={`upload__zone${isDragActive ? ' upload__zone--active' : ''}`}
        onClick={() => inputRef.current?.click()}
        disabled={disabled || loadingDemo}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
          className="upload__input"
          disabled={disabled || loadingDemo}
          onChange={(e) => {
            handleFiles(Array.from(e.target.files || []))
            e.target.value = ''
          }}
        />
        <div className="upload__content">
          <span className="upload__icon" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 16V4m0 0 4 4m-4-4-4 4M4 16.5V18a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1.5"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <p className="upload__title">{isDragActive ? 'Drop here' : 'Add a photo'}</p>
          <p className="upload__hint">Drag & drop or click</p>
          <p className="upload__formats">JPG, PNG, WEBP · 10 MB</p>
          {rejectMsg ? (
            <p className="upload__error" role="alert">
              {rejectMsg}
            </p>
          ) : null}
        </div>
      </button>
      {demoUrl ? (
        <button
          type="button"
          className="upload__demo"
          onClick={loadDemo}
          disabled={disabled || loadingDemo}
        >
          {loadingDemo ? 'Loading demo…' : demoLabel}
        </button>
      ) : null}
    </div>
  )
}
