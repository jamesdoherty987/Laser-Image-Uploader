import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { StatusBadge } from '../components/StatusBadge'
import {
  adminCreateLandingImage,
  adminCreateProduct,
  adminCreateTemplate,
  adminDeleteJob,
  adminDeleteLandingImage,
  adminDeleteProduct,
  adminDeleteTemplate,
  adminDesktopInfo,
  adminDownloadDesktop,
  adminGetContact,
  adminListJobs,
  adminListLandingImages,
  adminListProducts,
  adminListTemplates,
  adminLogin,
  adminPrepareJob,
  adminUpdateContact,
  adminUpdateJobStatus,
  adminUpdateLandingImage,
  adminUpdateProduct,
  adminUpdateTemplate,
  formatMoney,
  getAdminToken,
  getErrorMessage,
  mediaUrl,
  setAdminToken,
  type DesktopInfo,
} from '../services/api'
import type { CraftTemplate, LandingImage, Product, SiteContact } from '../types/content'
import type { Job, JobStatus } from '../types/job'

type Tab = 'jobs' | 'shop' | 'desktop' | 'content'

function eurosToCents(value: string): number {
  const cleaned = value.replace(',', '.').trim()
  const num = Number.parseFloat(cleaned)
  if (!Number.isFinite(num) || num < 0) return 0
  return Math.round(num * 100)
}

function centsToEurosInput(cents: number): string {
  return (cents / 100).toFixed(2)
}

const JOB_FILTERS: Array<{ value: '' | JobStatus; label: string }> = [
  { value: '', label: 'All' },
  { value: 'ready', label: 'Laser ready' },
  { value: 'uploaded', label: 'Uploaded' },
  { value: 'edited', label: 'Edited' },
  { value: 'imported', label: 'Imported' },
  { value: 'failed', label: 'Failed' },
]

