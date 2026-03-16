"""
音乐平台适配器基类
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from dataclasses import dataclass, field


@dataclass
class Track:
    """歌曲信息"""
    id: str
    platform: str
    platform_id: str
    title: str
    artists: List[str] = field(default_factory=list)
    album: str = ""
    duration: int = 0
    cover_url: str = ""
    audio_url: Optional[str] = None
    isrc: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "platform": self.platform,
            "platform_id": self.platform_id,
            "title": self.title,
            "artists": self.artists,
            "album": self.album,
            "duration": self.duration,
            "cover_url": self.cover_url,
            "audio_url": self.audio_url,
            "isrc": self.isrc
        }


@dataclass
class Playlist:
    """歌单信息"""
    id: str
    name: str
    platform: str
    description: str = ""
    track_count: int = 0
    cover_url: str = ""
    tracks: List[Track] = field(default_factory=list)


class MusicPlatformAdapter(ABC):
    """音乐平台适配器基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """平台名称"""
        pass
    
    @property
    @abstractmethod
    def is_authenticated(self) -> bool:
        """是否已认证"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """进行认证"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        limit: int = 10,
        search_type: str = "track"
    ) -> List[Track]:
        """
        搜索
        
        Args:
            query: 搜索关键词
            limit: 返回数量
            search_type: 搜索类型 (track/album/artist/playlist)
        """
        pass
    
    @abstractmethod
    async def get_track_url(self, track_id: str) -> Optional[str]:
        """获取歌曲播放地址"""
        pass
    
    @abstractmethod
    async def get_track_info(self, track_id: str) -> Optional[Track]:
        """获取歌曲详情"""
        pass
    
    @abstractmethod
    async def get_playlists(self) -> List[Playlist]:
        """获取用户歌单列表"""
        pass
    
    @abstractmethod
    async def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """获取歌单详情"""
        pass
    
    @abstractmethod
    async def create_playlist(
        self, 
        name: str, 
        description: str = ""
    ) -> Optional[Playlist]:
        """创建歌单"""
        pass
    
    @abstractmethod
    async def add_to_playlist(
        self, 
        playlist_id: str, 
        track_ids: List[str]
    ) -> bool:
        """添加歌曲到歌单"""
        pass
    
    @abstractmethod
    async def favorite(self, track_id: str) -> bool:
        """收藏歌曲"""
        pass
    
    @abstractmethod
    async def unfavorite(self, track_id: str) -> bool:
        """取消收藏"""
        pass
    
    @abstractmethod
    async def get_favorites(self, limit: int = 50) -> List[Track]:
        """获取收藏列表"""
        pass
    
    @abstractmethod
    async def get_recommendations(self, limit: int = 10) -> List[Track]:
        """获取推荐"""
        pass
