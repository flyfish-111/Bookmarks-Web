<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Sortable from 'sortablejs'
import { useBookmarksStore } from '../stores/bookmarks'
import { bookmarksApi } from '../api'
import BookmarkCard from '../components/BookmarkCard.vue'

const store = useBookmarksStore()
const gridRef = ref<HTMLElement | null>(null)
let sortable: Sortable | null = null

// 拖拽排序作用域：全部 / 某个分类 / 某个标签；搜索、星标、未分类视图下不支持
const scope = computed<string | null>(() => {
  const f = store.filters
  if (f.tag_id != null) return `tag:${f.tag_id}`
  if (f.category_id != null) return `cat:${f.category_id}`
  if (!f.q && !f.is_favorite && !f.uncategorized) return 'all'
  return null
})

function setupSortable() {
  if (sortable) {
    sortable.destroy()
    sortable = null
  }
  if (!gridRef.value || !scope.value) return
  const currentScope = scope.value
  sortable = Sortable.create(gridRef.value, {
    animation: 200,
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    dragClass: 'sortable-drag',
    filter: '.no-drag',
    onEnd: (evt) => {
      const { oldIndex, newIndex } = evt
      if (oldIndex === undefined || newIndex === undefined || oldIndex === newIndex) return
      const arr = [...store.items]
      const [moved] = arr.splice(oldIndex, 1)
      arr.splice(newIndex, 0, moved)
      store.items = arr
      bookmarksApi.reorder(currentScope, arr.map((i) => i.id))
    },
  })
}

onMounted(async () => {
  await store.load()
  await nextTick()
  setupSortable()
})

watch(scope, async () => {
  await nextTick()
  setupSortable()
})

onBeforeUnmount(() => {
  if (sortable) sortable.destroy()
})

function onPageChange(p: number) {
  store.setPage(p)
}
</script>

<template>
  <div class="list-view">
    <div class="list-header">
      <span class="result-count">共 {{ store.total }} 条收藏</span>
      <span v-if="scope" class="drag-hint">拖拽卡片可排序</span>
    </div>

    <div v-loading="store.loading">
      <div v-if="store.items.length > 0" ref="gridRef" class="grid">
        <BookmarkCard v-for="bm in store.items" :key="bm.id" :bookmark="bm" />
      </div>
      <el-empty v-else-if="!store.loading" description="还没有收藏，点右上角「添加收藏」开始吧" />
    </div>

    <div v-if="store.total > store.pageSize" class="pagination">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="store.total"
        :page-size="store.pageSize"
        :current-page="store.page"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.list-view {
  padding: 24px 28px;
  max-width: 1200px;
  margin: 0 auto;
}
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.result-count {
  font-size: 13px;
  color: #a89888;
}
.drag-hint {
  font-size: 12px;
  color: #c9bba8;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
}
.pagination {
  margin-top: 28px;
  display: flex;
  justify-content: center;
}
</style>