function formatWhen(iso: string) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export function AdminPage() {
  const [token, setToken] = useState<string | null>(() => getAdminToken())
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [tab, setTab] = useState<Tab>('jobs')

  const [jobs, setJobs] = useState<Job[]>([])
  const [jobFilter, setJobFilter] = useState<'' | JobStatus>('')
  const [desktop, setDesktop] = useState<DesktopInfo | null>(null)

  const [images, setImages] = useState<LandingImage[]>([])
  const [templates, setTemplates] = useState<CraftTemplate[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [editingPriceId, setEditingPriceId] = useState<string | null>(null)
  const [editingPriceValue, setEditingPriceValue] = useState('')

  const [imageTitle, setImageTitle] = useState('')
  const [imageAlt, setImageAlt] = useState('')
  const [imageSection, setImageSection] = useState('hero')
  const [imageFile, setImageFile] = useState<File | null>(null)

  const [templateName, setTemplateName] = useState('')
  const [templateDescription, setTemplateDescription] = useState('')
  const [templateCategory, setTemplateCategory] = useState('Wood')
  const [templateFile, setTemplateFile] = useState<File | null>(null)

  const [productName, setProductName] = useState('')
  const [productDescription, setProductDescription] = useState('')
  const [productCategory, setProductCategory] = useState('Wood')
  const [productPrice, setProductPrice] = useState('25.00')
  const [productCurrency, setProductCurrency] = useState('EUR')
  const [productFile, setProductFile] = useState<File | null>(null)

  const [contact, setContact] = useState<SiteContact | null>(null)
  const [contactForm, setContactForm] = useState({
    business_name: '',
    tagline: '',
    email: '',
    phone: '',
    location: '',
    hours: '',
    instagram: '',
    website: '',
    message: '',
  })

  const refreshJobs = useCallback(async () => {
    const next = await adminListJobs({
      limit: 200,
      status: jobFilter || undefined,
    })
    setJobs(next)
  }, [jobFilter])

  const refreshContent = useCallback(async () => {
    const [nextImages, nextTemplates, nextContact] = await Promise.all([
      adminListLandingImages(),
      adminListTemplates(),
      adminGetContact(),
    ])
    setImages(nextImages)
    setTemplates(nextTemplates)
    setContact(nextContact)
    setContactForm({
      business_name: nextContact.business_name,
      tagline: nextContact.tagline,
      email: nextContact.email,
      phone: nextContact.phone,
      location: nextContact.location,
      hours: nextContact.hours,
      instagram: nextContact.instagram,
      website: nextContact.website,
      message: nextContact.message,
    })
  }, [])

  const refreshProducts = useCallback(async () => {
    setProducts(await adminListProducts())
  }, [])

  const refreshDesktop = useCallback(async () => {
    setDesktop(await adminDesktopInfo())
  }, [])

  useEffect(() => {
    if (!token) return
    ;(async () => {
      try {
        await Promise.all([refreshJobs(), refreshContent(), refreshProducts(), refreshDesktop()])
      } catch (err) {
        setError(getErrorMessage(err))
        setAdminToken(null)
        setToken(null)
      }
    })()
  }, [token, refreshJobs, refreshContent, refreshProducts, refreshDesktop])

  useEffect(() => {
    if (!token || tab !== 'jobs') return
    const id = window.setInterval(() => {
      refreshJobs().catch(() => undefined)
    }, 12_000)
    return () => window.clearInterval(id)
  }, [token, tab, refreshJobs])

  const readyCount = useMemo(
    () => jobs.filter((j) => j.status === 'ready').length,
    [jobs],
  )

  async function handleLogin(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const next = await adminLogin(username, password)
      setToken(next)
      setPassword('')
      setNotice('Signed in.')
      setTab('jobs')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  function logout() {
    setAdminToken(null)
    setToken(null)
    setJobs([])
    setImages([])
    setTemplates([])
    setProducts([])
    setContact(null)
    setDesktop(null)
  }

  async function handleSaveContact(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const next = await adminUpdateContact(contactForm)
      setContact(next)
      setNotice('Contact details saved — they show on the landing page.')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleAddProduct(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await adminCreateProduct({
        name: productName,
        description: productDescription,
        category: productCategory,
        price_cents: eurosToCents(productPrice),
        currency: productCurrency,
        file: productFile,
      })
      setProductName('')
      setProductDescription('')
      setProductPrice('25.00')
      setProductFile(null)
      setNotice('Product added to shop.')
      await refreshProducts()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function saveProductPrice(product: Product) {
    setBusy(true)
    setError(null)
    try {
      await adminUpdateProduct(product.id, {
        price_cents: eurosToCents(editingPriceValue),
      })
      setEditingPriceId(null)
      setNotice('Price updated.')
      await refreshProducts()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleAddImage(e: FormEvent) {
    e.preventDefault()
    if (!imageFile) {
      setError('Choose an image file first.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await adminCreateLandingImage({
        file: imageFile,
        title: imageTitle,
        alt_text: imageAlt || imageTitle,
        section: imageSection,
      })
      setImageTitle('')
      setImageAlt('')
      setImageFile(null)
      setNotice('Landing image added.')
      await refreshContent()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleAddTemplate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await adminCreateTemplate({
        name: templateName,
        description: templateDescription,
        category: templateCategory,
        file: templateFile,
      })
      setTemplateName('')
      setTemplateDescription('')
      setTemplateFile(null)
      setNotice('Craft template added.')
      await refreshContent()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function runJobAction(label: string, action: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await action()
      setNotice(label)
      await refreshJobs()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function downloadDesktopZip() {
    setBusy(true)
    setError(null)
    try {
      const blob = await adminDownloadDesktop()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'galvin-crafts-desktop.zip'
      a.click()
      URL.revokeObjectURL(url)
      setNotice('Desktop connector download started.')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function copyToken() {
    if (!desktop?.pairing_token) return
    try {
      await navigator.clipboard.writeText(desktop.pairing_token)
      setNotice('Pairing token copied.')
    } catch {
      setError('Could not copy token — select and copy it manually.')
    }
  }

  if (!token) {
    return (
      <div className="admin">
        <div className="admin__card">
          <p className="admin__eyebrow">Galvin Crafts</p>
          <h1 className="admin__title">Admin login</h1>
          <form className="admin__form" onSubmit={handleLogin}>
            <label>
              Username
              <input value={username} onChange={(e) => setUsername(e.target.value)} required />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            {error ? <p className="banner banner--error">{error}</p> : null}
            <button className="btn btn--ink" type="submit" disabled={busy}>
              Sign in
            </button>
          </form>
          <Link className="admin__back" to="/">
            Back to site
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="admin admin--app">
      <header className="admin__top">
        <div>
          <p className="admin__eyebrow">Galvin Crafts</p>
          <h1 className="admin__title">Laser admin</h1>
          <p className="admin__help">
            Customer uploads land here so you can prepare, download, and cut them.
            {readyCount ? ` ${readyCount} ready for the laser.` : ''}
          </p>
        </div>
        <div className="admin__top-actions">
          <Link className="btn btn--quiet" to="/">
            View site
          </Link>
          <button type="button" className="btn btn--ink" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      <nav className="admin__tabs" aria-label="Admin sections">
        <button
          type="button"
          className={tab === 'jobs' ? 'admin__tab admin__tab--active' : 'admin__tab'}
          onClick={() => setTab('jobs')}
        >
          Incoming jobs
        </button>
        <button
          type="button"
          className={tab === 'shop' ? 'admin__tab admin__tab--active' : 'admin__tab'}
          onClick={() => setTab('shop')}
        >
          Shop
        </button>
        <button
          type="button"
          className={tab === 'desktop' ? 'admin__tab admin__tab--active' : 'admin__tab'}
          onClick={() => setTab('desktop')}
        >
          Desktop app
        </button>
        <button
          type="button"
          className={tab === 'content' ? 'admin__tab admin__tab--active' : 'admin__tab'}
          onClick={() => setTab('content')}
        >
          Site content
        </button>
      </nav>

      {error ? <p className="banner banner--error">{error}</p> : null}
      {notice ? <p className="banner banner--ok">{notice}</p> : null}

      {tab === 'jobs' ? (
        <section className="admin__section">
          <div className="admin__section-head">
            <div>
              <h2>Customer uploads</h2>
              <p className="admin__help">
                Every image customers submit appears here. Prepare for laser, download the file, or
                mark it imported after CorelDRAW.
              </p>
            </div>
            <button
              type="button"
              className="btn btn--quiet"
              disabled={busy}
              onClick={() =>
                runJobAction('Job list refreshed.', async () => {
                  await refreshJobs()
                })
              }
            >
              Refresh
            </button>
          </div>

          <div className="admin__filters">
            {JOB_FILTERS.map((f) => (
              <button
                key={f.label}
                type="button"
                className={
                  jobFilter === f.value
                    ? 'admin__filter admin__filter--active'
                    : 'admin__filter'
                }
                onClick={() => setJobFilter(f.value)}
              >
                {f.label}
              </button>
            ))}
          </div>

          {jobs.length === 0 ? (
            <p className="admin__empty">No customer uploads yet.</p>
          ) : (
            <ul className="admin__list admin__list--jobs">
              {jobs.map((job) => {
                const preview = job.prepared_url || job.edited_url || job.current_url || job.original_url
                const laserUrl = job.prepared_url
                return (
                  <li key={job.id} className="admin__job">
                    <a
                      className="admin__job-thumb"
                      href={mediaUrl(preview)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <img src={mediaUrl(preview)} alt={job.original_filename} />
                    </a>
                    <div className="admin__job-body">
                      <div className="admin__job-title">
                        <strong>{job.original_filename}</strong>
                        <StatusBadge status={job.status} />
                      </div>
                      <p>
                        {formatWhen(job.created_at)}
                        {job.width && job.height ? ` · ${job.width}×${job.height}` : ''}
                      </p>
                      {job.error_message ? (
                        <p className="admin__job-error">{job.error_message}</p>
                      ) : null}
                      <div className="admin__job-actions">
                        {!laserUrl ? (
                          <button
                            type="button"
                            className="btn btn--ink"
                            disabled={busy}
                            onClick={() =>
                              runJobAction('Prepared for laser.', async () => {
                                await adminPrepareJob(job.id)
                              })
                            }
                          >
                            Prepare for laser
                          </button>
                        ) : (
                          <a
                            className="btn btn--ink"
                            href={mediaUrl(laserUrl)}
                            download={`${job.original_filename.replace(/\.[^.]+$/, '')}-laser.png`}
                          >
                            Download laser file
                          </a>
                        )}
                        <a
                          className="btn btn--quiet"
                          href={mediaUrl(job.original_url)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Original
                        </a>
                        {job.status === 'ready' || job.status === 'downloading' ? (
                          <button
                            type="button"
                            className="btn btn--quiet"
                            disabled={busy}
                            onClick={() =>
                              runJobAction('Marked imported.', async () => {
                                await adminUpdateJobStatus(job.id, 'imported')
                              })
                            }
                          >
                            Mark imported
                          </button>
                        ) : null}
                        {job.status === 'imported' ? (
                          <button
                            type="button"
                            className="btn btn--quiet"
                            disabled={busy}
                            onClick={() =>
                              runJobAction('Re-opened as ready.', async () => {
                                await adminUpdateJobStatus(job.id, 'ready')
                              })
                            }
                          >
                            Re-open
                          </button>
                        ) : null}
                        <button
                          type="button"
                          className="btn btn--quiet"
                          disabled={busy}
                          onClick={() =>
                            runJobAction('Job deleted.', async () => {
                              await adminDeleteJob(job.id)
                            })
                          }
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </section>
      ) : null}

      {tab === 'shop' ? (
        <section className="admin__section">
          <h2>Shop products</h2>
          <p className="admin__help">
            Products appear in the public Shop section. Set name, photo, and price now — Stripe
            checkout can be wired later.
          </p>
          <form className="admin__form admin__form--grid" onSubmit={handleAddProduct}>
            <label>
              Name
              <input
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                required
              />
            </label>
            <label>
              Category
              <input
                value={productCategory}
                onChange={(e) => setProductCategory(e.target.value)}
              />
            </label>
            <label>
              Price
              <input
                value={productPrice}
                onChange={(e) => setProductPrice(e.target.value)}
                inputMode="decimal"
                placeholder="25.00"
                required
              />
            </label>
            <label>
              Currency
              <select
                value={productCurrency}
                onChange={(e) => setProductCurrency(e.target.value)}
              >
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="USD">USD</option>
              </select>
            </label>
            <label className="admin__span">
              Description
              <textarea
                value={productDescription}
                onChange={(e) => setProductDescription(e.target.value)}
                rows={3}
              />
            </label>
            <label>
              Image
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(e) => setProductFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <button className="btn btn--ink" type="submit" disabled={busy}>
              Add product
            </button>
          </form>

          {products.length === 0 ? (
            <p className="admin__empty">No shop products yet.</p>
          ) : (
            <ul className="admin__list">
              {products.map((product) => (
                <li key={product.id} className="admin__row admin__row--product">
                  {product.image_url ? (
                    <img src={mediaUrl(product.image_url)} alt={product.name} />
                  ) : (
                    <div className="admin__thumb-empty" />
                  )}
                  <div>
                    <strong>{product.name}</strong>
                    <p>
                      {product.category} · {product.is_active ? 'Listed' : 'Hidden'}
                    </p>
                    <p>{product.description}</p>
                    {editingPriceId === product.id ? (
                      <div className="admin__price-edit">
                        <input
                          value={editingPriceValue}
                          onChange={(e) => setEditingPriceValue(e.target.value)}
                          inputMode="decimal"
                          aria-label="Price"
                        />
                        <button
                          type="button"
                          className="btn btn--ink"
                          disabled={busy}
                          onClick={() => saveProductPrice(product)}
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          className="btn btn--quiet"
                          onClick={() => setEditingPriceId(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <p className="admin__price">
                        {formatMoney(product.price_cents, product.currency)}
                      </p>
                    )}
                  </div>
                  <div className="admin__row-actions">
                    {editingPriceId !== product.id ? (
                      <button
                        type="button"
                        className="btn btn--quiet"
                        onClick={() => {
                          setEditingPriceId(product.id)
                          setEditingPriceValue(centsToEurosInput(product.price_cents))
                        }}
                      >
                        Edit price
                      </button>
                    ) : null}
                    <button
                      type="button"
                      className="btn btn--quiet"
                      onClick={async () => {
                        await adminUpdateProduct(product.id, {
                          is_active: !product.is_active,
                        })
                        await refreshProducts()
                      }}
                    >
                      {product.is_active ? 'Hide' : 'Show'}
                    </button>
                    <button
                      type="button"
                      className="btn btn--quiet"
                      onClick={async () => {
                        await adminDeleteProduct(product.id)
                        await refreshProducts()
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}

      {tab === 'desktop' ? (
        <section className="admin__section">
          <h2>Desktop connector</h2>
          <p className="admin__help">
            Install this on the Windows PC next to the laser. It pulls laser-ready jobs into a
            folder and opens them in CorelDRAW.
          </p>

          <div className="admin__desktop">
            <button
              type="button"
              className="btn btn--ink"
              disabled={busy}
              onClick={downloadDesktopZip}
            >
              Download desktop app (.zip)
            </button>
            <button
              type="button"
              className="btn btn--quiet"
              disabled={busy}
              onClick={() =>
                runJobAction('Desktop info refreshed.', async () => {
                  await refreshDesktop()
                })
              }
            >
              Refresh token
            </button>
          </div>

          {desktop ? (
            <div className="admin__token-box">
              <p className="admin__help">{desktop.instructions}</p>
              <label>
                API base URL
                <input value={desktop.api_base} readOnly />
              </label>
              <label>
                Pairing token
                <div className="admin__token-row">
                  <input value={desktop.pairing_token} readOnly />
                  <button type="button" className="btn btn--quiet" onClick={copyToken}>
                    Copy
                  </button>
                </div>
              </label>
              <ol className="admin__steps">
                <li>Download and unzip on the laser PC.</li>
                <li>
                  Run <code>run_connector.bat</code> (or <code>python main.py --setup</code>).
                </li>
                <li>Paste the API URL and pairing token when asked.</li>
                <li>Leave it running — ready jobs download automatically.</li>
              </ol>
            </div>
          ) : null}
        </section>
      ) : null}

      {tab === 'content' ? (
        <>
          <section className="admin__section">
            <h2>Contact details</h2>
            <p className="admin__help">
              Shown in the Contact section and footer on the public site.
              {contact ? ` Last saved ${formatWhen(contact.updated_at)}.` : ''}
            </p>
            <form className="admin__form admin__form--grid" onSubmit={handleSaveContact}>
              <label>
                Business name
                <input
                  value={contactForm.business_name}
                  onChange={(e) =>
                    setContactForm((prev) => ({ ...prev, business_name: e.target.value }))
                  }
                />
              </label>
              <label>
                Tagline
                <input
                  value={contactForm.tagline}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, tagline: e.target.value }))}
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={contactForm.email}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, email: e.target.value }))}
                />
              </label>
              <label>
                Phone
                <input
                  value={contactForm.phone}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, phone: e.target.value }))}
                />
              </label>
              <label>
                Location
                <input
                  value={contactForm.location}
                  onChange={(e) =>
                    setContactForm((prev) => ({ ...prev, location: e.target.value }))
                  }
                />
              </label>
              <label>
                Hours
                <input
                  value={contactForm.hours}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, hours: e.target.value }))}
                />
              </label>
              <label>
                Instagram
                <input
                  value={contactForm.instagram}
                  onChange={(e) =>
                    setContactForm((prev) => ({ ...prev, instagram: e.target.value }))
                  }
                  placeholder="@galvincrafts"
                />
              </label>
              <label>
                Website
                <input
                  value={contactForm.website}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, website: e.target.value }))}
                  placeholder="https://"
                />
              </label>
              <label className="admin__span">
                Message
                <textarea
                  value={contactForm.message}
                  onChange={(e) => setContactForm((prev) => ({ ...prev, message: e.target.value }))}
                  rows={3}
                />
              </label>
              <button className="btn btn--ink" type="submit" disabled={busy}>
                Save contact
              </button>
            </form>
          </section>

          <section className="admin__section">
            <h2>Landing images</h2>
            <p className="admin__help">
              Hero images appear in the top showcase. Gallery images show lower on the page.
            </p>
            <form className="admin__form admin__form--grid" onSubmit={handleAddImage}>
              <label>
                Title
                <input value={imageTitle} onChange={(e) => setImageTitle(e.target.value)} />
              </label>
              <label>
                Alt text
                <input value={imageAlt} onChange={(e) => setImageAlt(e.target.value)} />
              </label>
              <label>
                Section
                <select value={imageSection} onChange={(e) => setImageSection(e.target.value)}>
                  <option value="hero">Hero</option>
                  <option value="gallery">Gallery</option>
                </select>
              </label>
              <label>
                Image
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
                  required
                />
              </label>
              <button className="btn btn--ink" type="submit" disabled={busy}>
                Add image
              </button>
            </form>

            <ul className="admin__list">
              {images.map((image) => (
                <li key={image.id} className="admin__row">
                  <img src={mediaUrl(image.image_url)} alt={image.alt_text} />
                  <div>
                    <strong>{image.title || 'Untitled'}</strong>
                    <p>
                      {image.section} · {image.is_active ? 'Active' : 'Hidden'}
                    </p>
                  </div>
                  <div className="admin__row-actions">
                    <button
                      type="button"
                      className="btn btn--quiet"
                      onClick={async () => {
                        await adminUpdateLandingImage(image.id, { is_active: !image.is_active })
                        await refreshContent()
                      }}
                    >
                      {image.is_active ? 'Hide' : 'Show'}
                    </button>
                    <button
                      type="button"
                      className="btn btn--quiet"
                      onClick={async () => {
                        await adminDeleteLandingImage(image.id)
                        await refreshContent()
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="admin__section">
            <h2>Craft templates</h2>
            <p className="admin__help">
              Common crafts customers can browse and start from on the landing page.
            </p>
            <form className="admin__form admin__form--grid" onSubmit={handleAddTemplate}>
              <label>
                Name
                <input
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  required
                />
              </label>
              <label>
                Category
                <input
                  value={templateCategory}
                  onChange={(e) => setTemplateCategory(e.target.value)}
                />
              </label>
              <label className="admin__span">
                Description
                <textarea
                  value={templateDescription}
                  onChange={(e) => setTemplateDescription(e.target.value)}
                  rows={3}
                />
              </label>
              <label>
                Image
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(e) => setTemplateFile(e.target.files?.[0] ?? null)}
                />
              </label>
              <button className="btn btn--ink" type="submit" disabled={busy}>
                Add template
              </button>
            </form>

            <ul className="admin__list">
              {templates.map((template) => (
                <li key={template.id} className="admin__row">
                  {template.image_url ? (
                    <img src={mediaUrl(template.image_url)} alt={template.name} />
                  ) : (
                    <div className="admin__thumb-empty" />
                  )}
                  <div>
                    <strong>{template.name}</strong>
                    <p>
                      {template.category} · {template.is_active ? 'Active' : 'Hidden'}
                    </p>
                    <p>{template.description}</p>
                  </div>
                  <div className="admin__row-actions">
                    <button
                      type="button"
                      className="btn btn--quiet"
                      onClick={async () => {
                        await adminUpdateTemplate(template.id, { is_active: !template.is_active })
                        await refreshContent()
                      }}
                    >
                      {template.is_active ? 'Hide' : 'Show'}
                    </button>
                    <button
                      type="button"
                      className="btn btn--quiet"
                      onClick={async () => {
                        await adminDeleteTemplate(template.id)
                        await refreshContent()
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </>
      ) : null}
    </div>
  )
}
