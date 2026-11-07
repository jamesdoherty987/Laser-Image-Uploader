/**
 * Drag-and-drop upload — adapted from aceternity/ui/file-upload.tsx
 * Restyled for a sharp black-and-white interface (no rounded corners).
 */
import { useCallback, useRef, useState } from 'react'
import { useDropzone } from 'react-dropzone'

const ACCEPT = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/webp': ['.webp'],
}

type Props = {
  onFile: (file: File) => void
  disabled?: boolean
}

export function FileUpload({ onFile, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [rejectMsg, setRejectMsg] = useState<string | null>(null)

  const handleFiles = useCallback(
    (files: File[]) => {
      const file = files[0]
      if (!file) return
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
    onDrop: handleFiles,
    onDropRejected: () => {
      setRejectMsg('Please choose a photo (JPG, PNG or WEBP).')
    },
  })

  return (
    <div className="upload" {...getRootProps()}>
      <button
        type="button"
        className={`upload__zone${isDragActive ? ' upload__zone--active' : ''}`}
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
          className="upload__input"
          disabled={disabled}
          onChange={(e) => {
            handleFiles(Array.from(e.target.files || []))
            e.target.value = ''
          }}
        />
        <div className="upload__content">
          <p className="upload__title">{isDragActive ? 'Drop photo here' : 'Add a photo'}</p>
          <p className="upload__hint">Drag and drop, or click to choose</p>
          <p className="upload__formats">JPG, PNG or WEBP</p>
          {rejectMsg ? (
            <p className="upload__error" role="alert">
              {rejectMsg}
            </p>
          ) : null}
        </div>
      </button>
    </div>
  )
}
