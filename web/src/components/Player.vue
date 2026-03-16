<template>
  <!-- 底部播放器 -->
  <footer class="h-24 bg-dark-200 border-t border-gray-800 flex items-center px-6">
    <!-- 当前歌曲信息 -->
    <div class="flex items-center gap-4 w-72">
      <!-- 封面 -->
      <div class="w-14 h-14 bg-dark-300 rounded-lg overflow-hidden flex-shrink-0">
        <img
          v-if="player.currentTrack?.cover_url"
          :src="player.currentTrack.cover_url"
          :alt="player.currentTrack.title"
          class="w-full h-full object-cover"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-2xl">
          🎵
        </div>
      </div>

      <!-- 歌曲信息 -->
      <div class="flex-1 min-w-0">
        <h4 class="text-white font-medium truncate">
          {{ player.currentTrack?.title || '未播放' }}
        </h4>
        <p class="text-gray-400 text-sm truncate">
          {{ artistNames }}
        </p>
      </div>

      <!-- 收藏按钮 -->
      <button
        class="btn btn-ghost p-2"
        :class="{ 'text-red-500': isFavorited }"
        @click="toggleFavorite"
      >
        <span class="text-xl">{{ isFavorited ? '❤️' : '🤍' }}</span>
      </button>
    </div>

    <!-- 播放控制 -->
    <div class="flex-1 flex flex-col items-center justify-center gap-2">
      <!-- 控制按钮 -->
      <div class="flex items-center gap-4">
        <!-- 随机播放 -->
        <button
          class="btn btn-ghost p-2"
          :class="{ 'text-primary-500': isShuffled }"
          @click="isShuffled = !isShuffled"
        >
          <span class="text-lg">🔀</span>
        </button>

        <!-- 上一首 -->
        <button class="btn btn-ghost p-2" @click="player.previous()">
          <span class="text-xl">⏮️</span>
        </button>

        <!-- 播放/暂停 -->
        <button
          class="w-12 h-12 bg-white rounded-full flex items-center justify-center hover:scale-105 transition-transform"
          @click="player.togglePlay()"
          :disabled="player.isLoading"
        >
          <span v-if="player.isLoading" class="text-dark-300 text-xl animate-spin">⏳</span>
          <span v-else class="text-dark-300 text-xl">
            {{ player.isPlaying ? '⏸️' : '▶️' }}
          </span>
        </button>

        <!-- 下一首 -->
        <button class="btn btn-ghost p-2" @click="player.next()">
          <span class="text-xl">⏭️</span>
        </button>

        <!-- 循环播放 -->
        <button
          class="btn btn-ghost p-2"
          :class="{ 'text-primary-500': repeatMode !== 'none' }"
          @click="toggleRepeat"
        >
          <span class="text-lg">{{ repeatMode === 'one' ? '🔂' : '🔁' }}</span>
        </button>
      </div>

      <!-- 进度条 -->
      <div class="w-full max-w-xl flex items-center gap-3">
        <span class="text-xs text-gray-400 w-10 text-right">
          {{ player.formattedProgress }}
        </span>
        <div
          class="flex-1 h-1 bg-gray-700 rounded-full cursor-pointer group"
          @click="seekTo"
          ref="progressBar"
        >
          <div
            class="h-full bg-primary-500 rounded-full relative"
            :style="{ width: `${player.progressPercent}%` }"
          >
            <div class="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </div>
        </div>
        <span class="text-xs text-gray-400 w-10">
          {{ player.formattedDuration }}
        </span>
      </div>
    </div>

    <!-- 音量和其他控制 -->
    <div class="flex items-center gap-4 w-72 justify-end">
      <!-- 播放队列 -->
      <button class="btn btn-ghost p-2" @click="showQueue = !showQueue">
        <span class="text-lg">📝</span>
      </button>

      <!-- 音量控制 -->
      <div class="flex items-center gap-2">
        <button class="btn btn-ghost p-2" @click="toggleMute">
          <span class="text-lg">{{ volumeIcon }}</span>
        </button>
        <input
          type="range"
          min="0"
          max="100"
          :value="player.volume"
          @input="player.setVolume($event.target.value)"
          class="w-20 h-1 bg-gray-700 rounded-full appearance-none cursor-pointer"
        />
      </div>
    </div>
  </footer>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usePlayerStore } from '@/stores/player'

const player = usePlayerStore()

// 状态
const isFavorited = ref(false)
const isShuffled = ref(false)
const repeatMode = ref('none') // none, all, one
const showQueue = ref(false)
const isMuted = ref(false)
const progressBar = ref(null)

// 计算属性
const artistNames = computed(() => {
  if (!player.currentTrack?.artists) return ''
  return player.currentTrack.artists.join(', ')
})

const volumeIcon = computed(() => {
  if (isMuted.value || player.volume === 0) return '🔇'
  if (player.volume < 50) return '🔉'
  return '🔊'
})

// 方法
const toggleFavorite = async () => {
  await player.favorite()
  isFavorited.value = !isFavorited.value
}

const toggleRepeat = () => {
  const modes = ['none', 'all', 'one']
  const currentIndex = modes.indexOf(repeatMode.value)
  repeatMode.value = modes[(currentIndex + 1) % modes.length]
}

const toggleMute = () => {
  isMuted.value = !isMuted.value
}

const seekTo = (event) => {
  if (!progressBar.value) return
  const rect = progressBar.value.getBoundingClientRect()
  const percent = (event.clientX - rect.left) / rect.width
  const newProgress = percent * player.duration
  player.setProgress(newProgress)
}
</script>

<style scoped>
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  cursor: pointer;
}

input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}
</style>
