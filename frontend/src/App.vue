<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useMetaStore } from './stores/meta'
import Sidebar from './components/Sidebar.vue'
import TopBar from './components/TopBar.vue'

const route = useRoute()
const auth = useAuthStore()
const meta = useMetaStore()

const isAuthPage = computed(() => route.path === '/login')

onMounted(() => {
  if (auth.token) auth.fetchMe()
})

// 登录成功后（user 从无到有）加载分类/标签，未登录不请求
watch(
  () => auth.user,
  (u) => {
    if (u) meta.loadAll()
  },
)
</script>

<template>
  <router-view v-if="isAuthPage" />
  <div v-else class="layout">
    <aside class="sidebar">
      <Sidebar />
    </aside>
    <div class="main-col">
      <TopBar />
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
}
.sidebar {
  width: 232px;
  flex-shrink: 0;
  background: #fffdfa;
  border-right: 1px solid #ece2d6;
  overflow-y: auto;
}
.main-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.content {
  flex: 1;
  overflow-y: auto;
  background: #f7f2ec;
}
</style>
