<script setup lang="ts">
import { onMounted } from 'vue'
import { useMetaStore } from './stores/meta'
import Sidebar from './components/Sidebar.vue'
import TopBar from './components/TopBar.vue'

const meta = useMetaStore()

onMounted(() => {
  meta.loadAll()
})
</script>

<template>
  <div class="layout">
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
