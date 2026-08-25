<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, Star, StarFilled } from '@element-plus/icons-vue'
import type { Bookmark } from '../types'
import { getHost } from '../utils'
import { useBookmarksStore } from '../stores/bookmarks'
import EditBookmarkDialog from './EditBookmarkDialog.vue'

const props = defineProps<{ bookmark: Bookmark }>()
const router = useRouter()
const store = useBookmarksStore()
const showEdit = ref(false)
const faviconFailed = ref(false)

const host = getHost(props.bookmark.url)

function openUrl() {
  window.open(props.bookmark.url, '_blank', 'noopener')
}
function openDetail() {
  router.push(`/bookmarks/${props.bookmark.id}`)
}
async function toggleFavorite() {
  await store.update(props.bookmark.id, { is_favorite: !props.bookmark.is_favorite })
}
async function remove() {
  try {
    await ElMessageBox.confirm('确定删除该收藏？', '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await store.remove(props.bookmark.id)
  ElMessage.success('已删除')
}
</script>

<template>
  <div class="card" @click="openDetail">
    <div class="card-head">
      <div class="favicon-box">
        <img
          v-if="bookmark.favicon_url && !faviconFailed"
          :src="bookmark.favicon_url"
          alt=""
          @error="faviconFailed = true"
        />
        <span v-else class="favicon-letter">{{ host.charAt(0).toUpperCase() }}</span>
      </div>
      <div class="head-text">
        <div class="title">{{ bookmark.title }}</div>
        <div class="host no-drag" @click.stop="openUrl">{{ host }}</div>
      </div>
    </div>

    <div v-if="bookmark.description" class="desc">{{ bookmark.description }}</div>

    <div v-if="bookmark.category || bookmark.tags.length" class="meta">
      <el-tag v-if="bookmark.category" size="small" type="info" effect="plain">
        {{ bookmark.category.name }}
      </el-tag>
      <el-tag v-for="tag in bookmark.tags" :key="tag.id" size="small" effect="plain"># {{ tag.name }}</el-tag>
    </div>

    <div class="actions no-drag">
      <el-icon class="fav-btn" :class="{ active: bookmark.is_favorite }" @click.stop="toggleFavorite">
        <StarFilled v-if="bookmark.is_favorite" />
        <Star v-else />
      </el-icon>
      <span class="spacer" />
      <div class="actions-right">
        <el-button size="small" text :icon="Edit" @click.stop="showEdit = true">编辑</el-button>
        <el-button size="small" text type="danger" :icon="Delete" @click.stop="remove">删除</el-button>
      </div>
    </div>

    <EditBookmarkDialog v-model="showEdit" :bookmark="bookmark" />
  </div>
</template>

<style scoped>
.card {
  background: #fffdfa;
  border: 1px solid #ece2d6;
  border-radius: 14px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(140, 100, 70, 0.12);
}
.card-head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.favicon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #f6efe7;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}
.favicon-box img {
  width: 22px;
  height: 22px;
  border-radius: 4px;
}
.favicon-letter {
  font-size: 17px;
  font-weight: 700;
  color: #c97b5d;
}
.head-text {
  min-width: 0;
  flex: 1;
}
.title {
  font-size: 15px;
  font-weight: 600;
  color: #403931;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}
.host {
  font-size: 12px;
  color: #b8a895;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.host:hover {
  color: #c97b5d;
}
.desc {
  font-size: 13px;
  color: #8c7c6c;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}
.fav-btn {
  cursor: pointer;
  font-size: 18px;
  color: #d5c8ba;
  transition: color 0.2s;
}
.fav-btn.active {
  color: #e0a458;
}
.spacer {
  flex: 1;
}
.actions-right {
  opacity: 0;
  transition: opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.card:hover .actions-right {
  opacity: 1;
}
</style>
