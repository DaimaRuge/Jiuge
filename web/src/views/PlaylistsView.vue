<template>
  <!-- 歌单管理视图 -->
  <div class="animate-fade-in">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-white">我的歌单</h1>
      <button class="btn btn-primary" @click="showCreateModal = true">
        ➕ 新建歌单
      </button>
    </div>

    <!-- 平台筛选 -->
    <div class="flex gap-2 mb-6">
      <button
        v-for="platform in platforms"
        :key="platform.id"
        class="px-4 py-2 rounded-full transition-colors"
        :class="selectedPlatform === platform.id
          ? 'bg-primary-500 text-white'
          : 'bg-dark-100 text-gray-400 hover:text-white'"
        @click="selectedPlatform = platform.id"
      >
        {{ platform.icon }} {{ platform.name }}
      </button>
    </div>

    <!-- 歌单列表 -->
    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="animate-spin text-4xl">⏳</div>
    </div>

    <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <div
        v-for="playlist in filteredPlaylists"
        :key="playlist.id"
        class="playlist-card p-4 cursor-pointer"
        @click="openPlaylist(playlist)"
      >
        <div class="aspect-square rounded-lg bg-dark-200 mb-3 overflow-hidden relative">
          <img
            v-if="playlist.cover_url"
            :src="playlist.cover_url"
            :alt="playlist.name"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-3xl">
            📋
          </div>
          <div class="playlist-overlay">
            <button
              class="w-12 h-12 bg-primary-500 rounded-full flex items-center justify-center"
              @click.stop="playPlaylist(playlist)"
            >
              <span class="text-white text-xl">▶️</span>
            </button>
          </div>
        </div>
        <h4 class="text-white font-medium truncate">{{ playlist.name }}</h4>
        <p class="text-sm text-gray-400">
          {{ playlist.track_count }} 首歌曲
        </p>
      </div>
    </div>

    <!-- 新建歌单弹窗 -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showCreateModal = false"
    >
      <div class="bg-dark-100 rounded-xl p-6 w-full max-w-md">
        <h3 class="text-xl font-bold text-white mb-4">新建歌单</h3>

        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-1">平台</label>
            <select v-model="newPlaylist.platform" class="input">
              <option v-for="p in platforms" :key="p.id" :value="p.id">
                {{ p.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">歌单名称</label>
            <input
              type="text"
              v-model="newPlaylist.name"
              placeholder="输入歌单名称"
              class="input"
            />
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">描述（可选）</label>
            <textarea
              v-model="newPlaylist.description"
              placeholder="输入歌单描述"
              class="input resize-none"
              rows="3"
            ></textarea>
          </div>
        </div>

        <div class="flex justify-end gap-3 mt-6">
          <button class="btn btn-secondary" @click="showCreateModal = false">
            取消
          </button>
          <button class="btn btn-primary" @click="createPlaylist">
            创建
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlaylistStore } from '@/stores'

const router = useRouter()
const playlistStore = usePlaylistStore()

const isLoading = ref(false)
const showCreateModal = ref(false)
const selectedPlatform = ref('all')
const playlists = ref([])

const platforms = [
  { id: 'all', name: '全部', icon: '📋' },
  { id: 'netease', name: '网易云', icon: '🎵' },
  { id: 'spotify', name: 'Spotify', icon: '🎧' },
  { id: 'apple', name: 'Apple', icon: '🍎' }
]

const newPlaylist = ref({
  platform: 'netease',
  name: '',
  description: ''
})

const filteredPlaylists = computed(() => {
  if (selectedPlatform.value === 'all') {
    return playlists.value
  }
  return playlists.value.filter(p => p.platform === selectedPlatform.value)
})

const openPlaylist = (playlist) => {
  router.push(`/playlists/${playlist.platform}/${playlist.id}`)
}

const playPlaylist = (playlist) => {
  console.log('播放歌单:', playlist.name)
}

const createPlaylist = async () => {
  if (!newPlaylist.value.name) return

  await playlistStore.createPlaylist(
    newPlaylist.value.platform,
    newPlaylist.value.name,
    newPlaylist.value.description
  )

  showCreateModal.value = false
  newPlaylist.value = { platform: 'netease', name: '', description: '' }
  fetchPlaylists()
}

const fetchPlaylists = async () => {
  isLoading.value = true
  try {
    await playlistStore.fetchPlaylists()
    playlists.value = playlistStore.playlists
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  // 模拟数据
  playlists.value = [
    { id: 1, name: '我喜欢的音乐', platform: 'netease', track_count: 128, cover_url: '' },
    { id: 2, name: '每日推荐', platform: 'netease', track_count: 30, cover_url: '' },
    { id: 3, name: '华语金曲', platform: 'netease', track_count: 50, cover_url: '' },
    { id: 4, name: '欧美流行', platform: 'spotify', track_count: 40, cover_url: '' },
    { id: 5, name: '轻音乐', platform: 'netease', track_count: 25, cover_url: '' }
  ]
})
</script>
