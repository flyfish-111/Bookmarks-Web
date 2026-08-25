import { defineStore } from 'pinia'
import { ref } from 'vue'
import { categoriesApi, tagsApi } from '../api'
import type { Category, TagWithCount } from '../types'

export const useMetaStore = defineStore('meta', () => {
  const tags = ref<TagWithCount[]>([])
  const categories = ref<Category[]>([])

  async function loadTags() {
    tags.value = await tagsApi.list()
  }
  async function loadCategories() {
    categories.value = await categoriesApi.list()
  }
  async function loadAll() {
    await Promise.all([loadTags(), loadCategories()])
  }

  async function createTag(name: string) {
    await tagsApi.create(name)
    await loadTags()
  }
  async function removeTag(id: number) {
    await tagsApi.remove(id)
    await loadTags()
  }
  async function renameTag(id: number, name: string) {
    await tagsApi.rename(id, name)
    await loadTags()
  }
  async function createCategory(name: string, parentId: number | null = null) {
    await categoriesApi.create({ name, parent_id: parentId })
    await loadCategories()
  }
  async function removeCategory(id: number) {
    await categoriesApi.remove(id)
    await loadCategories()
  }
  async function renameCategory(id: number, name: string) {
    await categoriesApi.update(id, { name })
    await loadCategories()
  }

  return { tags, categories, loadAll, loadTags, loadCategories, createTag, removeTag, renameTag, createCategory, removeCategory, renameCategory }
})
