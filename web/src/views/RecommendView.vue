<template>
  <!-- 推荐视图 -->
  <div class="animate-fade-in">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-white">为你推荐</h1>
      <p class="text-gray-400">基于你的听歌习惯推荐</p>
    </div>

    <!-- 推荐策略选择 -->
    <div class="flex gap-2 mb-6">
      <button
        v-for="strategy in strategies"
        :key="strategy.id"
        class="px-4 py-2 rounded-full transition-colors"
        :class="selectedStrategy === strategy.id
          ? 'bg-primary-500 text-white'
          : 'bg-dark-100 text-gray-400 hover:text-white'"
        @click="changeStrategy(strategy.id)"
      >
        {{ strategy.icon }} {{ strategy.name }}
      </button>
    </div>

    <!-- 推荐歌曲列表 -->
    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="animate-spin text-4xl">⏳</div>
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="(rec, index) in recommendations"
        :key="rec.track.id"
        class="track-item group"
        @click="playTrack(rec.track, index)"
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
            v-if="rec.track.cover_url"
            :src="rec.track.cover_url"
            :alt="rec.track.title"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center">🎵</div>
        </div>

        <!-- 歌曲信息 -->
        <div class="flex-1 min-w-0">
          <h4 class="text-white font-medium truncate">{{ rec.track.title }}</h4>
          <p class="text-sm text-gray-400 truncate">
            {{ rec.track.artists?.join(', ') }} - {{ rec.track.album }}
          </p>
        </div>

        <!-- 推荐分数 -->
        <div class="flex items-center gap-2">
          <div class="w-20 h-1 bg-dark-200 rounded-full overflow-hidden">
            <div
              class="h-full bg-primary-500"
              :style="{ width: `${rec.score * 100}%` }"
            ></div>
          </div>
          <span class="text-sm text-gray-400 w-12">{{ Math.round(rec.score * 100) }}%</span>
        </div>

        <!-- 推荐理由 -->
        <div class="hidden md:block max-w-xs">
          <p class="text-sm text-gray-500 truncate">
            {{ rec.reasons?.join(' · ') }}
          </p>
        </div>

        <!-- 操作按钮 -->
        <div class="track-actions flex gap-2">
          <button class="btn btn-ghost p-1" @click.stop="notInterested(rec)">
            <span>👎</span>
          </button>
          <button class="btn btn-ghost p-1" @click.stop="addToFavorites(rec)">
            <span>❤️</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 加载更多 -->
    <div class="text-center mt-6">
      <button class="btn btn-secondary" @click="loadMore">
        加载更多
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usePlayerStore } from '@/stores/player'
import * as api from '@/api'

const player = usePlayerStore()

const isLoading = ref(false)
const selectedStrategy = ref('hybrid')
const recommendations = ref([])

const strategies = [
  { id: 'hybrid', name: '混合推荐', icon: '✨' },
  { id: 'collaborative', name: '相似用户', icon: '👥' },
  { id: 'content', name: '相似歌曲', icon: '🎵' }
]

const changeStrategy = (strategy) => {
  selectedStrategy.value = strategy
  fetchRecommendations()
}

const fetchRecommendations = async () => {
  isLoading.value = true
  try {
    const result = await api.getRecommendations(20, selectedStrategy.value)
    recommendations.value = result || []
  } catch (error) {
    console.error('获取推荐失败:', error)
    // 使用模拟数据
    recommendations.value = [
      {
        track: { id: 1, title: '起风了', artists: ['买辣椒也用券'], album: '起风了', cover_url: '' },
        score: 0.95,
        reasons: ['你喜欢买辣椒也用券', '近期常听']
      },
      {
        track: { id: 2, title: '晴天', artists: ['周杰伦'], album: '叶惠美', cover_url: '' },
        score: 0.89,
        reasons: ['你喜欢周杰伦', '相似用户喜欢']
      },
      {
        track: { id: 3, title: '夜曲', artists: ['周杰伦'], album: '十一月的萧邦', cover_url: '' },
        score: 0.85,
        reasons: ['你喜欢周杰伦']
      }
    ]
  } finally {
    isLoading.value = false
  }
}

const playTrack = (track, index) => {
  player.play(track.id)
}

const notInterested = (rec) => {
  console.log('不感兴趣:', rec.track.title)
}

const addToFavorites = (rec) => {
  console.log('收藏:', rec.track.title)
}

const loadMore = () => {
  console.log('加载更多')
}

onMounted(() => {
  fetchRecommendations()
})
</script>
