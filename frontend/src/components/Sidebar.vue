<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, Collection, FolderOpened, Plus, Star } from '@element-plus/icons-vue'
import { useMetaStore } from '../stores/meta'
import { useBookmarksStore } from '../stores/bookmarks'
import type { Category } from '../types'

const router = useRouter()
const meta = useMetaStore()
const bookmarks = useBookmarksStore()

const catOpen = ref(true)
const tagOpen = ref(true)

interface CategoryNode {
  cat: Category
  depth: number
}

const flatCategories = computed<CategoryNode[]>(() => {
  const visited = new Set<number>()
  const result: CategoryNode[] = []
  const walk = (parentId: number | null, depth: number) => {
    meta.categories
      .filter((c) => c.parent_id === parentId)
      .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
      .forEach((c) => {
        if (visited.has(c.id)) return
        visited.add(c.id)
        result.push({ cat: c, depth })
        walk(c.id, depth + 1)
      })
  }
  walk(null, 0)
  return result
})

const isAll = computed(
  () =>
    !bookmarks.filters.category_id &&
    !bookmarks.filters.tag_id &&
    !bookmarks.filters.is_favorite &&
    !bookmarks.filters.uncategorized,
)
const isFav = computed(() => bookmarks.filters.is_favorite === true)
const isUncat = computed(() => bookmarks.filters.uncategorized === true)

function selectAll() {
  bookmarks.setFilter({ category_id: null, tag_id: null, is_favorite: undefined, uncategorized: undefined })
  router.push('/')
}
function selectFavorites() {
  bookmarks.setFilter({ is_favorite: true, category_id: null, tag_id: null, uncategorized: undefined })
  router.push('/')
}
function selectUncategorized() {
  bookmarks.setFilter({ uncategorized: true, category_id: null, tag_id: null, is_favorite: undefined })
  router.push('/')
}
function selectCategory(id: number) {
  bookmarks.setFilter({ category_id: id, tag_id: null, is_favorite: undefined, uncategorized: undefined })
  router.push('/')
}
function selectTag(id: number) {
  bookmarks.setFilter({ tag_id: id, category_id: null, is_favorite: undefined, uncategorized: undefined })
  router.push('/')
}

async function addCategory() {
  let value = ''
  try {
    const r = await ElMessageBox.prompt('请输入分类名称', '新建分类', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '名称不能为空',
    })
    value = r.value.trim()
  } catch {
    return
  }
  await meta.createCategory(value)
  ElMessage.success('分类已创建')
}

async function addTag() {
  let value = ''
  try {
    const r = await ElMessageBox.prompt('请输入标签名称', '新建标签', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '名称不能为空',
    })
    value = r.value.trim()
  } catch {
    return
  }
  await meta.createTag(value)
  ElMessage.success('标签已创建')
}

// —— 右键菜单（分类 / 标签通用） ——
interface CtxTarget {
  kind: 'category' | 'tag'
  id: number
  name: string
}

const menu = ref<{ visible: boolean; x: number; y: number; target: CtxTarget | null }>({
  visible: false,
  x: 0,
  y: 0,
  target: null,
})

function openCategoryMenu(e: MouseEvent, cat: Category) {
  menu.value = { visible: true, x: e.clientX, y: e.clientY, target: { kind: 'category', id: cat.id, name: cat.name } }
}
function openTagMenu(e: MouseEvent, id: number, name: string) {
  menu.value = { visible: true, x: e.clientX, y: e.clientY, target: { kind: 'tag', id, name } }
}
function closeMenu() {
  menu.value.visible = false
}

async function renameFromMenu() {
  const t = menu.value.target
  closeMenu()
  if (!t) return
  let value = ''
  try {
    const r = await ElMessageBox.prompt('重命名', '重命名', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '名称不能为空',
      inputValue: t.name,
    })
    value = r.value.trim()
  } catch {
    return
  }
  if (t.kind === 'category') await meta.renameCategory(t.id, value)
  else await meta.renameTag(t.id, value)
  ElMessage.success('已重命名')
}

