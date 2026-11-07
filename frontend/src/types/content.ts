export type LandingImage = {
  id: string
  title: string
  alt_text: string
  section: 'hero' | 'gallery' | string
  image_url: string
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type CraftTemplate = {
  id: string
  name: string
  description: string
  category: string
  image_url: string | null
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type Product = {
  id: string
  name: string
  description: string
  category: string
  price_cents: number
  currency: string
  image_url: string | null
  sort_order: number
  is_active: boolean
  stripe_price_id: string | null
  created_at: string
  updated_at: string
}

export type SiteContact = {
  business_name: string
  tagline: string
  email: string
  phone: string
  location: string
  hours: string
  instagram: string
  website: string
  message: string
  updated_at: string
}
