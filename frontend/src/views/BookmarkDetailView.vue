<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Delete, Edit, Link, Refresh, Star, StarFilled } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { bookmarksApi } from '../api'
import type { Bookmark } from '../types'
import { formatDate, getHost } from '../utils'
import { useBookmarksStore } from '../stores/bookmarks'
import EditBookmarkDialog from '../components/EditBookmarkDialog.vue'

const route = useRoute()
const router = useRouter()
const store = useBookmarksStore()

const bookmark = ref<Bookmark | null>(null)
const loading = ref(true)
const showEdit = ref(false)
const refetching = ref(false)

const md = new MarkdownIt({ html: false, linkify: true })
const rendered = computed(() => (bookmark.value ? md.render(bookmark.value.content_markdown || '') : ''))

async function load() {
  loading.value = true
  try {
    bookmark.value = await bookmarksApi.get(Number(route.params.id))
  } finally {
    loading.value = false
  }
}
onMounted(load)

function goBack() {
  router.push('/')
}
function openUrl() {
  if (bookmark.value) window.open(bookmark.value.url, '_blank', 'noopener')
}
function onSaved(updated: Bookmark) {
  bookmark.value = updated
}
async function toggleFavorite() {
  if (!bookmark.value) return
  bookmark.value = await bookmarksApi.update(bookmark.value.id, { is_favorite: !bookmark.value.is_favorite })
  ElMessage.success('已更新')
}
async function refetch() {
  if (!bookmark.value) return
  refetching.value = true
  try {
    bookmark.value = await bookmarksApi.refetch(bookmark.value.id)
    ElMessage.success('已重新抓取')
  } catch {
    // 错误已在拦截器提示
  } finally {
    refetching.value = false
  }
}
async function remove() {
  if (!bookmark.value) return
  try {
    await ElMessageBox.confirm('确定删除该收藏？', '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await store.remove(bookmark.value.id)
  ElMessage.success('已删除')
  router.push('/')
}
</script>

<template>
  <div v-loading="loading" class="detail-view">
    <template v-if="bookmark">
      <div class="detail-header">
        <el-button text :icon="ArrowLeft" @click="goBack">返回</el-button>
        <div class="header-actions">
          <el-icon class="fav-btn" :class="{ active: bookmark.is_favorite }" @click="toggleFavorite">
            <StarFilled v-if="bookmark.is_favorite" />
            <Star v-else />
          </el-icon>
          <el-button text :icon="Link" @click="openUrl">原文</el-button>
          <el-button text :icon="Refresh" :loading="refetching" @click="refetch">重新抓取</el-button>
          <el-button text :icon="Edit" @click="showEdit = true">编辑</el-button>
          <el-button text type="danger" :icon="Delete" @click="remove">删除</el-button>
        </div>
      </div>

      <div class="article">
        <h1 class="article-title">{{ bookmark.title }}</h1>
        <div class="article-meta">
          <a class="article-host" :href="bookmark.url" target="_blank" rel="noopener">🔗 {{ getHost(bookmark.url) }}</a>
          <span class="dot">·</span>
          <span class="date">{{ formatDate(bookmark.created_at) }}</span>
          <el-tag v-if="bookmark.category" size="small" type="info" effect="plain">
            {{ bookmark.category.name }}
          </el-tag>
          <el-tag v-for="tag in bookmark.tags" :key="tag.id" size="small" effect="plain"># {{ tag.name }}</el-tag>
        </div>
        <div v-if="bookmark.description" class="article-desc">{{ bookmark.description }}</div>
        <el-divider />
        <div class="markdown-body article-content" v-html="rendered" />
      </div>

      <EditBookmarkDialog v-model="showEdit" :bookmark="bookmark" @saved="onSaved" />
    </template>
  </div>
</template>

<style scoped>
.detail-view {
  padding: 24px 28px;
  max-width: 860px;
  margin: 0 auto;
}
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.fav-btn {
  cursor: pointer;
  font-size: 20px;
  color: #d5c8ba;
  margin-right: 6px;
  transition: color 0.2s;
}
.fav-btn.active {
  color: #e0a458;
}
.article {
  background: #fffdfa;
  border: 1px solid #ece2d6;
  border-radius: 14px;
  padding: 36px 44px;
  box-shadow: 0 6px 24px rgba(140, 100, 70, 0.07);
}
.article-title {
  font-size: 26px;
  font-weight: 700;
  color: #362f28;
  line-height: 1.4;
  margin-bottom: 14px;
}
.article-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.article-host {
  font-size: 13px;
  color: #c97b5d;
  text-decoration: none;
}
.article-host:hover {
  text-decoration: underline;
}
.dot {
  color: #d5c8ba;
}
.date {
  font-size: 13px;
  color: #a89888;
}
.article-desc {
  font-size: 14px;
  color: #8c7c6c;
  background: #f6efe7;
  border-radius: 8px;
  padding: 12px 14px;
}
.article-content {
  min-height: 120px;
}
</style>
