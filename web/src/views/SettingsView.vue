<template>
  <!-- 设置视图 -->
  <div class="animate-fade-in max-w-3xl">
    <h1 class="text-2xl font-bold text-white mb-6">设置</h1>

    <!-- 平台配置 -->
    <section class="mb-8">
      <h2 class="text-lg font-semibold text-white mb-4">平台配置</h2>
      <div class="space-y-4">
        <div
          v-for="platform in platforms"
          :key="platform.id"
          class="card flex items-center justify-between"
        >
          <div class="flex items-center gap-4">
            <span class="text-2xl">{{ platform.icon }}</span>
            <div>
              <h3 class="text-white font-medium">{{ platform.name }}</h3>
              <p class="text-sm text-gray-400">{{ platform.description }}</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span
              class="text-sm"
              :class="platform.connected ? 'text-green-500' : 'text-gray-500'"
            >
              {{ platform.connected ? '已连接' : '未连接' }}
            </span>
            <button
              class="btn btn-sm"
              :class="platform.connected ? 'btn-secondary' : 'btn-primary'"
              @click="configurePlatform(platform)"
            >
              {{ platform.connected ? '配置' : '连接' }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 播放器设置 -->
    <section class="mb-8">
      <h2 class="text-lg font-semibold text-white mb-4">播放器设置</h2>
      <div class="space-y-4">
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-white font-medium">默认音量</h3>
              <p class="text-sm text-gray-400">启动时的默认音量</p>
            </div>
            <div class="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="100"
                v-model="settings.defaultVolume"
                class="w-24"
              />
              <span class="text-white w-10 text-right">{{ settings.defaultVolume }}%</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-white font-medium">自动播放</h3>
              <p class="text-sm text-gray-400">启动时自动继续上次播放</p>
            </div>
            <button
              class="w-12 h-6 rounded-full transition-colors"
              :class="settings.autoPlay ? 'bg-primary-500' : 'bg-dark-200'"
              @click="settings.autoPlay = !settings.autoPlay"
            >
              <div
                class="w-5 h-5 bg-white rounded-full transition-transform"
                :class="settings.autoPlay ? 'translate-x-6' : 'translate-x-1'"
              ></div>
            </button>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-white font-medium">歌词显示</h3>
              <p class="text-sm text-gray-400">播放时显示歌词</p>
            </div>
            <button
              class="w-12 h-6 rounded-full transition-colors"
              :class="settings.showLyrics ? 'bg-primary-500' : 'bg-dark-200'"
              @click="settings.showLyrics = !settings.showLyrics"
            >
              <div
                class="w-5 h-5 bg-white rounded-full transition-transform"
                :class="settings.showLyrics ? 'translate-x-6' : 'translate-x-1'"
              ></div>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 推荐设置 -->
    <section class="mb-8">
      <h2 class="text-lg font-semibold text-white mb-4">推荐设置</h2>
      <div class="card">
        <h3 class="text-white font-medium mb-4">推荐权重</h3>
        <div class="space-y-4">
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-400">协同过滤</span>
              <span class="text-white">{{ settings.weights.collaborative }}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              v-model="settings.weights.collaborative"
              class="w-full"
            />
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-400">基于内容</span>
              <span class="text-white">{{ settings.weights.content }}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              v-model="settings.weights.content"
              class="w-full"
            />
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-400">流行度</span>
              <span class="text-white">{{ settings.weights.popularity }}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              v-model="settings.weights.popularity"
              class="w-full"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- 缓存和数据 -->
    <section class="mb-8">
      <h2 class="text-lg font-semibold text-white mb-4">缓存和数据</h2>
      <div class="space-y-4">
        <div class="card flex items-center justify-between">
          <div>
            <h3 class="text-white font-medium">清除缓存</h3>
            <p class="text-sm text-gray-400">清除本地缓存数据</p>
          </div>
          <button class="btn btn-secondary" @click="clearCache">
            清除
          </button>
        </div>

        <div class="card flex items-center justify-between">
          <div>
            <h3 class="text-white font-medium">导出数据</h3>
            <p class="text-sm text-gray-400">导出歌单和播放历史</p>
          </div>
          <button class="btn btn-secondary" @click="exportData">
            导出
          </button>
        </div>

        <div class="card flex items-center justify-between">
          <div>
            <h3 class="text-white font-medium">重置设置</h3>
            <p class="text-sm text-gray-400">恢复默认设置</p>
          </div>
          <button class="btn btn-secondary text-red-400" @click="resetSettings">
            重置
          </button>
        </div>
      </div>
    </section>

    <!-- 关于 -->
    <section>
      <h2 class="text-lg font-semibold text-white mb-4">关于</h2>
      <div class="card">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-12 h-12 bg-primary-500 rounded-xl flex items-center justify-center">
            <span class="text-white font-bold text-xl">J</span>
          </div>
          <div>
            <h3 class="text-white font-medium">Jiuge 音乐智能体</h3>
            <p class="text-sm text-gray-400">版本 2.0.0-beta</p>
          </div>
        </div>
        <p class="text-gray-400 text-sm">
          Jiuge 是一个智能音乐助手，支持多平台音乐控制、歌单同步和智能推荐。
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const platforms = ref([
  { id: 'netease', name: '网易云音乐', icon: '🎵', description: '连接网易云音乐账号', connected: true },
  { id: 'spotify', name: 'Spotify', icon: '🎧', description: '连接 Spotify 账号', connected: false },
  { id: 'apple', name: 'Apple Music', icon: '🍎', description: '连接 Apple Music 账号', connected: false },
  { id: 'qqmusic', name: 'QQ音乐', icon: '🔊', description: '连接 QQ音乐账号', connected: false }
])

const settings = ref({
  defaultVolume: 80,
  autoPlay: true,
  showLyrics: true,
  weights: {
    collaborative: 40,
    content: 30,
    popularity: 20
  }
})

const configurePlatform = (platform) => {
  console.log('配置平台:', platform.name)
}

const clearCache = () => {
  if (confirm('确定要清除缓存吗？')) {
    console.log('清除缓存')
  }
}

const exportData = () => {
  console.log('导出数据')
}

const resetSettings = () => {
  if (confirm('确定要重置所有设置吗？')) {
    settings.value = {
      defaultVolume: 80,
      autoPlay: true,
      showLyrics: true,
      weights: { collaborative: 40, content: 30, popularity: 20 }
    }
  }
}
</script>
