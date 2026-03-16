<template>
  <!-- 首页视图 -->
  <div class="animate-fade-in">
    <!-- 欢迎区域 -->
    <section class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">欢迎回来</h1>
      <p class="text-gray-400">今天想听点什么？</p>
    </section>

    <!-- 快捷操作 -->
    <section class="mb-8">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <button
          v-for="action in quickActions"
          :key="action.title"
          class="p-4 bg-gradient-to-br rounded-xl text-left hover:scale-[1.02] transition-transform"
          :class="action.gradient"
          @click="action.action"
        >
          <span class="text-2xl mb-2 block">{{ action.icon }}</span>
          <h3 class="text-white font-medium">{{ action.title }}</h3>
          <p class="text-sm text-white/70">{{ action.description }}</p>
        </button>
      </div>
    </section>

    <!-- 最近播放 -->
    <section class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold text-white">最近播放</h2>
        <router-link to="/playlists" class="text-primary-500 text-sm hover:underline">
          查看全部
        </router-link>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <div
          v-for="track in recentTracks"
          :key="track.id"
          class="playlist-card p-4 cursor-pointer"
          @click="playTrack(track)"
        >
          <div class="aspect-square rounded-lg bg-dark-200 mb-3 overflow-hidden">
            <img
              v-if="track.cover_url"
              :src="track.cover_url"
              :alt="track.title"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-3xl">
              🎵
            </div>
          </div>
          <h4 class="text-white font-medium truncate">{{ track.title }}</h4>
          <p class="text-sm text-gray-400 truncate">{{ track.artists?.join(', ') }}</p>
        </div>
      </div>
    </section>

    <!-- 推荐歌单 -->
    <section class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold text-white">为你推荐</h2>
        <router-link to="/recommend" class="text-primary-500 text-sm hover:underline">
          更多推荐
        </router-link>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <div
          v-for="playlist in recommendedPlaylists"
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
              <button class="w-12 h-12 bg-primary-500 rounded-full flex items-center justify-center">
                <span class="text-white text-xl">▶️</span>
              </button>
            </div>
          </div>
          <h4 class="text-white font-medium truncate">{{ playlist.name }}</h4>
          <p class="text-sm text-gray-400">{{ playlist.track_count }} 首歌曲</p>
        </div>
      </div>
    </section>

    <!-- 统计信息 -->
    <section>
      <h2 class="text-xl font-semibold text-white mb-4">你的音乐库</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="card text-center">
          <p class="text-3xl font-bold text-primary-500">{{ stats.totalTracks }}</p>
          <p class="text-gray-400 text-sm">首歌曲</p>
        </div>
        <div class="card text-center">
          <p class="text-3xl font-bold text-primary-500">{{ stats.totalArtists }}</p>
          <p class="text-gray-400 text-sm">位歌手</p>
        </div>
        <div class="card text-center">
          <p class="text-3xl font-bold text-primary-500">{{ stats.totalAlbums }}</p>
          <p class="text-gray-400 text-sm">张专辑</p>
        </div>
        <div class="card text-center">
          <p class="text-3xl font-bold text-primary-500">{{ stats.totalHours }}</p>
          <p class="text-gray-400 text-sm">小时</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'

const router = useRouter()
const player = usePlayerStore()

// 快捷操作
const quickActions = [
  {
    title: '搜索音乐',
    description: '发现新歌曲',
    icon: '🔍',
    gradient: 'from-blue-500 to-blue-600',
    action: () => router.push('/search')
  },
  {
    title: '每日推荐',
    description: '个性化推荐',
    icon: '✨',
    gradient: 'from-purple-500 to-purple-600',
    action: () => router.push('/recommend')
  },
  {
    title: '本地音乐',
    description: '扫描本地文件',
    icon: '📁',
    gradient: 'from-green-500 to-green-600',
    action: () => router.push('/library')
  },
  {
    title: '歌单同步',
    description: '跨平台同步',
    icon: '🔄',
    gradient: 'from-orange-500 to-orange-600',
    action: () => router.push('/sync')
  }
]

// 最近播放
const recentTracks = ref([
  { id: 1, title: '起风了', artists: ['买辣椒也用券'], cover_url: '' },
  { id: 2, title: '告白气球', artists: ['周杰伦'], cover_url: '' },
  { id: 3, title: '晴天', artists: ['周杰伦'], cover_url: '' },
  { id: 4, title: '稻香', artists: ['周杰伦'], cover_url: '' },
  { id: 5, title: '夜曲', artists: ['周杰伦'], cover_url: '' }
])

// 推荐歌单
const recommendedPlaylists = ref([
  { id: 1, name: '每日推荐', track_count: 30, cover_url: '' },
  { id: 2, name: '华语金曲', track_count: 50, cover_url: '' },
  { id: 3, name: '轻音乐', track_count: 25, cover_url: '' },
  { id: 4, name: '欧美流行', track_count: 40, cover_url: '' },
  { id: 5, name: '怀旧经典', track_count: 35, cover_url: '' }
])

// 统计信息
const stats = ref({
  totalTracks: 1280,
  totalArtists: 156,
  totalAlbums: 89,
  totalHours: 72
})

// 播放歌曲
const playTrack = async (track) => {
  await player.play(track.id)
}

// 打开歌单
const openPlaylist = (playlist) => {
  router.push(`/playlists/netease/${playlist.id}`)
}

onMounted(() => {
  player.fetchStatus()
})
</script>
