import { http } from './client'
import type { AuthResponse, Bookmark, Category, ListResult, Tag, TagWithCount, User } from '../types'

export const authApi = {
  async register(username: string, password: string): Promise<AuthResponse> {
    const { data } = await http.post<AuthResponse>('/auth/register', { username, password })
    return data
  },
  async login(username: string, password: string): Promise<AuthResponse> {
    const { data } = await http.post<AuthResponse>('/auth/login', { username, password })
    return data
  },
  async me(): Promise<User> {
    const { data } = await http.get<User>('/auth/me')
    return data
  },
}

export interface BookmarkListParams {
  q?: string
  category_id?: number | null
  tag_id?: number | null
  is_favorite?: boolean
  uncategorized?: boolean
  page?: number
  page_size?: number
}

export interface BookmarkUpdatePayload {
  title?: string
  description?: string
  category_name?: string | null
  tags?: string[]
  is_favorite?: boolean
}

export const bookmarksApi = {
  async create(payload: { url: string; category_name?: string | null; tags?: string[] }): Promise<Bookmark> {
    const { data } = await http.post<Bookmark>('/bookmarks', payload)
    return data
  },
  async list(params: BookmarkListParams = {}): Promise<ListResult<Bookmark>> {
    const { data } = await http.get<ListResult<Bookmark>>('/bookmarks', { params })
    return data
  },
  async get(id: number): Promise<Bookmark> {
    const { data } = await http.get<Bookmark>(`/bookmarks/${id}`)
    return data
  },
  async update(id: number, payload: BookmarkUpdatePayload): Promise<Bookmark> {
    const { data } = await http.put<Bookmark>(`/bookmarks/${id}`, payload)
    return data
  },
  async remove(id: number): Promise<void> {
    await http.delete(`/bookmarks/${id}`)
  },
  async refetch(id: number): Promise<Bookmark> {
    const { data } = await http.post<Bookmark>(`/bookmarks/${id}/refetch`)
    return data
  },
  async reorder(scope: string, ids: number[]): Promise<void> {
    await http.put('/bookmarks/reorder', { scope, ids })
  },
  async exportFile(format: 'json' | 'html'): Promise<void> {
    const resp = await http.get('/bookmarks/export', { params: { format }, responseType: 'blob' })
    const blob = resp.data as Blob
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bookmarks.${format}`
    a.click()
    URL.revokeObjectURL(url)
  },
  async importFile(data: string): Promise<{ imported: number; skipped: number }> {
    const { data: result } = await http.post<{ imported: number; skipped: number }>('/bookmarks/import', { data }, { timeout: 300000 })
    return result
  },
}

export const tagsApi = {
  async list(): Promise<TagWithCount[]> {
    const { data } = await http.get<TagWithCount[]>('/tags')
    return data
  },
  async create(name: string): Promise<Tag> {
    const { data } = await http.post<Tag>('/tags', { name })
    return data
  },
  async rename(id: number, name: string): Promise<Tag> {
    const { data } = await http.put<Tag>(`/tags/${id}`, { name })
    return data
  },
  async remove(id: number): Promise<void> {
    await http.delete(`/tags/${id}`)
  },
}

export const categoriesApi = {
  async list(): Promise<Category[]> {
    const { data } = await http.get<Category[]>('/categories')
    return data
  },
  async create(payload: { name: string; parent_id?: number | null }): Promise<Category> {
    const { data } = await http.post<Category>('/categories', payload)
    return data
  },
  async update(id: number, payload: { name?: string; parent_id?: number | null }): Promise<Category> {
    const { data } = await http.put<Category>(`/categories/${id}`, payload)
    return data
  },
  async remove(id: number): Promise<void> {
    await http.delete(`/categories/${id}`)
  },
}
