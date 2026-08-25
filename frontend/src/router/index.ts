import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'list', component: () => import('../views/BookmarkListView.vue') },
    { path: '/bookmarks/:id', name: 'detail', component: () => import('../views/BookmarkDetailView.vue') },
  ],
})

export default router
