import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AuroraHero } from '../components/aceternity/AuroraHero'
import { StudioPanel } from '../components/StudioPanel'
import {
  fetchContact,
  fetchProducts,
  fetchTemplates,
  formatMoney,
  mediaUrl,
} from '../services/api'
import type { CraftTemplate, Product, SiteContact } from '../types/content'

function instagramHref(handle: string): string {
  const cleaned = handle.trim().replace(/^@/, '')
  if (!cleaned) return '#'
  if (cleaned.startsWith('http://') || cleaned.startsWith('https://')) return cleaned
  return `https://instagram.com/${cleaned}`
}

export function HomePage() {
  const [templates, setTemplates] = useState<CraftTemplate[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [contact, setContact] = useState<SiteContact | null>(null)

  useEffect(() => {
    let alive = true
    async function load() {
      try {
        const [nextTemplates, nextProducts, nextContact] = await Promise.all([
          fetchTemplates(),
          fetchProducts(),
          fetchContact(),
        ])
        if (!alive) return
        setTemplates(nextTemplates)
        setProducts(nextProducts)
        setContact(nextContact)
      } catch {
        if (!alive) return
        setTemplates([])
        setProducts([])
        setContact(null)
      }
    }
    void load()
    return () => {
      alive = false
    }
  }, [])

  const brand = contact?.business_name || 'Galvin Crafts'

  return (
    <div className="site site--light">
      <header className="site-header site-header--light">
        <div className="site-header__inner">
          <a className="site-header__brand" href="#top">
            {brand}
          </a>
          <nav className="site-header__nav" aria-label="Primary">
            <a className="site-header__link" href="#shop">
              Shop
            </a>
            <a className="site-header__link" href="#templates">
              Templates
            </a>
            <a className="site-header__link" href="#contact">
              Contact
            </a>
            <Link className="site-header__link site-header__link--muted" to="/admin">
              Admin
            </Link>
            <a className="site-header__cta" href="#studio">
              Upload
            </a>
          </nav>
        </div>
      </header>

      <main id="top">
        <AuroraHero>
          <p className="hero__eyebrow">{brand}</p>
          <h1 className="hero__title">Photo to laser-ready</h1>
          <p className="hero__sub">Upload a photo. Prepare it for engraving.</p>
          <div className="hero__actions">
            <a className="btn btn--ink" href="#studio">
              Start upload
            </a>
          </div>
        </AuroraHero>

        <section className="studio" id="studio" aria-label="Upload">
          <div className="section section--studio">
            <StudioPanel />
          </div>
        </section>

        <section className="section" id="shop" aria-labelledby="shop-title">
          <div className="section__head">
            <div>
              <h2 className="section__title" id="shop-title">
                Shop
              </h2>
              <p className="section__lede">
                Laser-cut wooden crafts and custom pieces ready to order.
              </p>
            </div>
            <Link className="section__action" to="/admin">
              Manage products
            </Link>
          </div>
          {products.length > 0 ? (
            <div className="product-grid">
              {products.map((product) => (
                <article key={product.id} className="product-card">
                  {product.image_url ? (
                    <img src={mediaUrl(product.image_url)} alt={product.name} />
                  ) : (
                    <div className="product-card__empty" />
                  )}
                  <div className="product-card__body">
                    <p className="product-card__cat">{product.category}</p>
                    <div className="product-card__title-row">
                      <h3>{product.name}</h3>
                      <p className="product-card__price">
                        {formatMoney(product.price_cents, product.currency)}
                      </p>
                    </div>
                    <p>{product.description}</p>
                    <button type="button" className="btn btn--quiet" disabled title="Stripe coming soon">
                      Buy soon
                    </button>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-hint">
              No products yet. Add some in <Link to="/admin">Admin</Link>.
            </p>
          )}
        </section>

        <section className="section" id="templates" aria-labelledby="templates-title">
          <div className="section__head">
            <h2 className="section__title" id="templates-title">
              Craft templates
            </h2>
            <Link className="section__action" to="/admin">
              Manage templates
            </Link>
          </div>
          {templates.length > 0 ? (
            <div className="template-grid">
              {templates.map((template) => (
                <article key={template.id} className="template-card">
                  {template.image_url ? (
                    <img src={mediaUrl(template.image_url)} alt={template.name} />
                  ) : (
                    <div className="template-card__empty" />
                  )}
                  <div className="template-card__body">
                    <p className="template-card__cat">{template.category}</p>
                    <h3>{template.name}</h3>
                    <p>{template.description}</p>
                    <a className="btn btn--quiet" href="#studio">
                      Use this craft
                    </a>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-hint">
              No templates yet. Add some in <Link to="/admin">Admin</Link>.
            </p>
          )}
        </section>

        <section className="section section--contact" id="contact" aria-labelledby="contact-title">
          <div className="section__head">
            <h2 className="section__title" id="contact-title">
              Contact
            </h2>
            <Link className="section__action" to="/admin">
              Edit contact
            </Link>
          </div>
          {contact ? (
            <div className="contact-panel">
              <div className="contact-panel__intro">
                <p className="contact-panel__eyebrow">{contact.tagline || brand}</p>
                <h3>{brand}</h3>
                {contact.message ? <p>{contact.message}</p> : null}
              </div>
              <ul className="contact-panel__list">
                {contact.email ? (
                  <li>
                    <span>Email</span>
                    <a href={`mailto:${contact.email}`}>{contact.email}</a>
                  </li>
                ) : null}
                {contact.phone ? (
                  <li>
                    <span>Phone</span>
                    <a href={`tel:${contact.phone.replace(/\s+/g, '')}`}>{contact.phone}</a>
                  </li>
                ) : null}
                {contact.location ? (
                  <li>
                    <span>Location</span>
                    <strong>{contact.location}</strong>
                  </li>
                ) : null}
                {contact.hours ? (
                  <li>
                    <span>Hours</span>
                    <strong>{contact.hours}</strong>
                  </li>
                ) : null}
                {contact.instagram ? (
                  <li>
                    <span>Instagram</span>
                    <a href={instagramHref(contact.instagram)} target="_blank" rel="noreferrer">
                      {contact.instagram}
                    </a>
                  </li>
                ) : null}
                {contact.website ? (
                  <li>
                    <span>Web</span>
                    <a href={contact.website} target="_blank" rel="noreferrer">
                      {contact.website.replace(/^https?:\/\//, '')}
                    </a>
                  </li>
                ) : null}
              </ul>
            </div>
          ) : (
            <p className="empty-hint">
              Contact details coming soon. Add them in <Link to="/admin">Admin</Link>.
            </p>
          )}
        </section>
      </main>

      <footer className="site-footer">
        <div>
          <div className="site-footer__brand">{brand}</div>
          <p>{contact?.tagline || 'Photo to laser-ready artwork.'}</p>
          {contact?.email ? (
            <p>
              <a href={`mailto:${contact.email}`}>{contact.email}</a>
              {contact.phone ? ` · ${contact.phone}` : ''}
            </p>
          ) : null}
        </div>
        <nav className="site-footer__nav" aria-label="Footer">
          <a href="#studio">Upload</a>
          <a href="#shop">Shop</a>
          <a href="#contact">Contact</a>
          <Link to="/admin">Admin</Link>
        </nav>
      </footer>
    </div>
  )
}
