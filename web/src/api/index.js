/**
 * API 客户端
 * 封装与后端 API 的通信
 */
import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加认证 token
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// ==================== 播放控制 API ====================

/**
 * 获取播放状态
 */
export const getStatus = () => api.get('/status')

/**
 * 搜索歌曲
 */
export const searchTracks = (query, platforms = null, limit = 20) =>
  api.post('/search', { query, platforms, limit })

/**
 * 播放歌曲
 */
export const playTrack = (trackId = null, index = null) =>
  api.post('/play', { track_id: trackId, index })

/**
 * 暂停播放
 */
export const pausePlayback = () => api.post('/pause')

/**
 * 继续播放
 */
export const resumePlayback = () => api.post('/resume')

/**
 * 下一首
 */
export const nextTrack = () => api.post('/next')

/**
 * 上一首
 */
export const previousTrack = () => api.post('/previous')

/**
 * 停止播放
 */
export const stopPlayback = () => api.post('/stop')

/**
 * 收藏当前歌曲
 */
export const favoriteCurrentTrack = () => api.post('/favorite')

// ==================== 歌单 API ====================

/**
 * 获取歌单列表
 */
export const getPlaylists = (platform = null) =>
  api.get('/playlists', { params: { platform } })

/**
 * 获取歌单详情
 */
export const getPlaylist = (platform, playlistId) =>
  api.get(`/playlists/${platform}/${playlistId}`)

/**
 * 创建歌单
 */
export const createPlaylist = (platform, name, description = '') =>
  api.post('/playlists', null, { params: { platform, name, description } })

// ==================== 同步 API ====================

/**
 * 创建同步任务
 */
export const createSyncTask = (sourcePlatform, sourcePlaylistId, targetPlatform, targetPlaylistName = null) =>
  api.post('/sync', {
    source_platform: sourcePlatform,
    source_playlist_id: sourcePlaylistId,
    target_platform: targetPlatform,
    target_playlist_name: targetPlaylistName
  })

/**
 * 获取同步任务状态
 */
export const getSyncTask = (taskId) =>
  api.get(`/sync/${taskId}`)

/**
 * 执行同步任务
 */
export const executeSyncTask = (taskId) =>
  api.post(`/sync/${taskId}/execute`)

/**
 * 获取同步统计
 */
export const getSyncStats = () => api.get('/sync/stats')

// ==================== 本地音乐库 API ====================

/**
 * 扫描本地音乐库
 */
export const scanLibrary = (paths) =>
  api.post('/library/scan', { paths })

/**
 * 获取本地歌曲列表
 */
export const getLibraryTracks = (limit = 100, offset = 0) =>
  api.get('/library/tracks', { params: { limit, offset } })

/**
 * 搜索本地歌曲
 */
export const searchLibrary = (query, limit = 50) =>
  api.get('/library/search', { params: { query, limit } })

/**
 * 获取本地音乐库统计
 */
export const getLibraryStats = () => api.get('/library/stats')

/**
 * 上传歌曲到平台
 */
export const uploadToPlatform = (trackId, platform) =>
  api.post('/library/upload', null, { params: { track_id: trackId, platform } })

// ==================== 推荐 API ====================

/**
 * 获取推荐歌曲
 */
export const getRecommendations = (limit = 20, strategy = 'hybrid', context = null) =>
  api.post('/recommend', { limit, strategy, context })

/**
 * 获取相似歌曲
 */
export const getSimilarTracks = (trackId, limit = 10) =>
  api.get(`/recommend/similar/${trackId}`, { params: { limit } })

// ==================== WebSocket 连接 ====================

/**
 * 创建 WebSocket 连接
 */
export const createWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws`
  return new WebSocket(wsUrl)
}

export default api