async function removeFromMenu() {
  const t = menu.value.target
  closeMenu()
  if (!t) return
  const label =
    t.kind === 'category'
      ? '删除该分类？分类下的书签会变为「未分类」，不会被删除。'
      : '删除该标签？标签将从所有书签上移除。'
  try {
    await ElMessageBox.confirm(label, '提示', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  if (t.kind === 'category') {
    await meta.removeCategory(t.id)
    if (bookmarks.filters.category_id === t.id) selectAll()
    else bookmarks.load()
  } else {
    await meta.removeTag(t.id)
    if (bookmarks.filters.tag_id === t.id) selectAll()
    else bookmarks.load()
  }
  ElMessage.success('已删除')
}
</script>

<template>
  <div class="sidebar-inner">
    <div class="quick-section">
      <div class="nav-item" :class="{ active: isAll }" @click="selectAll">
        <el-icon><Collection /></el-icon><span>全部收藏</span>
      </div>
      <div class="nav-item" :class="{ active: isFav }" @click="selectFavorites">
        <el-icon><Star /></el-icon><span>星标</span>
      </div>
      <div class="nav-item" :class="{ active: isUncat }" @click="selectUncategorized">
        <el-icon><FolderOpened /></el-icon><span>未分类</span>
      </div>
    </div>

    <div class="section-title" @click="catOpen = !catOpen">
      <span class="section-label">
        <el-icon class="arrow" :class="{ open: catOpen }"><ArrowRight /></el-icon>
        分类
      </span>
      <el-icon class="add-btn" @click.stop="addCategory"><Plus /></el-icon>
    </div>
    <div v-show="catOpen">
      <div
        v-for="node in flatCategories"
        :key="node.cat.id"
        class="nav-item"
        :class="{ active: bookmarks.filters.category_id === node.cat.id }"
        :style="{ paddingLeft: 12 + node.depth * 14 + 'px' }"
        @click="selectCategory(node.cat.id)"
        @contextmenu.prevent="openCategoryMenu($event, node.cat)"
      >
        <span class="item-text">🗂 {{ node.cat.name }}</span>
        <span class="count">{{ node.cat.count }}</span>
      </div>
    </div>

    <div class="section-title" @click="tagOpen = !tagOpen">
      <span class="section-label">
        <el-icon class="arrow" :class="{ open: tagOpen }"><ArrowRight /></el-icon>
        标签
      </span>
      <el-icon class="add-btn" @click.stop="addTag"><Plus /></el-icon>
    </div>
    <div v-show="tagOpen">
      <div
        v-for="tag in meta.tags"
        :key="tag.id"
        class="nav-item tag-item"
        :class="{ active: bookmarks.filters.tag_id === tag.id }"
        @click="selectTag(tag.id)"
        @contextmenu.prevent="openTagMenu($event, tag.id, tag.name)"
      >
        <span class="tag-name"># {{ tag.name }}</span>
        <span class="count">{{ tag.count }}</span>
      </div>
    </div>
  </div>

  <teleport to="body">
    <div v-if="menu.visible" class="ctx-mask" @click="closeMenu" @contextmenu.prevent="closeMenu"></div>
    <div v-if="menu.visible" class="ctx-menu" :style="{ left: menu.x + 'px', top: menu.y + 'px' }">
      <div class="ctx-item" @click="renameFromMenu">重命名</div>
      <div class="ctx-item danger" @click="removeFromMenu">删除</div>
    </div>
  </teleport>
</template>

<style scoped>
.sidebar-inner {
  padding: 14px 12px;
}
.quick-section {
  margin-bottom: 8px;
}
.nav-item {
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  color: #5f564b;
  font-size: 14px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.nav-item .el-icon {
  font-size: 15px;
  color: #b8a895;
}
.nav-item:hover {
  background: #f4ece3;
}
.nav-item.active {
  background: #f7e8db;
  color: #b06749;
  font-weight: 600;
}
.nav-item.active .el-icon {
  color: #c97b5d;
}
.item-text,
.tag-name {
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  flex: 1;
}
.count {
  color: #b8a895;
  font-size: 12px;
  flex-shrink: 0;
}
.section-title {
  margin: 16px 8px 6px;
  font-size: 12px;
  color: #a89888;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}
.section-label {
  display: flex;
  align-items: center;
  gap: 4px;
}
.arrow {
  font-size: 12px;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.arrow.open {
  transform: rotate(90deg);
}
.add-btn {
  cursor: pointer;
  color: #b8a895;
  font-size: 13px;
}
.add-btn:hover {
  color: #c97b5d;
}
.tag-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ctx-mask {
  position: fixed;
  inset: 0;
  z-index: 3000;
}
.ctx-menu {
  position: fixed;
  z-index: 3001;
  min-width: 120px;
  background: #fffdfa;
  border: 1px solid #ece2d6;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(140, 100, 70, 0.14);
  padding: 6px;
}
.ctx-item {
  padding: 8px 12px;
  border-radius: 7px;
  cursor: pointer;
  font-size: 13px;
  color: #5f564b;
}
.ctx-item:hover {
  background: #f4ece3;
}
.ctx-item.danger {
  color: #d9765b;
}
.ctx-item.danger:hover {
  background: #fbeae4;
}
</style>
