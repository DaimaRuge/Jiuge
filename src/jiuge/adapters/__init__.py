"""
平台适配器模块

提供多个音乐平台的适配器实现：
- NeteaseAdapter: 网易云音乐
- SpotifyAdapter: Spotify
- QQMusicAdapter: QQ 音乐
- AppleMusicAdapter: Apple Music
"""

from .base import MusicPlatformAdapter, Track, Playlist
from .netease import NeteaseAdapter
from .spotify import SpotifyAdapter
from .qqmusic import QQMusicAdapter
from .apple import AppleMusicAdapter

__all__ = [
    "MusicPlatformAdapter",
    "Track",
    "Playlist",
    "NeteaseAdapter",
    "SpotifyAdapter",
    "QQMusicAdapter",
    "AppleMusicAdapter"
]
