"""
统一音乐服务
"""

from typing import List, Optional, Dict, Any
import logging

from .adapters.base import MusicPlatformAdapter, Track, Playlist
from .adapters.netease import NeteaseAdapter
from .adapters.spotify import SpotifyAdapter
from .player.local import LocalPlayer
from .memory.store import MusicMemoryStore

logger = logging.getLogger(__name__)


class UnifiedMusicService:
    """统一音乐服务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.adapters: Dict[str, MusicPlatformAdapter] = {}
        self.player = LocalPlayer()
        self.memory = MusicMemoryStore()
        
        self.current_playlist: List[Track] = []
        self.current_index = -1
        
        # 初始化适配器
        self._init_adapters(config)
    
    def _init_adapters(self, config: Dict[str, Any]):
        """初始化平台适配器"""
        # 网易云音乐
        netease_config = config.get("netease", {})
        if netease_config.get("enabled", True):
            try:
                self.adapters["netease"] = NeteaseAdapter(
                    cookie=netease_config.get("cookie")
                )
                logger.info("网易云音乐适配器已初始化")
            except Exception as e:
                logger.warning(f"网易云音乐适配器初始化失败: {e}")
        
        # Spotify
        spotify_config = config.get("spotify", {})
        if spotify_config.get("enabled") and spotify_config.get("client_id"):
            try:
                self.adapters["spotify"] = SpotifyAdapter(
                    client_id=spotify_config["client_id"],
                    client_secret=spotify_config["client_secret"],
                    redirect_uri=spotify_config.get("redirect_uri", "http://localhost:8888/callback")
                )
                logger.info("Spotify 适配器已初始化")
            except Exception as e:
                logger.warning(f"Spotify 适配器初始化失败: {e}")
    
    async def search(
        self, 
        query: str, 
        platforms: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Track]:
        """跨平台搜索"""
        platforms = platforms or list(self.adapters.keys())
        all_tracks = []
        
        for platform in platforms:
            if platform in self.adapters:
                try:
                    adapter = self.adapters[platform]
                    tracks = await adapter.search(query, limit)
                    all_tracks.extend(tracks)
                except Exception as e:
                    logger.error(f"{platform} 搜索失败: {e}")
        
        # 去重（基于歌曲名+歌手）
        seen = set()
        unique_tracks = []
        for track in all_tracks:
            key = (
                track.title.lower().strip(),
                tuple(sorted([a.lower() for a in track.artists]))
            )
            if key not in seen:
                seen.add(key)
                unique_tracks.append(track)
        
        # 保存到播放列表
        self.current_playlist = unique_tracks
        self.current_index = -1
        
        # 保存到记忆
        for track in unique_tracks[:limit]:
            self.memory.save_track(track.to_dict())
        
        return unique_tracks[:limit]
    
    async def play(self, index: int = None) -> Optional[Track]:
        """播放歌曲"""
        if not self.current_playlist:
            return None
        
        if index is not None:
            self.current_index = index
        
        if self.current_index < 0:
            self.current_index = 0
        
        if self.current_index >= len(self.current_playlist):
            self.current_index = len(self.current_playlist) - 1
        
        track = self.current_playlist[self.current_index]
        
        # 获取播放地址
        adapter = self.adapters.get(track.platform)
        if adapter:
            audio_url = await adapter.get_track_url(track.platform_id)
            if audio_url:
                track.audio_url = audio_url
                await self.player.play(audio_url)
                
                # 记录播放
                self.memory.record_play(track.to_dict())
                
                return track
        
        return None
    
    async def pause(self):
        """暂停"""
        await self.player.pause()
    
    async def resume(self):
        """继续"""
        await self.player.resume()
    
    async def next(self) -> Optional[Track]:
        """下一首"""
        if self.current_index < len(self.current_playlist) - 1:
            return await self.play(self.current_index + 1)
        return None
    
    async def previous(self) -> Optional[Track]:
        """上一首"""
        if self.current_index > 0:
            return await self.play(self.current_index - 1)
        return None
    
    async def stop(self):
        """停止"""
        await self.player.stop()
        self.current_index = -1
    
    async def favorite(self) -> bool:
        """收藏当前歌曲"""
        if self.current_index < 0:
            return False
        
        track = self.current_playlist[self.current_index]
        adapter = self.adapters.get(track.platform)
        
        if adapter:
            success = await adapter.favorite(track.platform_id)
            if success:
                self.memory.add_favorite(track.to_dict())
            return success
        
        return False
    
    async def get_recommendations(self, limit: int = 10) -> List[Track]:
        """获取推荐"""
        # 优先使用 Spotify 推荐
        if "spotify" in self.adapters:
            return await self.adapters["spotify"].get_recommendations(limit)
        
        # 其次网易云
        if "netease" in self.adapters:
            return await self.adapters["netease"].get_recommendations(limit)
        
        return []
    
    async def get_status(self) -> Dict[str, Any]:
        """获取播放状态"""
        status = await self.player.get_status()
        
        current_track = None
        if 0 <= self.current_index < len(self.current_playlist):
            track = self.current_playlist[self.current_index]
            current_track = {
                "title": track.title,
                "artists": track.artists,
                "album": track.album,
                "duration": self._format_duration(track.duration),
                "position": status.get("position", "0:00")
            }
        
        return {
            "state": status.get("state", "stopped"),
            "current_track": current_track,
            "playlist_count": len(self.current_playlist),
            "current_index": self.current_index + 1
        }
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
