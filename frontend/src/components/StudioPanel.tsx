import { useEffect, useMemo, useRef, useState } from 'react'
import { ImageCompare } from './aceternity/ImageCompare'
import { FileUpload } from './FileUpload'
import { StatusBadge } from './StatusBadge'
import { WorkflowRail } from './WorkflowRail'
import {
  editJob,
  fetchRecentJobs,
  getErrorMessage,
  mediaUrl,
  prepareJob,
  uploadImage,
} from '../services/api'
import type { Job, PrepMode, PrepareOptions, StudioStep } from '../types/job'

function formatBytes(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function deriveStep(job: Job | null, hasLocalPreview: boolean): StudioStep {
  if (!job && !hasLocalPreview) return 'upload'
  if (!job) return 'review'
  if (job.status === 'ready' || job.prepared_url) return 'ready'
  if (job.status === 'preparing') return 'prepare'
  if (job.status === 'editing') return 'review'
  return 'review'
}

function cacheBust(url: string, stamp: string | number | null | undefined) {
  if (!url) return url
  const base = mediaUrl(url)
  if (!stamp) return base
  const sep = base.includes('?') ? '&' : '?'
  return `${base}${sep}t=${encodeURIComponent(String(stamp))}`
}

function prepKey(options: PrepareOptions) {
  return JSON.stringify(options)
}

const DEFAULT_PREP: PrepareOptions = {
  mode: 'floyd',
  contrast: 1.55,
  brightness: 1.05,
  sharpness: 1.1,
  denoise: 0.35,
  invert: false,
  threshold: 128,
  width_mm: 90,
  height_mm: null,
  dpi: 300,
}

const MODE_HELP: Record<PrepMode, string> = {
  floyd: 'Floyd–Steinberg — best for photos & portraits',
  jarvis: 'Jarvis–Judice–Ninke — smoother photo dither',
  stucki: 'Stucki — sharp photo dither, common in LightBurn',
  atkinson: 'Atkinson — high-contrast / comic look',
  ordered: 'Bayer ordered — logos & flat fills',
  threshold: 'Hard black/white cut — clean line art',
  grayscale: 'Continuous tone — if your laser software dithers',
}

const PREP_MODES = Object.keys(MODE_HELP) as PrepMode[]

export function StudioPanel() {
  const [job, setJob] = useState<Job | null>(null)
  const [localPreview, setLocalPreview] = useState<string | null>(null)
  const [localFile, setLocalFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [preparing, setPreparing] = useState(false)
  const [editing, setEditing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [recent, setRecent] = useState<Job[]>([])
  const [prep, setPrep] = useState<PrepareOptions>(DEFAULT_PREP)
  const [appliedPrep, setAppliedPrep] = useState<PrepareOptions | null>(null)
  const [editPrompt, setEditPrompt] = useState('')
  const openedDemo = useRef(false)

  const prepDirty = Boolean(job && appliedPrep && prepKey(prep) !== prepKey(appliedPrep))
  const needsFirstPrepare = Boolean(job && !job.prepared_url)

  useEffect(() => {
    return () => {
      if (localPreview) URL.revokeObjectURL(localPreview)
    }
  }, [localPreview])

  useEffect(() => {
    let cancelled = false
    fetchRecentJobs(6)
      .then((jobs) => {
        if (cancelled) return
        setRecent(jobs)
        if (!openedDemo.current) {
          const demo = jobs.find((item) => item.original_filename === 'wedding.jpeg')
          if (demo) {
            openedDemo.current = true
            setJob((current) => current ?? demo)
            if (demo.prepared_url) setAppliedPrep(DEFAULT_PREP)
          }
        }
      })
      .catch(() => {
        if (!cancelled) setRecent([])
      })
    return () => {
      cancelled = true
    }
  }, [job?.id, job?.status])

  function updatePrep(patch: Partial<PrepareOptions>) {
    setPrep((prev) => ({ ...prev, ...patch }))
    setNotice(null)
  }

  async function handleFile(file: File) {
    setError(null)
    setNotice(null)
    setJob(null)
    setPrep(DEFAULT_PREP)
    setAppliedPrep(null)
    setEditPrompt('')
    if (localPreview) URL.revokeObjectURL(localPreview)
    const preview = URL.createObjectURL(file)
    setLocalPreview(preview)
    setLocalFile(file)
    setUploading(true)
    setProgress(8)
    try {
      const created = await uploadImage(file, setProgress)
      setJob(created)
      URL.revokeObjectURL(preview)
      setLocalPreview(null)
      setNotice('Uploaded. Tweak laser settings, then press Prepare for laser.')
    } catch (err) {
      setJob(null)
      setError(getErrorMessage(err))
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  function reset() {
    if (localPreview) URL.revokeObjectURL(localPreview)
    setLocalPreview(null)
    setLocalFile(null)
    setJob(null)
    setError(null)
    setNotice(null)
    setPrep(DEFAULT_PREP)
    setAppliedPrep(null)
    setEditPrompt('')
  }

  async function handlePrepare() {
    if (!job) return
    setError(null)
    setNotice(null)
    setPreparing(true)
    try {
      const updated = await prepareJob(job.id, prep)
      setJob(updated)
      setAppliedPrep(prep)
      setNotice('Laser preview updated with your current settings.')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setPreparing(false)
    }
  }

  async function handleEdit() {
    if (!job || editPrompt.trim().length < 3) return
    setError(null)
    setNotice(null)
    setEditing(true)
    try {
      const updated = await editJob(job.id, editPrompt.trim())
      setJob(updated)
      setAppliedPrep(null)
      setNotice('AI edit applied. Press Prepare for laser to refresh the engraving preview.')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setEditing(false)
    }
  }

  async function openRecent(item: Job) {
    setError(null)
    setNotice(null)
    setLocalFile(null)
    if (localPreview) URL.revokeObjectURL(localPreview)
    setLocalPreview(null)
    setJob(item)
    // Unknown prior settings for older jobs — mark clean until user changes something
    setAppliedPrep(item.prepared_url ? { ...prep } : null)
    setPrep((p) => ({ ...p }))
  }

  const step = deriveStep(job, Boolean(localPreview))
  const busy = uploading || editing || preparing

  const previewSrc = useMemo(() => {
    if (!job) return localPreview
    return cacheBust(job.current_url, job.updated_at)
  }, [job, localPreview])

  const compareBefore = useMemo(() => {
    if (!job) return null
    return cacheBust(job.edited_url || job.original_url, job.updated_at)
  }, [job])

  const compareAfter = useMemo(() => {
    if (!job?.prepared_url) return null
    return cacheBust(job.prepared_url, job.updated_at)
  }, [job])

  const showPreview = Boolean(previewSrc)
  const isReady = Boolean(job?.prepared_url || job?.status === 'ready')
  const applyLabel = preparing
    ? 'Updating…'
    : needsFirstPrepare
      ? 'Prepare for laser'
      : 'Update preview'

  return (
    <div className="studio-shell">
      <WorkflowRail current={step} />

      <div className="studio__panel">
        {!showPreview ? (
          <section className="stage" aria-label="Upload">
            <FileUpload onFile={handleFile} disabled={busy} />
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
                    Uploading… {progress}%
                  </span>
                ) : editing ? (
                  <span className="preview__busy" role="status" aria-live="polite">
                    AI editing…
                  </span>
                ) : preparing ? (
                  <span className="preview__busy" role="status" aria-live="polite">
                    Preparing laser artwork…
                  </span>
                ) : (
                  <span className="preview__name">
                    {job?.original_filename ?? localFile?.name ?? 'Your photo'}
                  </span>
                )}
              </div>

              {job ? (
                <div className="preview__stats" aria-label="Laser metrics">
                  {job.width && job.height ? (
                    <span>
                      {job.width} × {job.height}px
                    </span>
                  ) : null}
                  {job.width_mm && job.height_mm ? (
                    <span>
                      {job.width_mm} × {job.height_mm} mm
                    </span>
                  ) : null}
                  {job.dpi ? <span>{job.dpi} DPI</span> : null}
                  {localFile ? <span>{formatBytes(localFile.size)}</span> : null}
                  <span className="preview__id">Job {job.id.slice(0, 8)}</span>
                </div>
              ) : null}

              <div
                className={`preview__stage${prepDirty ? ' is-stale' : ''}${
                  busy ? ' is-busy' : ''
                }`}
              >
                {compareAfter && compareBefore ? (
                  <ImageCompare
                    firstImage={compareBefore}
                    secondImage={compareAfter}
                    alt={`Preview of ${job!.original_filename}`}
                  />
                ) : (
                  <div className={`preview__frame${busy ? ' preview__frame--busy' : ''}`}>
                    <img
                      src={previewSrc!}
                      alt={
                        job
                          ? `Preview of ${job.original_filename}`
                          : 'Selected photo preview'
                      }
                    />
                  </div>
                )}
                {prepDirty ? (
                  <button
                    type="button"
                    className="preview__stale"
                    onClick={handlePrepare}
                    disabled={!job || busy}
                  >
                    Preview outdated · Update
                  </button>
                ) : null}
              </div>

              {uploading ? (
                <div className="progress" aria-hidden="true">
                  <span className="progress__bar" style={{ width: `${progress}%` }} />
                </div>
              ) : null}

              {error ? (
                <p className="banner banner--error" role="alert">
                  {error}
                </p>
              ) : null}
              {notice && !prepDirty ? (
                <p className="banner banner--ok" role="status">
                  {notice}
                </p>
              ) : null}

              {job && !uploading ? (
                <div className="studio-tools">
                  <div className="studio-tools__block">
                    <label className="studio-tools__label" htmlFor="ai-edit-prompt">
                      AI edit
                    </label>
                    <p className="studio-tools__hint">
                      Describe a change — remove background, simplify lines, boost subject…
                    </p>
                    <div className="studio-tools__row">
                      <input
                        id="ai-edit-prompt"
                        className="studio-input"
                        type="text"
                        value={editPrompt}
                        onChange={(e) => setEditPrompt(e.target.value)}
                        placeholder="e.g. remove background, keep the couple"
                        disabled={busy}
                        maxLength={800}
                      />
                      <button
                        type="button"
                        className="btn btn--quiet"
                        onClick={handleEdit}
                        disabled={busy || editPrompt.trim().length < 3}
                      >
                        Apply edit
                      </button>
                    </div>
                  </div>

                  <div className="studio-tools__block">
                    <div className="studio-tools__heading">
                      <span className="studio-tools__label">Laser prep</span>
                      {prepDirty ? (
                        <span className="prep-pill" role="status">
                          Needs update
                        </span>
                      ) : isReady ? (
                        <span className="prep-pill prep-pill--ok">Up to date</span>
                      ) : null}
                    </div>
                    <p className="studio-tools__hint">{MODE_HELP[prep.mode]}</p>

                    <div className="prep-modes" role="group" aria-label="Dither / finish mode">
                      {PREP_MODES.map((mode) => (
                        <button
                          key={mode}
                          type="button"
                          className={`prep-mode${prep.mode === mode ? ' is-active' : ''}`}
                          onClick={() => updatePrep({ mode })}
                          disabled={busy}
                        >
                          {mode}
                        </button>
                      ))}
                    </div>

                    <div className="prep-sliders">
                      <label className="prep-slider">
                        <span>Contrast {prep.contrast.toFixed(2)}</span>
                        <input
                          type="range"
                          min={0.5}
                          max={2.5}
                          step={0.05}
                          value={prep.contrast}
                          onChange={(e) => updatePrep({ contrast: Number(e.target.value) })}
                          disabled={busy}
                        />
                      </label>
                      <label className="prep-slider">
                        <span>Brightness {prep.brightness.toFixed(2)}</span>
                        <input
                          type="range"
                          min={0.4}
                          max={2.0}
                          step={0.05}
                          value={prep.brightness}
                          onChange={(e) => updatePrep({ brightness: Number(e.target.value) })}
                          disabled={busy}
                        />
                      </label>
                      <label className="prep-slider">
                        <span>Sharpness {prep.sharpness.toFixed(2)}</span>
                        <input
                          type="range"
                          min={0}
                          max={3}
                          step={0.05}
                          value={prep.sharpness}
                          onChange={(e) => updatePrep({ sharpness: Number(e.target.value) })}
                          disabled={busy}
                        />
                      </label>
                      <label className="prep-slider">
                        <span>Denoise {prep.denoise.toFixed(2)}</span>
                        <input
                          type="range"
                          min={0}
                          max={1}
                          step={0.05}
                          value={prep.denoise}
                          onChange={(e) => updatePrep({ denoise: Number(e.target.value) })}
                          disabled={busy}
                        />
                      </label>
                      {prep.mode === 'threshold' ? (
                        <label className="prep-slider">
                          <span>Threshold {prep.threshold}</span>
                          <input
                            type="range"
                            min={1}
                            max={254}
                            step={1}
                            value={prep.threshold}
                            onChange={(e) => updatePrep({ threshold: Number(e.target.value) })}
                            disabled={busy}
                          />
                        </label>
                      ) : null}
                      <label className="prep-check">
                        <input
                          type="checkbox"
                          checked={prep.invert}
                          onChange={(e) => updatePrep({ invert: e.target.checked })}
                          disabled={busy}
                        />
                        Invert (dark materials / coated)
                      </label>
                    </div>

                    <div className="prep-size">
                      <label className="prep-field">
                        <span>Width (mm)</span>
                        <input
                          type="number"
                          min={5}
                          max={600}
                          step={1}
                          value={prep.width_mm ?? ''}
                          onChange={(e) =>
                            updatePrep({
                              width_mm: e.target.value === '' ? null : Number(e.target.value),
                            })
                          }
                          disabled={busy}
                        />
                      </label>
                      <label className="prep-field">
                        <span>Height (mm)</span>
                        <input
                          type="number"
                          min={5}
                          max={600}
                          step={1}
                          value={prep.height_mm ?? ''}
                          placeholder="auto"
                          onChange={(e) =>
                            updatePrep({
                              height_mm: e.target.value === '' ? null : Number(e.target.value),
                            })
                          }
                          disabled={busy}
                        />
                      </label>
                      <label className="prep-field">
                        <span>DPI</span>
                        <input
                          type="number"
                          min={72}
                          max={600}
                          step={1}
                          value={prep.dpi}
                          onChange={(e) => updatePrep({ dpi: Number(e.target.value) || 300 })}
                          disabled={busy}
                        />
                      </label>
                    </div>

                    <div className="prep-apply">
                      <button
                        type="button"
                        className={`btn${prepDirty || needsFirstPrepare ? ' btn--ink' : ' btn--quiet'}`}
                        onClick={handlePrepare}
                        disabled={!job || busy}
                      >
                        {applyLabel}
                      </button>
                      {prepDirty ? (
                        <span className="prep-apply__note">Applies contrast, dither & size</span>
                      ) : null}
                    </div>
                  </div>
                </div>
              ) : null}

              <div className="actions actions--dock">
                {isReady && !prepDirty ? (
                  <a
                    className="btn btn--ink"
                    href={compareAfter || mediaUrl(job!.prepared_url || job!.current_url)}
                    download={`${(job?.original_filename || 'image').replace(/\.[^.]+$/, '')}-laser.png`}
                  >
                    Download laser file
                  </a>
                ) : (
                  <button
                    type="button"
                    className="btn btn--ink"
                    disabled
                    title={
                      needsFirstPrepare
                        ? 'Prepare the image first'
                        : 'Update the preview first'
                    }
                  >
                    Download laser file
                  </button>
                )}
                <button type="button" className="btn btn--quiet" onClick={reset} disabled={busy}>
                  New photo
                </button>
              </div>
            </div>
          </section>
        )}
      </div>

      {recent.length > 0 ? (
        <aside className="recent" aria-label="Recent jobs">
          <div className="recent__head">
            <h3 className="recent__title">Recent</h3>
          </div>
          <ul className="recent__list">
            {recent.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={`recent__item${job?.id === item.id ? ' is-active' : ''}`}
                  onClick={() => openRecent(item)}
                >
                  <span
                    className="recent__thumb"
                    style={{
                      backgroundImage: `url(${cacheBust(item.current_url, item.updated_at)})`,
                    }}
                    aria-hidden="true"
                  />
                  <span className="recent__meta">
                    <span className="recent__name">{item.original_filename}</span>
                    <StatusBadge status={item.status} />
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>
      ) : null}
    </div>
  )
}
