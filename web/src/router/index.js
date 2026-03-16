/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('@/views/SearchView.vue'),
    meta: { title: '搜索' }
  },
  {
    path: '/playlists',
    name: 'Playlists',
    component: () => import('@/views/PlaylistsView.vue'),
    meta: { title: '歌单' }
  },
  {
    path: '/playlists/:platform/:id',
    name: 'PlaylistDetail',
    component: () => import('@/views/PlaylistDetailView.vue'),
    meta: { title: '歌单详情' }
  },
  {
    path: '/library',
    name: 'Library',
    component: () => import('@/views/LibraryView.vue'),
    meta: { title: '本地音乐库' }
  },
  {
    path: '/sync',
    name: 'Sync',
    component: () => import('@/views/SyncView.vue'),
    meta: { title: '歌单同步' }
  },
  {
    path: '/recommend',
    name: 'Recommend',
    component: () => import('@/views/RecommendView.vue'),
    meta: { title: '推荐' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { title: '设置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 更新页面标题
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'Jiuge'} - Jiuge 音乐智能体`
  next()
})

export default router
