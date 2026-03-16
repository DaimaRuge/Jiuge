<template>
  <!-- 用户菜单 -->
  <div class="relative">
    <button
      class="flex items-center gap-2 btn btn-ghost"
      @click="showMenu = !showMenu"
    >
      <div class="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
        <span class="text-white text-sm font-medium">J</span>
      </div>
      <span class="text-sm text-gray-300">用户</span>
    </button>

    <!-- 下拉菜单 -->
    <transition name="fade">
      <div
        v-if="showMenu"
        class="absolute right-0 top-full mt-2 w-48 bg-dark-100 rounded-lg shadow-xl border border-gray-700 overflow-hidden z-50"
      >
        <div class="p-3 border-b border-gray-700">
          <p class="text-white font-medium">Jiuge 用户</p>
          <p class="text-sm text-gray-400">已连接网易云音乐</p>
        </div>
        <ul>
          <li>
            <router-link
              to="/settings"
              class="block px-4 py-2 text-gray-300 hover:bg-white/5"
              @click="showMenu = false"
            >
              ⚙️ 设置
            </router-link>
          </li>
          <li>
            <a
              href="#"
              class="block px-4 py-2 text-gray-300 hover:bg-white/5"
              @click.prevent="showAbout"
            >
              ℹ️ 关于
            </a>
          </li>
        </ul>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const showMenu = ref(false)

const showAbout = () => {
  alert('Jiuge 音乐智能体 v2.0.0-beta\n\n一个智能的音乐助手，支持多平台控制和推荐。')
  showMenu.value = false
}
</script>
