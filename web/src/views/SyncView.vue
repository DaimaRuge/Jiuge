<template>
  <!-- 歌单同步视图 -->
  <div class="animate-fade-in">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white">歌单同步</h1>
        <p class="text-gray-400">跨平台同步你的歌单</p>
      </div>
      <button class="btn btn-primary" @click="showCreateModal = true">
        ➕ 新建同步任务
      </button>
    </div>

    <!-- 同步统计 -->
    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="card text-center">
        <p class="text-2xl font-bold text-primary-500">{{ stats.completedTasks }}</p>
        <p class="text-gray-400 text-sm">已完成</p>
      </div>
      <div class="card text-center">
        <p class="text-2xl font-bold text-yellow-500">{{ stats.pendingTasks }}</p>
        <p class="text-gray-400 text-sm">进行中</p>
      </div>
      <div class="card text-center">
        <p class="text-2xl font-bold text-green-500">{{ stats.totalMappings }}</p>
        <p class="text-gray-400 text-sm">歌曲映射</p>
      </div>
    </div>

    <!-- 同步任务列表 -->
    <h2 class="text-lg font-semibold text-white mb-4">同步任务</h2>
    <div class="space-y-4">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="card"
      >
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-2">
              <span class="text-lg">{{ getPlatformIcon(task.sourcePlatform) }}</span>
              <span class="text-gray-400">→</span>
              <span class="text-lg">{{ getPlatformIcon(task.targetPlatform) }}</span>
            </div>
            <h3 class="text-white font-medium">{{ task.name }}</h3>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="px-2 py-1 rounded text-xs"
              :class="getStatusClass(task.status)"
            >
              {{ getStatusText(task.status) }}
            </span>
            <button
              v-if="task.status === 'pending'"
              class="btn btn-primary btn-sm"
              @click="executeTask(task)"
            >
              执行
            </button>
            <button
              v-if="task.status === 'completed'"
              class="btn btn-secondary btn-sm"
              @click="executeTask(task)"
            >
              重新同步
            </button>
          </div>
        </div>

        <!-- 进度条 -->
        <div v-if="task.status === 'syncing'" class="mb-3">
          <div class="flex justify-between text-sm text-gray-400 mb-1">
            <span>同步中...</span>
            <span>{{ task.syncedTracks }} / {{ task.totalTracks }}</span>
          </div>
          <div class="h-2 bg-dark-200 rounded-full overflow-hidden">
            <div
              class="h-full bg-primary-500 transition-all"
              :style="{ width: `${(task.syncedTracks / task.totalTracks) * 100}%` }"
            ></div>
          </div>
        </div>

        <!-- 同步结果 -->
        <div v-else class="flex gap-4 text-sm text-gray-400">
          <span>✅ 成功: {{ task.syncedTracks }}</span>
          <span v-if="task.failedTracks > 0" class="text-red-400">
            ❌ 失败: {{ task.failedTracks }}
          </span>
        </div>

        <p class="text-xs text-gray-500 mt-2">
          {{ task.updatedAt }}
        </p>
      </div>
    </div>

    <!-- 新建同步任务弹窗 -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showCreateModal = false"
    >
      <div class="bg-dark-100 rounded-xl p-6 w-full max-w-lg">
        <h3 class="text-xl font-bold text-white mb-4">新建同步任务</h3>

        <div class="space-y-4">
          <!-- 源平台 -->
          <div>
            <label class="block text-sm text-gray-400 mb-1">源平台</label>
            <select v-model="newTask.sourcePlatform" class="input">
              <option v-for="p in platforms" :key="p.id" :value="p.id">
                {{ p.name }}
              </option>
            </select>
          </div>

          <!-- 源歌单 -->
          <div>
            <label class="block text-sm text-gray-400 mb-1">源歌单</label>
            <select v-model="newTask.sourcePlaylistId" class="input">
              <option value="">选择歌单</option>
              <option v-for="pl in sourcePlaylists" :key="pl.id" :value="pl.id">
                {{ pl.name }} ({{ pl.track_count }}首)
              </option>
            </select>
          </div>

          <!-- 目标平台 -->
          <div>
            <label class="block text-sm text-gray-400 mb-1">目标平台</label>
            <select v-model="newTask.targetPlatform" class="input">
              <option v-for="p in targetPlatforms" :key="p.id" :value="p.id">
                {{ p.name }}
              </option>
            </select>
          </div>

          <!-- 目标歌单名称 -->
          <div>
            <label class="block text-sm text-gray-400 mb-1">目标歌单名称（可选）</label>
            <input
              type="text"
              v-model="newTask.targetPlaylistName"
              placeholder="留空则使用源歌单名称"
              class="input"
            />
          </div>
        </div>

        <div class="flex justify-end gap-3 mt-6">
          <button class="btn btn-secondary" @click="showCreateModal = false">
            取消
          </button>
          <button class="btn btn-primary" @click="createTask">
            创建任务
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const showCreateModal = ref(false)

const stats = ref({
  completedTasks: 5,
  pendingTasks: 1,
  totalMappings: 156
})

const tasks = ref([
  {
    id: 1,
    name: '我喜欢的音乐',
    sourcePlatform: 'netease',
    targetPlatform: 'spotify',
    status: 'completed',
    totalTracks: 128,
    syncedTracks: 125,
    failedTracks: 3,
    updatedAt: '2024-01-15 14:30'
  },
  {
    id: 2,
    name: '华语金曲',
    sourcePlatform: 'netease',
    targetPlatform: 'apple',
    status: 'syncing',
    totalTracks: 50,
    syncedTracks: 30,
    failedTracks: 0,
    updatedAt: '正在同步...'
  }
])

const platforms = [
  { id: 'netease', name: '网易云音乐' },
  { id: 'spotify', name: 'Spotify' },
  { id: 'apple', name: 'Apple Music' }
]

const newTask = ref({
  sourcePlatform: 'netease',
  sourcePlaylistId: '',
  targetPlatform: 'spotify',
  targetPlaylistName: ''
})

const sourcePlaylists = ref([
  { id: 1, name: '我喜欢的音乐', track_count: 128 },
  { id: 2, name: '华语金曲', track_count: 50 }
])

const targetPlatforms = computed(() => {
  return platforms.filter(p => p.id !== newTask.value.sourcePlatform)
})

const getPlatformIcon = (platform) => {
  const icons = { netease: '🎵', spotify: '🎧', apple: '🍎' }
  return icons[platform] || '🎵'
}

const getStatusClass = (status) => {
  return {
    pending: 'bg-yellow-500/20 text-yellow-500',
    syncing: 'bg-blue-500/20 text-blue-500',
    completed: 'bg-green-500/20 text-green-500',
    failed: 'bg-red-500/20 text-red-500'
  }[status]
}

const getStatusText = (status) => {
  return {
    pending: '待执行',
    syncing: '同步中',
    completed: '已完成',
    failed: '失败'
  }[status]
}

const executeTask = (task) => {
  console.log('执行任务:', task.id)
}

const createTask = () => {
  console.log('创建任务:', newTask.value)
  showCreateModal.value = false
}
</script>
