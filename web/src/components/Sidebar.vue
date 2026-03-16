<template>
  <!-- 侧边栏导航 -->
  <aside class="w-64 bg-dark-200 flex flex-col border-r border-gray-800">
    <!-- Logo -->
    <div class="h-16 flex items-center px-6 border-b border-gray-800">
      <router-link to="/" class="flex items-center gap-3">
        <div class="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
          <span class="text-white font-bold text-lg">J</span>
        </div>
        <span class="text-xl font-semibold text-white">Jiuge</span>
      </router-link>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 py-4 overflow-y-auto">
      <!-- 主菜单 -->
      <div class="px-3 mb-6">
        <h3 class="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          发现
        </h3>
        <ul class="space-y-1">
          <li v-for="item in mainMenu" :key="item.path">
            <router-link
              :to="item.path"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
              :class="{ 'bg-white/10 text-white': isActive(item.path) }"
            >
              <span class="text-lg">{{ item.icon }}</span>
              <span>{{ item.title }}</span>
            </router-link>
          </li>
        </ul>
      </div>

      <!-- 音乐库 -->
      <div class="px-3 mb-6">
        <h3 class="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          音乐库
        </h3>
        <ul class="space-y-1">
          <li v-for="item in libraryMenu" :key="item.path">
            <router-link
              :to="item.path"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
              :class="{ 'bg-white/10 text-white': isActive(item.path) }"
            >
              <span class="text-lg">{{ item.icon }}</span>
              <span>{{ item.title }}</span>
            </router-link>
          </li>
        </ul>
      </div>

      <!-- 平台歌单 -->
      <div class="px-3">
        <h3 class="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          平台
        </h3>
        <ul class="space-y-1">
          <li v-for="platform in platforms" :key="platform.id">
            <button
              class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
              @click="selectPlatform(platform)"
            >
              <span class="text-lg">{{ platform.icon }}</span>
              <span>{{ platform.name }}</span>
              <span v-if="platform.connected" class="ml-auto w-2 h-2 bg-green-500 rounded-full"></span>
            </button>
          </li>
        </ul>
      </div>
    </nav>

    <!-- 底部设置 -->
    <div class="p-3 border-t border-gray-800">
      <router-link
        to="/settings"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
      >
        <span class="text-lg">⚙️</span>
        <span>设置</span>
      </router-link>
    </div>
  </aside>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

// 主菜单
const mainMenu = [
  { path: '/', title: '首页', icon: '🏠' },
  { path: '/search', title: '搜索', icon: '🔍' },
  { path: '/recommend', title: '推荐', icon: '✨' }
]

// 音乐库菜单
const libraryMenu = [
  { path: '/playlists', title: '歌单', icon: '📋' },
  { path: '/library', title: '本地音乐', icon: '📁' },
  { path: '/sync', title: '同步', icon: '🔄' }
]

// 平台列表
const platforms = [
  { id: 'netease', name: '网易云音乐', icon: '🎵', connected: true },
  { id: 'spotify', name: 'Spotify', icon: '🎧', connected: false },
  { id: 'apple', name: 'Apple Music', icon: '🍎', connected: false },
  { id: 'qqmusic', name: 'QQ音乐', icon: '🔊', connected: false }
]

// 判断当前路由
const isActive = (path) => {
  return route.path === path
}

// 选择平台
const selectPlatform = (platform) => {
  console.log('选择平台:', platform.name)
  // TODO: 实现平台选择逻辑
}
</script>
