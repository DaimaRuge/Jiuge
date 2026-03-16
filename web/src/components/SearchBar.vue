<template>
  <!-- 搜索栏 -->
  <div class="relative">
    <div class="relative">
      <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
      <input
        type="text"
        v-model="query"
        placeholder="搜索歌曲、歌手、专辑..."
        class="w-full pl-10 pr-4 py-2 bg-dark-300 border border-gray-700 rounded-full text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
        @keyup.enter="search"
        @focus="showSuggestions = true"
        @blur="hideSuggestions"
      />
    </div>

    <!-- 搜索建议/历史 -->
    <div
      v-if="showSuggestions && (recentSearches.length > 0 || query)"
      class="absolute top-full left-0 right-0 mt-2 bg-dark-100 rounded-lg shadow-xl border border-gray-700 overflow-hidden z-50"
    >
      <!-- 搜索历史 -->
      <div v-if="!query && recentSearches.length > 0" class="p-2">
        <h4 class="px-3 py-1 text-xs text-gray-500 font-medium">搜索历史</h4>
        <ul>
          <li
            v-for="item in recentSearches"
            :key="item"
            class="px-3 py-2 text-gray-300 hover:bg-white/5 cursor-pointer rounded-lg"
            @mousedown="selectHistory(item)"
          >
            <span class="mr-2">🕐</span>
            {{ item }}
          </li>
        </ul>
      </div>

      <!-- 平台筛选 -->
      <div v-if="query" class="p-2 border-b border-gray-700">
        <div class="flex gap-2 px-2">
          <button
            v-for="platform in platforms"
            :key="platform.id"
            class="px-3 py-1 text-sm rounded-full transition-colors"
            :class="selectedPlatforms.includes(platform.id)
              ? 'bg-primary-500 text-white'
              : 'bg-dark-200 text-gray-400 hover:text-white'"
            @mousedown="togglePlatform(platform.id)"
          >
            {{ platform.name }}
          </button>
        </div>
      </div>

      <!-- 快速搜索 -->
      <div v-if="query" class="p-2">
        <button
          class="w-full px-3 py-2 text-left text-gray-300 hover:bg-white/5 rounded-lg flex items-center gap-2"
          @mousedown="search"
        >
          <span>🔍</span>
          <span>搜索 "{{ query }}"</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'

const router = useRouter()
const player = usePlayerStore()

const query = ref('')
const showSuggestions = ref(false)
const recentSearches = ref(['周杰伦', '起风了', '告白气球'])
const selectedPlatforms = ref(['netease', 'spotify'])

const platforms = [
  { id: 'netease', name: '网易' },
  { id: 'spotify', name: 'Spotify' },
  { id: 'apple', name: 'Apple' },
  { id: 'qqmusic', name: 'QQ' }
]

const search = () => {
  if (!query.value.trim()) return

  // 添加到搜索历史
  if (!recentSearches.value.includes(query.value)) {
    recentSearches.value.unshift(query.value)
    if (recentSearches.value.length > 10) {
      recentSearches.value.pop()
    }
  }

  // 跳转到搜索页
  router.push({
    path: '/search',
    query: { q: query.value, platforms: selectedPlatforms.value.join(',') }
  })

  showSuggestions.value = false
}

const selectHistory = (item) => {
  query.value = item
  search()
}

const togglePlatform = (platformId) => {
  const index = selectedPlatforms.value.indexOf(platformId)
  if (index > -1) {
    selectedPlatforms.value.splice(index, 1)
  } else {
    selectedPlatforms.value.push(platformId)
  }
}

const hideSuggestions = () => {
  // 延迟隐藏，以便点击建议项
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}
</script>
