"""
音乐播放器模块
支持搜索、播放、暂停、切换等操作
"""

import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

try:
    from ffpyplayer.player import MediaPlayer
except ImportError:
    MediaPlayer = None
    print("警告: ffpyplayer 未安装，播放功能不可用")

from netease_api import NeteaseMusic


class PlayerState(Enum):
    """播放器状态"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


@dataclass
class Song:
    """歌曲信息"""
    id: int
    name: str
    artist: str
    album: str
    duration: int
    cover: str = ""
    url: str = ""


class MusicPlayer:
    """音乐播放器"""

    def __init__(self, on_state_change: Optional[Callable] = None):
        """
        初始化播放器

        Args:
            on_state_change: 状态变化回调函数
        """
        self.netease = NeteaseMusic()
        self.playlist: List[Song] = []
        self.state = PlayerState.STOPPED
        self.current_song: Optional[Song] = None
        self.current_index: int = -1
        self.position: int = 0
        self.player: Optional[MediaPlayer] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_monitor = False
        self.on_state_change = on_state_change

    def search(self, keywords: str, limit: int = 10) -> List[Dict]:
        """
        搜索歌曲并添加到播放列表

        Args:
            keywords: 搜索关键词
            limit: 返回数量

        Returns:
            搜索结果列表
        """
        results = self.netease.search(keywords, limit)

        # 清空当前播放列表并添加新结果
        self.playlist = []
        for r in results:
            self.playlist.append(Song(
                id=r["id"],
                name=r["name"],
                artist=r["artist"],
                album=r["album"],
                duration=r["duration"],
                cover=r.get("cover", "")
            ))

        return results

    def play(self, index: int = None) -> Dict:
        """
        播放歌曲

        Args:
            index: 播放列表索引，None 表示播放当前或第一首

        Returns:
            播放状态
        """
        if not self.playlist:
            return {"error": "播放列表为空，请先搜索歌曲"}

        # 确定播放索引
        if index is not None:
            if 0 <= index < len(self.playlist):
                self.current_index = index
            else:
                return {"error": f"无效索引，请选择 1-{len(self.playlist)}"}
        elif self.current_index < 0:
            self.current_index = 0

        song = self.playlist[self.current_index]

        # 获取播放地址
        if not song.url:
            url = self.netease.get_song_url(song.id)
            if not url:
                return {"error": f"无法获取《{song.name}》的播放地址"}
            song.url = url

        # 开始播放
        self._play_url(song.url)

        self.state = PlayerState.PLAYING
        self.current_song = song
        self.position = 0

        self._notify_state_change()

        return {
            "success": True,
            "song": {
                "name": song.name,
                "artist": song.artist,
                "album": song.album,
                "duration": NeteaseMusic.format_duration(song.duration)
            },
            "state": self.state.value
        }

    def _play_url(self, url: str):
        """播放指定URL"""
        if MediaPlayer is None:
            raise RuntimeError("ffpyplayer 未安装")

        # 停止当前播放
        if self.player:
            self._stop_monitor = True
            self.player.close_player()
            self.player = None
            time.sleep(0.1)

        # 创建新播放器
        self.player = MediaPlayer(url)
        self._stop_monitor = False

        # 启动监控线程
        self._thread = threading.Thread(target=self._monitor_playback, daemon=True)
        self._thread.start()

    def _monitor_playback(self):
        """监控播放进度"""
        while not self._stop_monitor and self.player:
            try:
                state = self.player.get_state()
                if state == "eof":
                    self._on_song_end()
                    break
                elif state == "playing":
                    self.position = int(self.player.get_pts())
                time.sleep(0.5)
            except:
                break

    def _on_song_end(self):
        """歌曲播放结束"""
        if self.current_index < len(self.playlist) - 1:
            self.play(self.current_index + 1)
        else:
            self.state = PlayerState.STOPPED
            self.current_song = None
            self._notify_state_change()

    def pause(self) -> Dict:
        """暂停播放"""
        if self.player and self.state == PlayerState.PLAYING:
            self.player.toggle_pause()
            self.state = PlayerState.PAUSED
            self._notify_state_change()
            return {"success": True, "state": "paused"}
        return {"error": "当前没有正在播放的歌曲"}

    def resume(self) -> Dict:
        """继续播放"""
        if self.player and self.state == PlayerState.PAUSED:
            self.player.toggle_pause()
            self.state = PlayerState.PLAYING
            self._notify_state_change()
            return {"success": True, "state": "playing"}
        return {"error": "当前没有暂停的歌曲"}

    def next(self) -> Dict:
        """下一首"""
        if self.current_index < len(self.playlist) - 1:
            return self.play(self.current_index + 1)
        return {"error": "已经是最后一首了"}

    def prev(self) -> Dict:
        """上一首"""
        if self.current_index > 0:
            return self.play(self.current_index - 1)
        return {"error": "已经是第一首了"}

    def stop(self) -> Dict:
        """停止播放"""
        if self.player:
            self._stop_monitor = True
            self.player.close_player()
            self.player = None

        self.state = PlayerState.STOPPED
        self.current_song = None
        self.position = 0
        self._notify_state_change()

        return {"success": True, "state": "stopped"}

    def get_status(self) -> Dict:
        """获取播放状态"""
        song_info = None
        if self.current_song:
            song_info = {
                "name": self.current_song.name,
                "artist": self.current_song.artist,
                "album": self.current_song.album,
                "position": NeteaseMusic.format_duration(self.position),
                "duration": NeteaseMusic.format_duration(self.current_song.duration)
            }

        return {
            "state": self.state.value,
            "current_song": song_info,
            "playlist_count": len(self.playlist),
            "current_index": self.current_index + 1 if self.current_index >= 0 else 0
        }

    def get_playlist(self) -> List[Dict]:
        """获取播放列表"""
        return [
            {
                "index": i + 1,
                "name": s.name,
                "artist": s.artist,
                "duration": NeteaseMusic.format_duration(s.duration),
                "is_current": i == self.current_index
            }
            for i, s in enumerate(self.playlist)
        ]

    def clear_playlist(self):
        """清空播放列表"""
        self.stop()
        self.playlist = []
        self.current_index = -1

    def _notify_state_change(self):
        """通知状态变化"""
        if self.on_state_change:
            try:
                self.on_state_change(self.get_status())
            except:
                pass


# 全局播放器实例
_player: Optional[MusicPlayer] = None


def get_player(on_state_change: Optional[Callable] = None) -> MusicPlayer:
    """获取全局播放器实例"""
    global _player
    if _player is None:
        _player = MusicPlayer(on_state_change)
    return _player
