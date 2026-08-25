export interface Tag {
  id: number
  name: string
}

export interface TagWithCount extends Tag {
  count: number
}

export interface Category {
  id: number
  name: string
  parent_id: number | null
  sort_order: number
  count: number
}

export interface Bookmark {
  id: number
  url: string
  title: string
  description: string
  content_markdown: string
  favicon_url: string
  category_id: number | null
  is_favorite: boolean
  created_at: string
  updated_at: string
  tags: Tag[]
  category: Category | null
}

export interface ListResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface User {
  id: number
  username: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}
