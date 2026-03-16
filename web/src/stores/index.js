/**
 * 歌单状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api'

export const usePlaylistStore = defineStore('playlist', () => {
  // 歌单列表
  const playlists = ref([])
  const currentPlaylist = ref(null)
  const isLoading = ref(false)

  /**
   * 获取歌单列表
   */
  async function fetchPlaylists(platform = null) {
    isLoading.value = true
    try {
      playlists.value = await api.getPlaylists(platform)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取歌单详情
   */
  async function fetchPlaylist(platform, playlistId) {
    isLoading.value = true
    try {
      currentPlaylist.value = await api.getPlaylist(platform, playlistId)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建歌单
   */
  async function createPlaylist(platform, name, description = '') {
    return await api.createPlaylist(platform, name, description)
  }

  return {
    playlists,
    currentPlaylist,
    isLoading,
    fetchPlaylists,
    fetchPlaylist,
    createPlaylist
  }
})

/**
 * 本地音乐库状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api'

export const useLibraryStore = defineStore('library', () => {
  // 本地歌曲列表
  const tracks = ref([])
  const stats = ref(null)
  const isLoading = ref(false)
  const isScanning = ref(false)

  /**
   * 扫描本地音乐库
   */
  async function scanLibrary(paths) {
    isScanning.value = true
    try {
      return await api.scanLibrary(paths)
    } finally {
      isScanning.value = false
    }
  }

  /**
   * 获取本地歌曲列表
   */
  async function fetchTracks(limit = 100, offset = 0) {
    isLoading.value = true
    try {
      tracks.value = await api.getLibraryTracks(limit, offset)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 搜索本地歌曲
   */
  async function searchTracks(query, limit = 50) {
    isLoading.value = true
    try {
      return await api.searchLibrary(query, limit)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取统计信息
   */
  async function fetchStats() {
    stats.value = await api.getLibraryStats()
  }

  /**
   * 上传歌曲到平台
   */
  async function uploadTrack(trackId, platform) {
    return await api.uploadToPlatform(trackId, platform)
  }

  return {
    tracks,
    stats,
    isLoading,
    isScanning,
    scanLibrary,
    fetchTracks,
    searchTracks,
    fetchStats,
    uploadTrack
  }
})

/**
 * 同步状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api'

export const useSyncStore = defineStore('sync', () => {
  // 同步任务
  const tasks = ref([])
  const currentTask = ref(null)
  const stats = ref(null)
  const isLoading = ref(false)

  /**
   * 创建同步任务
   */
  async function createTask(sourcePlatform, sourcePlaylistId, targetPlatform, targetPlaylistName = null) {
    return await api.createSyncTask(
      sourcePlatform,
      sourcePlaylistId,
      targetPlatform,
      targetPlaylistName
    )
  }

  /**
   * 获取任务状态
   */
  async function fetchTask(taskId) {
    return await api.getSyncTask(taskId)
  }

  /**
   * 执行同步任务
   */
  async function executeTask(taskId) {
    isLoading.value = true
    try {
      return await api.executeSyncTask(taskId)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取同步统计
   */
  async function fetchStats() {
    stats.value = await api.getSyncStats()
  }

  return {
    tasks,
    currentTask,
    stats,
    isLoading,
    createTask,
    fetchTask,
    executeTask,
    fetchStats
  }
})
