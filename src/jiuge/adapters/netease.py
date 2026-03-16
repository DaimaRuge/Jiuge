"""
网易云音乐适配器
基于 NeteaseCloudMusicApi
"""

from typing import List, Optional
import logging

from .base import MusicPlatformAdapter, Track, Playlist

logger = logging.getLogger(__name__)


class NeteaseAdapter(MusicPlatformAdapter):
    """网易云音乐适配器"""
    
    def __init__(self, cookie: str = None):
        self.cookie = cookie
        self._api = None
        self._authenticated = False
    
    @property
    def name(self) -> str:
        return "netease"
    
    @property
    def is_authenticated(self) -> bool:
        return self._authenticated
    
    def _get_api(self):
        """懒加载 API"""
        if self._api is None:
            try:
                from NeteaseCloudMusic import NeteaseCloudMusicApi
                self._api = NeteaseCloudMusicApi()
                if self.cookie:
                    self._api.cookie = self.cookie
            except ImportError:
                logger.error("请安装 NeteaseCloudMusicApi: pip install NeteaseCloudMusicApi")
                raise
        return self._api
    
    async def authenticate(self) -> bool:
        """认证（通过 cookie）"""
        if self.cookie:
            self._authenticated = True
            return True
        return False
    
    async def search(
        self, 
        query: str, 
        limit: int = 10,
        search_type: str = "track"
    ) -> List[Track]:
        """搜索歌曲"""
        api = self._get_api()
        
        type_map = {
            "track": 1,
            "album": 10,
            "artist": 100,
            "playlist": 1000
        }
        
        try:
            result = api.request("search", {
                "keywords": query,
                "limit": limit,
                "type": type_map.get(search_type, 1)
            })
            
            songs = result.get("result", {}).get("songs", [])
            
            return [
                Track(
                    id=f"netease:{s['id']}",
                    platform="netease",
                    platform_id=str(s["id"]),
                    title=s["name"],
                    artists=[a["name"] for a in s.get("artists", [])],
                    album=s.get("album", {}).get("name", ""),
                    duration=s.get("duration", 0) // 1000,
                    cover_url=s.get("album", {}).get("picUrl", "")
                )
                for s in songs
            ]
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    async def get_track_url(self, track_id: str) -> Optional[str]:
        """获取播放地址"""
        api = self._get_api()
        
        try:
            # 去掉平台前缀
            if ":" in track_id:
                track_id = track_id.split(":")[1]
            
            result = api.request("song_url_v1", {
                "id": int(track_id),
                "level": "exhigh"
            })
            
            data = result.get("data", [])
            if data:
                return data[0].get("url")
        except Exception as e:
            logger.error(f"获取播放地址失败: {e}")
        
        return None
    
    async def get_track_info(self, track_id: str) -> Optional[Track]:
        """获取歌曲详情"""
        api = self._get_api()
        
        if ":" in track_id:
            track_id = track_id.split(":")[1]
        
        try:
            result = api.request("song_detail", {"ids": track_id})
            songs = result.get("songs", [])
            
            if songs:
                s = songs[0]
                return Track(
                    id=f"netease:{s['id']}",
                    platform="netease",
                    platform_id=str(s["id"]),
                    title=s["name"],
                    artists=[a["name"] for a in s.get("ar", [])],
                    album=s.get("al", {}).get("name", ""),
                    duration=s.get("dt", 0) // 1000,
                    cover_url=s.get("al", {}).get("picUrl", "")
                )
        except Exception as e:
            logger.error(f"获取歌曲详情失败: {e}")
        
        return None
    
    async def get_playlists(self) -> List[Playlist]:
        """获取用户歌单"""
        # 需要登录态
        return []
    
    async def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """获取歌单详情"""
        api = self._get_api()
        
        try:
            result = api.request("playlist_detail", {"id": playlist_id})
            playlist = result.get("playlist", {})
            
            tracks = [
                Track(
                    id=f"netease:{t['id']}",
                    platform="netease",
                    platform_id=str(t["id"]),
                    title=t["name"],
                    artists=[a["name"] for a in t.get("ar", [])],
                    album=t.get("al", {}).get("name", ""),
                    duration=t.get("dt", 0) // 1000
                )
                for t in playlist.get("tracks", [])
            ]
            
            return Playlist(
                id=f"netease:{playlist_id}",
                name=playlist.get("name", ""),
                platform="netease",
                description=playlist.get("description", ""),
                track_count=playlist.get("trackCount", 0),
                tracks=tracks
            )
        except Exception as e:
            logger.error(f"获取歌单失败: {e}")
        
        return None
    
    async def create_playlist(self, name: str, description: str = "") -> Optional[Playlist]:
        """创建歌单（需要登录）"""
        return None
    
    async def add_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """添加歌曲到歌单"""
        return False
    
    async def favorite(self, track_id: str) -> bool:
        """收藏歌曲"""
        return False
    
    async def unfavorite(self, track_id: str) -> bool:
        """取消收藏"""
        return False
    
    async def get_favorites(self, limit: int = 50) -> List[Track]:
        """获取收藏列表"""
        return []
    
    async def get_recommendations(self, limit: int = 10) -> List[Track]:
        """获取推荐"""
        api = self._get_api()
        
        try:
            result = api.request("recommend_songs", {})
            data = result.get("data", {})
            daily_songs = data.get("dailySongs", [])
            
            return [
                Track(
                    id=f"netease:{s['id']}",
                    platform="netease",
                    platform_id=str(s["id"]),
                    title=s["name"],
                    artists=[a["name"] for a in s.get("ar", [])],
                    album=s.get("al", {}).get("name", ""),
                    duration=s.get("dt", 0) // 1000,
                    cover_url=s.get("al", {}).get("picUrl", "")
                )
                for s in daily_songs[:limit]
            ]
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return []
