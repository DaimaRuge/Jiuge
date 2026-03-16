/**
 * 播放器状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api'
import { createWebSocket } from '@/api'

export const usePlayerStore = defineStore('player', () => {
  // ==================== 状态 ====================

  // 播放状态
  const isPlaying = ref(false)
  const isLoading = ref(false)
  const currentTrack = ref(null)
  const currentIndex = ref(-1)
  const progress = ref(0) // 当前播放进度（秒）
  const duration = ref(0) // 总时长（秒）
  const volume = ref(80) // 音量 (0-100)

  // 播放队列
  const playlist = ref([])
  const queue = ref([])

  // WebSocket 连接
  const ws = ref(null)
  const isConnected = ref(false)

  // ==================== 计算属性 ====================

  // 格式化进度
  const formattedProgress = computed(() => formatTime(progress.value))

  // 格式化时长
  const formattedDuration = computed(() => formatTime(duration.value))

  // 播放进度百分比
  const progressPercent = computed(() => {
    if (duration.value === 0) return 0
    return (progress.value / duration.value) * 100
  })

  // ==================== 方法 ====================

  /**
   * 格式化时间
   */
  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  /**
   * 初始化 WebSocket 连接
   */
  function initWebSocket() {
    if (ws.value) return

    ws.value = createWebSocket()

    ws.value.onopen = () => {
      isConnected.value = true
      console.log('WebSocket 已连接')
    }

    ws.value.onclose = () => {
      isConnected.value = false
      console.log('WebSocket 已断开')
      // 尝试重连
      setTimeout(initWebSocket, 5000)
    }

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }

    ws.value.onerror = (error) => {
      console.error('WebSocket 错误:', error)
    }
  }

  /**
   * 处理 WebSocket 消息
   */
  function handleWebSocketMessage(data) {
    switch (data.command) {
      case 'status_update':
        updateStatus(data.data)
        break
      case 'pong':
        // 心跳响应
        break
    }
  }

  /**
   * 更新播放状态
   */
  function updateStatus(status) {
    isPlaying.value = status.is_playing || false
    currentTrack.value = status.current_track || null
    currentIndex.value = status.current_index ?? -1
    progress.value = status.progress || 0
    duration.value = status.duration || 0
    playlist.value = status.playlist || []
    volume.value = status.volume ?? 80
  }

  /**
   * 搜索歌曲
   */
  async function search(query, platforms = null) {
    isLoading.value = true
    try {
      const result = await api.searchTracks(query, platforms)
      return result
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 播放歌曲
   */
  async function play(trackId = null, index = null) {
    isLoading.value = true
    try {
      await api.playTrack(trackId, index)
      isPlaying.value = true
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 暂停播放
   */
  async function pause() {
    await api.pausePlayback()
    isPlaying.value = false
  }

  /**
   * 继续播放
   */
  async function resume() {
    await api.resumePlayback()
    isPlaying.value = true
  }

  /**
   * 切换播放/暂停
   */
  async function togglePlay() {
    if (isPlaying.value) {
      await pause()
    } else {
      await resume()
    }
  }

  /**
   * 下一首
   */
  async function next() {
    isLoading.value = true
    try {
      await api.nextTrack()
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 上一首
   */
  async function previous() {
    isLoading.value = true
    try {
      await api.previousTrack()
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 设置进度
   */
  function setProgress(value) {
    progress.value = value
  }

  /**
   * 设置音量
   */
  function setVolume(value) {
    volume.value = value
    // TODO: 同步到后端
  }

  /**
   * 收藏当前歌曲
   */
  async function favorite() {
    if (!currentTrack.value) return
    await api.favoriteCurrentTrack()
  }

  /**
   * 获取初始状态
   */
  async function fetchStatus() {
    try {
      const status = await api.getStatus()
      updateStatus(status)
    } catch (error) {
      console.error('获取状态失败:', error)
    }
  }

  return {
    // 状态
    isPlaying,
    isLoading,
    currentTrack,
    currentIndex,
    progress,
    duration,
    volume,
    playlist,
    queue,
    isConnected,

    // 计算属性
    formattedProgress,
    formattedDuration,
    progressPercent,

    // 方法
    initWebSocket,
    search,
    play,
    pause,
    resume,
    togglePlay,
    next,
    previous,
    setProgress,
    setVolume,
    favorite,
    fetchStatus
  }
})
