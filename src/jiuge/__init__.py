"""
Jiuge - OpenClaw 音乐智能体
统一多平台音乐控制
"""

__version__ = "1.0.0"
__author__ = "DaimaRuge"

from .agent import JiugeAgent
from .service import UnifiedMusicService
from .memory import MusicMemoryStore

__all__ = [
    "JiugeAgent",
    "UnifiedMusicService", 
    "MusicMemoryStore"
]
