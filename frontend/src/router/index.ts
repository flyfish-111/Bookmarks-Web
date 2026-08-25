import { createRouter, createWebHistory } from 'vue-router'
import { TOKEN_KEY } from '../api/client'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'list', component: () => import('../views/BookmarkListView.vue') },
    { path: '/bookmarks/:id', name: 'detail', component: () => import('../views/BookmarkDetailView.vue') },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (to.path !== '/login' && !token) {
    return { path: '/login' }
  }
  if (to.path === '/login' && token) {
    return { path: '/' }
  }
})

export default router
