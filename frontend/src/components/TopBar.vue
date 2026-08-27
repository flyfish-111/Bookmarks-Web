<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, Plus, Search } from '@element-plus/icons-vue'
import { useBookmarksStore } from '../stores/bookmarks'
import { useAuthStore } from '../stores/auth'
import AddBookmarkDialog from './AddBookmarkDialog.vue'
import ExportDialog from './ExportDialog.vue'
import ImportDialog from './ImportDialog.vue'

const store = useBookmarksStore()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const showAdd = ref(false)
const addUrl = ref('')
const searchInput = ref(store.filters.q ?? '')
const showBookmarklet = ref(false)
const showExport = ref(false)
const showImport = ref(false)

const bookmarkletCode = computed(() => {
  const origin = window.location.origin
  return `javascript:(function(){var a=document.createElement('a');a.href='${origin}/?url='+encodeURIComponent(location.href);a.target='_blank';a.rel='noopener';document.body.appendChild(a);a.click();document.body.removeChild(a);})()`
})

let timer: ReturnType<typeof setTimeout> | undefined
watch(searchInput, (val) => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    store.setFilter({ q: val || undefined })
  }, 400)
})

watch(
  () => route.query.url,
  (u) => {
    if (typeof u === 'string' && u.trim()) {
      addUrl.value = u.trim()
      showAdd.value = true
    }
  },
  { immediate: true },
)

function logout() {
  auth.logout()
  store.reset()
  router.push('/login')
}

function onUserCommand(cmd: string | number | object) {
  if (cmd === 'logout') logout()
}

function onMoreCommand(cmd: string | number | object) {
  if (cmd === 'export') showExport.value = true
  else if (cmd === 'import') showImport.value = true
  else if (cmd === 'bookmarklet') showBookmarklet.value = true
}
</script>

<template>
  <header class="topbar">
    <div class="brand">📌 网址收藏夹</div>
    <el-input
      v-model="searchInput"
      placeholder="搜索标题 / 描述 / 正文…"
      clearable
      :prefix-icon="Search"
      class="search"
    />
    <div class="spacer" />
    <el-dropdown trigger="click" @command="onUserCommand">
      <span class="user">
        {{ auth.user?.username || '用户' }}
        <el-icon><ArrowDown /></el-icon>
      </span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="logout">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
    <el-dropdown trigger="click" @command="onMoreCommand">
      <span class="user">
        更多
        <el-icon><ArrowDown /></el-icon>
      </span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="export">导出收藏</el-dropdown-item>
          <el-dropdown-item command="import">导入收藏</el-dropdown-item>
          <el-dropdown-item divided command="bookmarklet">一键收藏书签工具</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
    <el-button type="primary" :icon="Plus" @click="showAdd = true">添加收藏</el-button>
    <AddBookmarkDialog v-model="showAdd" :initial-url="addUrl" />
    <ExportDialog v-model="showExport" />
    <ImportDialog v-model="showImport" />

    <el-dialog v-model="showBookmarklet" title="一键收藏书签工具" width="520px" append-to-body>
      <p class="bm-tip">把下面的按钮拖到浏览器书签栏，之后在任意网页点它，就能一键收藏当前页。</p>
      <div class="bm-drag">
        <a :href="bookmarkletCode" class="bm-link">📌 收藏到网址收藏夹</a>
      </div>
      <p class="bm-tip">若拖拽无效，复制下面代码，手动新建书签并把地址粘贴进去：</p>
      <el-input type="textarea" :model-value="bookmarkletCode" readonly :rows="2" />
    </el-dialog>
  </header>
</template>

<style scoped>
.topbar {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 24px;
  background: #fffdfa;
  border-bottom: 1px solid #ece2d6;
  flex-shrink: 0;
}
.brand {
  font-size: 17px;
  font-weight: 700;
  color: #403931;
  white-space: nowrap;
}
.search {
  max-width: 420px;
}
.search :deep(.el-input__wrapper) {
  border-radius: 20px;
  background: #f6efe7;
  box-shadow: none;
  padding-left: 14px;
}
.spacer {
  flex: 1;
}
.user {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #403931;
  cursor: pointer;
  white-space: nowrap;
  outline: none;
}
.bm-tip {
  color: #8c7c6c;
  font-size: 13px;
  margin: 0 0 10px;
}
.bm-drag {
  text-align: center;
  margin: 4px 0 16px;
}
.bm-link {
  display: inline-block;
  padding: 10px 20px;
  background: #c97b5d;
  color: #fff;
  border-radius: 10px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  cursor: grab;
}
</style>
