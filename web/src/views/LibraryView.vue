<template>
  <!-- 本地音乐库视图 -->
  <div class="animate-fade-in">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white">本地音乐库</h1>
        <p class="text-gray-400">管理本地音乐文件</p>
      </div>
      <button class="btn btn-primary" @click="showScanModal = true">
        📁 扫描目录
      </button>
    </div>

    <!-- 统计信息 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="card">
        <p class="text-2xl font-bold text-primary-500">{{ stats.totalTracks }}</p>
        <p class="text-gray-400 text-sm">首歌曲</p>
      </div>
      <div class="card">
        <p class="text-2xl font-bold text-primary-500">{{ stats.totalArtists }}</p>
        <p class="text-gray-400 text-sm">位歌手</p>
      </div>
      <div class="card">
        <p class="text-2xl font-bold text-primary-500">{{ stats.totalAlbums }}</p>
        <p class="text-gray-400 text-sm">张专辑</p>
      </div>
      <div class="card">
        <p class="text-2xl font-bold text-primary-500">{{ formatSize(stats.totalSize) }}</p>
        <p class="text-gray-400 text-sm">总大小</p>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="flex gap-4 mb-6">
      <div class="flex-1 relative">
        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索本地歌曲..."
          class="input pl-10"
        />
      </div>
      <select v-model="sortBy" class="input w-40">
        <option value="title">按歌名</option>
        <option value="artist">按歌手</option>
        <option value="album">按专辑</option>
        <option value="added">按添加时间</option>
      </select>
    </div>

    <!-- 歌曲列表 -->
    <div class="space-y-2">
      <div
        v-for="track in filteredTracks"
        :key="track.id"
        class="track-item group"
      >
        <!-- 封面 -->
        <div class="w-12 h-12 bg-dark-200 rounded overflow-hidden flex-shrink-0">
          <img
            v-if="track.cover_path"
            :src="track.cover_path"
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

        <!-- 格式 -->
        <div class="px-2 py-1 rounded bg-dark-200 text-xs text-gray-400 uppercase">
          {{ track.file_format }}
        </div>

        <!-- 时长 -->
        <div class="w-16 text-right text-gray-400 text-sm">
          {{ formatDuration(track.duration) }}
        </div>

        <!-- 操作按钮 -->
        <div class="track-actions flex gap-2">
          <button class="btn btn-ghost p-1" @click="playTrack(track)" title="播放">
            <span>▶️</span>
          </button>
          <button class="btn btn-ghost p-1" @click="uploadTrack(track)" title="上传到平台">
            <span>☁️</span>
          </button>
          <button class="btn btn-ghost p-1" @click="showInfo(track)" title="详情">
            <span>ℹ️</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 扫描目录弹窗 -->
    <div
      v-if="showScanModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showScanModal = false"
    >
      <div class="bg-dark-100 rounded-xl p-6 w-full max-w-md">
        <h3 class="text-xl font-bold text-white mb-4">扫描音乐目录</h3>

        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-1">选择目录</label>
            <input
              type="text"
              v-model="scanPath"
              placeholder="输入目录路径"
              class="input"
            />
          </div>
          <p class="text-sm text-gray-500">
            支持的格式: MP3, FLAC, M4A, AAC, OGG, WAV
          </p>
        </div>

        <div class="flex justify-end gap-3 mt-6">
          <button class="btn btn-secondary" @click="showScanModal = false">
            取消
          </button>
          <button class="btn btn-primary" @click="startScan">
            开始扫描
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const showScanModal = ref(false)
const scanPath = ref('')
const searchQuery = ref('')
const sortBy = ref('title')

const stats = ref({
  totalTracks: 256,
  totalArtists: 42,
  totalAlbums: 28,
  totalSize: 2147483648 // 2GB
})

const tracks = ref([
  { id: 1, title: '起风了', artists: ['买辣椒也用券'], album: '起风了', duration: 240, file_format: 'mp3', cover_path: '' },
  { id: 2, title: '告白气球', artists: ['周杰伦'], album: '周杰伦的床边故事', duration: 215, file_format: 'flac', cover_path: '' },
  { id: 3, title: '晴天', artists: ['周杰伦'], album: '叶惠美', duration: 269, file_format: 'mp3', cover_path: '' }
])

const filteredTracks = computed(() => {
  let result = tracks.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(t =>
      t.title.toLowerCase().includes(query) ||
      t.artists?.some(a => a.toLowerCase().includes(query)) ||
      t.album?.toLowerCase().includes(query)
    )
  }
  return result
})

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(1) + ' GB'
}

const formatDuration = (seconds) => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const playTrack = (track) => {
  console.log('播放:', track.title)
}

const uploadTrack = (track) => {
  console.log('上传:', track.title)
}

const showInfo = (track) => {
  console.log('详情:', track)
}

const startScan = () => {
  console.log('扫描目录:', scanPath.value)
  showScanModal.value = false
}
</script>
