<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown, Plus, Search } from '@element-plus/icons-vue'
import { useBookmarksStore } from '../stores/bookmarks'
import { useAuthStore } from '../stores/auth'
import AddBookmarkDialog from './AddBookmarkDialog.vue'

const store = useBookmarksStore()
const auth = useAuthStore()
const router = useRouter()
const showAdd = ref(false)
const searchInput = ref(store.filters.q ?? '')

let timer: ReturnType<typeof setTimeout> | undefined
watch(searchInput, (val) => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    store.setFilter({ q: val || undefined })
  }, 400)
})

function logout() {
  auth.logout()
  store.reset()
  router.push('/login')
}

function onCommand(cmd: string | number | object) {
  if (cmd === 'logout') logout()
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
    <el-dropdown trigger="click" @command="onCommand">
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
    <el-button type="primary" :icon="Plus" @click="showAdd = true">添加收藏</el-button>
    <AddBookmarkDialog v-model="showAdd" />
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
</style>
