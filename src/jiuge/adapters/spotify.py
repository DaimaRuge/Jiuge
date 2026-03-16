"""
Spotify 适配器
基于 spotipy 库
"""

from typing import List, Optional
import logging

from .base import MusicPlatformAdapter, Track, Playlist

logger = logging.getLogger(__name__)


class SpotifyAdapter(MusicPlatformAdapter):
    """Spotify 适配器"""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8888/callback"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._sp = None
        self._authenticated = False
    
    @property
    def name(self) -> str:
        return "spotify"
    
    @property
    def is_authenticated(self) -> bool:
        return self._authenticated
    
    def _get_client(self):
        """获取 Spotify 客户端"""
        if self._sp is None:
            try:
                import spotipy
                from spotipy.oauth2 import SpotifyOAuth
                
                self._sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    scope="user-library-read user-library-modify "
                          "user-read-recently-played user-top-read "
                          "playlist-read-private playlist-modify-public "
                          "playlist-modify-private user-read-playback-state "
                          "user-modify-playback-state"
                ))
                self._authenticated = True
            except ImportError:
                logger.error("请安装 spotipy: pip install spotipy")
                raise
        return self._sp
    
    async def authenticate(self) -> bool:
        """认证"""
        try:
            self._get_client()
            return True
        except Exception as e:
            logger.error(f"Spotify 认证失败: {e}")
            return False
    
    async def search(
        self, 
        query: str, 
        limit: int = 10,
        search_type: str = "track"
    ) -> List[Track]:
        """搜索"""
        sp = self._get_client()
        
        try:
            results = sp.search(q=query, limit=limit, type=search_type)
            
            tracks = []
            for item in results.get("tracks", {}).get("items", []):
                tracks.append(Track(
                    id=f"spotify:{item['id']}",
                    platform="spotify",
                    platform_id=item["id"],
                    title=item["name"],
                    artists=[a["name"] for a in item.get("artists", [])],
                    album=item.get("album", {}).get("name", ""),
                    duration=item.get("duration_ms", 0) // 1000,
                    cover_url=item.get("album", {}).get("images", [{}])[0].get("url", "")
                ))
            
            return tracks
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    async def get_track_url(self, track_id: str) -> Optional[str]:
        """获取播放地址（Spotify 需要通过播放器 API）"""
        # Spotify 不直接提供音频 URL，需要通过播放 API
        return None
    
    async def get_track_info(self, track_id: str) -> Optional[Track]:
        """获取歌曲详情"""
        sp = self._get_client()
        
        if ":" in track_id:
            track_id = track_id.split(":")[1]
        
        try:
            item = sp.track(track_id)
            
            return Track(
                id=f"spotify:{item['id']}",
                platform="spotify",
                platform_id=item["id"],
                title=item["name"],
                artists=[a["name"] for a in item.get("artists", [])],
                album=item.get("album", {}).get("name", ""),
                duration=item.get("duration_ms", 0) // 1000,
                cover_url=item.get("album", {}).get("images", [{}])[0].get("url", "")
            )
        except Exception as e:
            logger.error(f"获取歌曲详情失败: {e}")
        
        return None
    
    async def get_playlists(self) -> List[Playlist]:
        """获取用户歌单"""
        sp = self._get_client()
        
        try:
            results = sp.current_user_playlists()
            
            return [
                Playlist(
                    id=f"spotify:{p['id']}",
                    name=p["name"],
                    platform="spotify",
                    description=p.get("description", ""),
                    track_count=p.get("tracks", {}).get("total", 0),
                    cover_url=p.get("images", [{}])[0].get("url", "")
                )
                for p in results.get("items", [])
            ]
        except Exception as e:
            logger.error(f"获取歌单失败: {e}")
            return []
    
    async def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """获取歌单详情"""
        sp = self._get_client()
        
        if ":" in playlist_id:
            playlist_id = playlist_id.split(":")[1]
        
        try:
            result = sp.playlist(playlist_id)
            
            tracks = []
            for item in result.get("tracks", {}).get("items", []):
                t = item.get("track", {})
                if t:
                    tracks.append(Track(
                        id=f"spotify:{t['id']}",
                        platform="spotify",
                        platform_id=t["id"],
                        title=t["name"],
                        artists=[a["name"] for a in t.get("artists", [])],
                        album=t.get("album", {}).get("name", ""),
                        duration=t.get("duration_ms", 0) // 1000
                    ))
            
            return Playlist(
                id=f"spotify:{playlist_id}",
                name=result.get("name", ""),
                platform="spotify",
                description=result.get("description", ""),
                track_count=result.get("tracks", {}).get("total", 0),
                cover_url=result.get("images", [{}])[0].get("url", ""),
                tracks=tracks
            )
        except Exception as e:
            logger.error(f"获取歌单详情失败: {e}")
        
        return None
    
    async def create_playlist(self, name: str, description: str = "") -> Optional[Playlist]:
        """创建歌单"""
        sp = self._get_client()
        
        try:
            user_id = sp.current_user()["id"]
            result = sp.user_playlist_create(
                user=user_id,
                name=name,
                description=description
            )
            
            return Playlist(
                id=f"spotify:{result['id']}",
                name=result["name"],
                platform="spotify",
                description=result.get("description", "")
            )
        except Exception as e:
            logger.error(f"创建歌单失败: {e}")
        
        return None
    
    async def add_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """添加歌曲到歌单"""
        sp = self._get_client()
        
        if ":" in playlist_id:
            playlist_id = playlist_id.split(":")[1]
        
        uris = [
            f"spotify:track:{tid.split(':')[-1]}" if ":" in tid else f"spotify:track:{tid}"
            for tid in track_ids
        ]
        
        try:
            sp.playlist_add_items(playlist_id, uris)
            return True
        except Exception as e:
            logger.error(f"添加歌曲失败: {e}")
        
        return False
    
    async def favorite(self, track_id: str) -> bool:
        """收藏歌曲"""
        sp = self._get_client()
        
        if ":" in track_id:
            track_id = track_id.split(":")[1]
        
        try:
            sp.current_user_saved_tracks_add([track_id])
            return True
        except Exception as e:
            logger.error(f"收藏失败: {e}")
        
        return False
    
    async def unfavorite(self, track_id: str) -> bool:
        """取消收藏"""
        sp = self._get_client()
        
        if ":" in track_id:
            track_id = track_id.split(":")[1]
        
        try:
            sp.current_user_saved_tracks_delete([track_id])
            return True
        except Exception as e:
            logger.error(f"取消收藏失败: {e}")
        
        return False
    
    async def get_favorites(self, limit: int = 50) -> List[Track]:
        """获取收藏列表"""
        sp = self._get_client()
        
        try:
            results = sp.current_user_saved_tracks(limit=limit)
            
            return [
                Track(
                    id=f"spotify:{item['track']['id']}",
                    platform="spotify",
                    platform_id=item["track"]["id"],
                    title=item["track"]["name"],
                    artists=[a["name"] for a in item["track"].get("artists", [])],
                    album=item["track"].get("album", {}).get("name", ""),
                    duration=item["track"].get("duration_ms", 0) // 1000
                )
                for item in results.get("items", [])
            ]
        except Exception as e:
            logger.error(f"获取收藏失败: {e}")
            return []
    
    async def get_recommendations(self, limit: int = 10) -> List[Track]:
        """获取推荐"""
        sp = self._get_client()
        
        try:
            # 基于最近播放获取推荐
            recent = sp.current_user_recently_played(limit=5)
            seed_tracks = [item["track"]["id"] for item in recent["items"][:5]]
            
            results = sp.recommendations(
                seed_tracks=seed_tracks,
                limit=limit
            )
            
            return [
                Track(
                    id=f"spotify:{t['id']}",
                    platform="spotify",
                    platform_id=t["id"],
                    title=t["name"],
                    artists=[a["name"] for a in t.get("artists", [])],
                    album=t.get("album", {}).get("name", ""),
                    duration=t.get("duration_ms", 0) // 1000,
                    cover_url=t.get("album", {}).get("images", [{}])[0].get("url", "")
                )
                for t in results.get("tracks", [])
            ]
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return []
