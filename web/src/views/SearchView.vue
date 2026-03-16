<template>
  <!-- 搜索视图 -->
  <div class="animate-fade-in">
    <!-- 搜索头部 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-white mb-2">
        搜索 "{{ searchQuery }}"
      </h1>
      <p class="text-gray-400">找到 {{ searchResults.length }} 首歌曲</p>
    </div>

    <!-- 平台筛选 -->
    <div class="flex gap-2 mb-6">
      <button
        v-for="platform in platforms"
        :key="platform.id"
        class="px-4 py-2 rounded-full transition-colors"
        :class="selectedPlatforms.includes(platform.id)
          ? 'bg-primary-500 text-white'
          : 'bg-dark-100 text-gray-400 hover:text-white'"
        @click="togglePlatform(platform.id)"
      >
        {{ platform.icon }} {{ platform.name }}
      </button>
    </div>

    <!-- 搜索结果 -->
    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="animate-spin text-4xl">⏳</div>
    </div>

    <div v-else-if="searchResults.length === 0" class="text-center py-12">
      <p class="text-gray-400 text-lg">没有找到相关歌曲</p>
      <p class="text-gray-500 text-sm mt-2">试试其他关键词？</p>
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="(track, index) in searchResults"
        :key="track.id"
        class="track-item group"
        @click="playTrack(track, index)"
      >
        <!-- 序号 -->
        <div class="w-8 text-center text-gray-500 group-hover:hidden">
          {{ index + 1 }}
        </div>
        <div class="w-8 text-center hidden group-hover:block">
          <span class="text-white">▶️</span>
        </div>

        <!-- 封面 -->
        <div class="w-12 h-12 bg-dark-200 rounded overflow-hidden flex-shrink-0">
          <img
            v-if="track.cover_url"
            :src="track.cover_url"
            :alt="track.title"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center">🎵</div>
        </div>

        <!-- 歌曲信息 -->
        <div class="flex-1 min-w-0">
          <h4 class="text-white font-medium truncate">{{ track.title }}</h4>
          <p class="text-sm text-gray-400 truncate">
            {{ track.artists?.join(', ') }} - {{ track.album }}
          </p>
        </div>

        <!-- 平台标签 -->
        <div class="px-2 py-1 rounded bg-dark-200 text-xs text-gray-400">
          {{ getPlatformName(track.platform) }}
        </div>

        <!-- 时长 -->
        <div class="w-16 text-right text-gray-400 text-sm">
          {{ formatDuration(track.duration) }}
        </div>

        <!-- 操作按钮 -->
        <div class="track-actions flex gap-2">
          <button class="btn btn-ghost p-1" @click.stop="addToQueue(track)">
            <span>➕</span>
          </button>
          <button class="btn btn-ghost p-1" @click.stop="showMore(track)">
            <span>⋯</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePlayerStore } from '@/stores/player'

const route = useRoute()
const player = usePlayerStore()

const isLoading = ref(false)
const searchResults = ref([])
const selectedPlatforms = ref(['netease', 'spotify'])

const platforms = [
  { id: 'netease', name: '网易云', icon: '🎵' },
  { id: 'spotify', name: 'Spotify', icon: '🎧' },
  { id: 'apple', name: 'Apple', icon: '🍎' },
  { id: 'qqmusic', name: 'QQ音乐', icon: '🔊' }
]

const searchQuery = computed(() => route.query.q || '')

const togglePlatform = (platformId) => {
  const index = selectedPlatforms.value.indexOf(platformId)
  if (index > -1) {
    selectedPlatforms.value.splice(index, 1)
  } else {
    selectedPlatforms.value.push(platformId)
  }
  search()
}

const search = async () => {
  if (!searchQuery.value) return

  isLoading.value = true
  try {
    const results = await player.search(
      searchQuery.value,
      selectedPlatforms.value
    )
    searchResults.value = results || []
  } catch (error) {
    console.error('搜索失败:', error)
    searchResults.value = []
  } finally {
    isLoading.value = false
  }
}

const playTrack = async (track, index) => {
  await player.play(track.id)
}

const addToQueue = (track) => {
  console.log('添加到队列:', track.title)
}

const showMore = (track) => {
  console.log('更多选项:', track)
}

const getPlatformName = (platform) => {
  const names = {
    netease: '网易',
    spotify: 'Spotify',
    apple: 'Apple',
    qqmusic: 'QQ音乐'
  }
  return names[platform] || platform
}

const formatDuration = (seconds) => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

watch(searchQuery, () => {
  if (searchQuery.value) {
    search()
  }
})

onMounted(() => {
  if (searchQuery.value) {
    search()
  }
})
</script>
