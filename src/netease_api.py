"""
网易云音乐 API 封装
基于 NeteaseCloudMusicApi Python SDK
"""

import os
from typing import List, Dict, Optional
from NeteaseCloudMusic import NeteaseCloudMusicApi


class NeteaseMusic:
    """网易云音乐 API 客户端"""

    def __init__(self, cookie: Optional[str] = None):
        self.api = NeteaseCloudMusicApi()
        if cookie:
            self.api.cookie = cookie
        elif os.getenv("NETEASE_COOKIE"):
            self.api.cookie = os.getenv("NETEASE_COOKIE")

    def search(self, keywords: str, limit: int = 10, search_type: int = 1) -> List[Dict]:
        """
        搜索歌曲

        Args:
            keywords: 搜索关键词
            limit: 返回数量，默认10
            search_type: 搜索类型，1=单曲，10=专辑，100=歌手，1000=歌单

        Returns:
            歌曲列表
        """
        try:
            result = self.api.request("search", {
                "keywords": keywords,
                "limit": limit,
                "type": search_type
            })
            return self._parse_search_result(result)
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def get_song_url(self, song_id: int, level: str = "exhigh") -> Optional[str]:
        """
        获取歌曲播放地址

        Args:
            song_id: 歌曲ID
            level: 音质等级 (standard/higher/exhigh/lossless/hires)

        Returns:
            播放URL或None
        """
        try:
            result = self.api.request("song_url_v1", {
                "id": song_id,
                "level": level
            })
            data = result.get("data", [])
            if data:
                return data[0].get("url")
        except Exception as e:
            print(f"获取播放地址失败: {e}")
        return None

    def get_song_detail(self, song_ids: List[int]) -> List[Dict]:
        """
        获取歌曲详情

        Args:
            song_ids: 歌曲ID列表

        Returns:
            歌曲详情列表
        """
        try:
            result = self.api.request("song_detail", {
                "ids": ",".join(map(str, song_ids))
            })
            songs = result.get("songs", [])
            return [self._format_song(s) for s in songs]
        except Exception as e:
            print(f"获取歌曲详情失败: {e}")
            return []

    def _parse_search_result(self, result: Dict) -> List[Dict]:
        """解析搜索结果"""
        songs = result.get("result", {}).get("songs", [])
        return [self._format_song(s) for s in songs]

    def _format_song(self, song: Dict) -> Dict:
        """格式化歌曲信息"""
        return {
            "id": song.get("id"),
            "name": song.get("name", "未知"),
            "artist": ", ".join([a.get("name", "") for a in song.get("artists", [])]),
            "album": song.get("album", {}).get("name", ""),
            "duration": song.get("duration", 0) // 1000,  # ms -> s
            "cover": song.get("album", {}).get("picUrl", "")
        }

    @staticmethod
    def format_duration(seconds: int) -> str:
        """格式化时长"""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
