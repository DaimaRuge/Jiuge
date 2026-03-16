"""
Jiuge - OpenClaw 网易云音乐控制
"""

from .netease_api import NeteaseMusic
from .music_player import MusicPlayer, get_player, PlayerState

__all__ = ["NeteaseMusic", "MusicPlayer", "get_player", "PlayerState"]
__version__ = "0.1.0"
