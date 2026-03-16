<template>
  <!-- Jiuge 主应用 -->
  <div class="flex h-full bg-dark-300">
    <!-- 侧边栏 -->
    <Sidebar />

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- 顶部导航 -->
      <header class="h-16 bg-dark-200 border-b border-gray-800 flex items-center px-6">
        <SearchBar class="flex-1 max-w-xl" />
        <div class="flex items-center gap-4 ml-auto">
          <button class="btn btn-ghost" @click="toggleTheme">
            <span class="text-xl">{{ isDark ? '🌙' : '☀️' }}</span>
          </button>
          <UserMenu />
        </div>
      </header>

      <!-- 内容区域 -->
      <div class="flex-1 overflow-y-auto p-6">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>

      <!-- 底部播放器 -->
      <Player />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import Player from '@/components/Player.vue'
import SearchBar from '@/components/SearchBar.vue'
import UserMenu from '@/components/UserMenu.vue'

// 主题切换
const isDark = ref(true)
const toggleTheme = () => {
  isDark.value = !isDark.value
}
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
