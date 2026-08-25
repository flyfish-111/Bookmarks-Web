import { defineStore } from 'pinia'
import { ref } from 'vue'
import { bookmarksApi } from '../api'
import type { Bookmark } from '../types'
import { useMetaStore } from './meta'

export interface BookmarkFilters {
  q?: string
  category_id?: number | null
  tag_id?: number | null
  is_favorite?: boolean
  uncategorized?: boolean
}

export const useBookmarksStore = defineStore('bookmarks', () => {
  const items = ref<Bookmark[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const filters = ref<BookmarkFilters>({
    q: undefined,
    category_id: null,
    tag_id: null,
    is_favorite: undefined,
    uncategorized: undefined,
  })

  async function load() {
    loading.value = true
    try {
      const res = await bookmarksApi.list({ ...filters.value, page: page.value, page_size: pageSize.value })
      items.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  function setFilter(patch: Partial<BookmarkFilters>) {
    filters.value = { ...filters.value, ...patch }
    page.value = 1
    load()
  }

  function setPage(p: number) {
    page.value = p
    load()
  }

  async function create(payload: { url: string; category_name?: string | null; tags?: string[] }) {
    const bm = await bookmarksApi.create(payload)
    await load()
    useMetaStore().loadAll()
    return bm
  }

  async function update(
    id: number,
    payload: { title?: string; description?: string; category_name?: string | null; tags?: string[]; is_favorite?: boolean },
  ) {
    const bm = await bookmarksApi.update(id, payload)
    const idx = items.value.findIndex((it) => it.id === id)
    if (idx !== -1) items.value[idx] = bm
    useMetaStore().loadAll()
    return bm
  }

  async function remove(id: number) {
    await bookmarksApi.remove(id)
    const idx = items.value.findIndex((it) => it.id === id)
    if (idx !== -1) {
      items.value.splice(idx, 1)
      total.value -= 1
    }
    if (items.value.length === 0 && total.value > 0) {
      await load()
    }
    useMetaStore().loadAll()
  }

  return { items, total, page, pageSize, loading, filters, load, setFilter, setPage, create, update, remove }
})
