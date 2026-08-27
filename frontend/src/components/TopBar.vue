<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown, Plus, Search } from '@element-plus/icons-vue'
import { bookmarksApi } from '../api'
import { useBookmarksStore } from '../stores/bookmarks'
import { useAuthStore } from '../stores/auth'
import { useMetaStore } from '../stores/meta'
import AddBookmarkDialog from './AddBookmarkDialog.vue'

const store = useBookmarksStore()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const showAdd = ref(false)
const addUrl = ref('')
const searchInput = ref(store.filters.q ?? '')
const fileInput = ref<HTMLInputElement | null>(null)
const showBookmarklet = ref(false)

const bookmarkletCode = computed(() => {
  const origin = window.location.origin
  return `javascript:(function(){window.open('${origin}/?url='+encodeURIComponent(location.href),'_blank','noopener');})()`
})

let timer: ReturnType<typeof setTimeout> | undefined
watch(searchInput, (val) => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    store.setFilter({ q: val || undefined })
  }, 400)
})

onMounted(() => {
  const u = route.query.url
  if (typeof u === 'string' && u.trim()) {
    addUrl.value = u.trim()
    showAdd.value = true
  }
})

function logout() {
  auth.logout()
  store.reset()
  router.push('/login')
}

function onUserCommand(cmd: string | number | object) {
  if (cmd === 'logout') logout()
}

function onMoreCommand(cmd: string | number | object) {
  if (cmd === 'export-json') doExport('json')
  else if (cmd === 'export-html') doExport('html')
  else if (cmd === 'import') fileInput.value?.click()
  else if (cmd === 'bookmarklet') showBookmarklet.value = true
}

async function doExport(format: 'json' | 'html') {
  try {
    await bookmarksApi.exportFile(format)
  } catch {
    // 错误已由拦截器提示
  }
}

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const loading = ElMessage({ message: '正在导入并抓取网页信息，请稍候…', type: 'info', duration: 0 })
  try {
    const text = await file.text()
    const result = await bookmarksApi.importFile(text)
    loading.close()
    ElMessage.success(`导入完成：新增 ${result.imported} 条，跳过 ${result.skipped} 条（已存在）`)
    await store.load()
    useMetaStore().loadAll()
  } catch {
    loading.close()
    // 错误已由拦截器提示
  } finally {
    input.value = ''
  }
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
          <el-dropdown-item command="export-html">导出收藏（HTML）</el-dropdown-item>
          <el-dropdown-item command="export-json">导出收藏（JSON 备份）</el-dropdown-item>
          <el-dropdown-item command="import">导入收藏</el-dropdown-item>
          <el-dropdown-item divided command="bookmarklet">一键收藏书签工具</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
    <el-button type="primary" :icon="Plus" @click="showAdd = true">添加收藏</el-button>
    <AddBookmarkDialog v-model="showAdd" :initial-url="addUrl" />

    <input ref="fileInput" type="file" accept=".json,.html,.htm,.txt" style="display: none" @change="onFileChange" />

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
