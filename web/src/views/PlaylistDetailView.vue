<template>
  <!-- 歌单详情视图 -->
  <div class="animate-fade-in">
    <!-- 歌单头部 -->
    <div class="flex gap-6 mb-8">
      <!-- 封面 -->
      <div class="w-48 h-48 flex-shrink-0 bg-dark-200 rounded-xl overflow-hidden shadow-xl">
        <img
          v-if="playlist?.cover_url"
          :src="playlist.cover_url"
          :alt="playlist.name"
          class="w-full h-full object-cover"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-5xl">
          📋
        </div>
      </div>

      <!-- 信息 -->
      <div class="flex flex-col justify-end">
        <p class="text-sm text-gray-400 mb-1">歌单</p>
        <h1 class="text-4xl font-bold text-white mb-4">{{ playlist?.name }}</h1>
        <p class="text-gray-400 mb-4">{{ playlist?.description }}</p>
        <div class="flex items-center gap-4 text-sm text-gray-400">
          <span>{{ playlist?.track_count || 0 }} 首歌曲</span>
          <span>·</span>
          <span>{{ getPlatformName(playlist?.platform) }}</span>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="flex gap-4 mb-6">
      <button class="btn btn-primary flex items-center gap-2" @click="playAll">
        <span class="text-xl">▶️</span>
        播放全部
      </button>
      <button class="btn btn-secondary" @click="shufflePlay">
        🔀 随机播放
      </button>
      <button class="btn btn-ghost" @click="syncPlaylist">
        🔄 同步到其他平台
      </button>
    </div>

    <!-- 歌曲列表 -->
    <div class="space-y-2">
      <div
        v-for="(track, index) in playlist?.tracks || []"
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

        <!-- 时长 -->
        <div class="w-16 text-right text-gray-400 text-sm">
          {{ formatDuration(track.duration) }}
        </div>

        <!-- 操作按钮 -->
        <div class="track-actions flex gap-2">
          <button class="btn btn-ghost p-1" @click.stop="removeTrack(track)">
            <span>✕</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { usePlaylistStore } from '@/stores'

const route = useRoute()
const router = useRouter()
const player = usePlayerStore()
const playlistStore = usePlaylistStore()

const playlist = ref(null)

const getPlatformName = (platform) => {
  const names = { netease: '网易云音乐', spotify: 'Spotify', apple: 'Apple Music' }
  return names[platform] || platform
}

const formatDuration = (seconds) => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const playAll = () => {
  player.play(null, 0)
}

const shufflePlay = () => {
  const count = playlist.value?.tracks?.length || 0
  const randomIndex = Math.floor(Math.random() * count)
  player.play(null, randomIndex)
}

const playTrack = (track, index) => {
  player.play(null, index)
}

const removeTrack = (track) => {
  console.log('移除歌曲:', track.title)
}

const syncPlaylist = () => {
  router.push({
    path: '/sync',
    query: {
      platform: playlist.value?.platform,
      playlistId: playlist.value?.id
    }
  })
}

onMounted(async () => {
  const { platform, id } = route.params
  // 模拟数据
  playlist.value = {
    id: id,
    name: '我喜欢的音乐',
    platform: platform,
    description: '我喜欢的歌曲合集',
    track_count: 5,
    cover_url: '',
    tracks: [
      { id: 1, title: '起风了', artists: ['买辣椒也用券'], album: '起风了', duration: 240 },
      { id: 2, title: '告白气球', artists: ['周杰伦'], album: '周杰伦的床边故事', duration: 215 },
      { id: 3, title: '晴天', artists: ['周杰伦'], album: '叶惠美', duration: 269 },
      { id: 4, title: '稻香', artists: ['周杰伦'], album: '魔杰座', duration: 223 },
      { id: 5, title: '夜曲', artists: ['周杰伦'], album: '十一月的萧邦', duration: 246 }
    ]
  }
})
</script>
