"""
本地音频播放器
"""

import threading
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LocalPlayer:
    """本地音频播放器"""
    
    def __init__(self):
        self.player = None
        self.state = "stopped"  # stopped, playing, paused
        self.position = 0
        self._thread: Optional[threading.Thread] = None
        self._stop_monitor = False
    
    async def play(self, url: str):
        """播放"""
        try:
            from ffpyplayer.player import MediaPlayer
            
            # 停止当前播放
            if self.player:
                self._stop_monitor = True
                self.player.close_player()
                time.sleep(0.1)
            
            self.player = MediaPlayer(url)
            self._stop_monitor = False
            self.state = "playing"
            
            # 启动监控线程
            self._thread = threading.Thread(target=self._monitor, daemon=True)
            self._thread.start()
            
        except ImportError:
            logger.error("请安装 ffpyplayer: pip install ffpyplayer")
            raise
        except Exception as e:
            logger.error(f"播放失败: {e}")
            raise
    
    def _monitor(self):
        """监控播放进度"""
        while not self._stop_monitor and self.player:
            try:
                state = self.player.get_state()
                if state == "eof":
                    self.state = "stopped"
                    break
                elif state == "playing":
                    self.position = int(self.player.get_pts() or 0)
                time.sleep(0.5)
            except:
                break
    
    async def pause(self):
        """暂停"""
        if self.player and self.state == "playing":
            self.player.toggle_pause()
            self.state = "paused"
    
    async def resume(self):
        """继续"""
        if self.player and self.state == "paused":
            self.player.toggle_pause()
            self.state = "playing"
    
    async def stop(self):
        """停止"""
        if self.player:
            self._stop_monitor = True
            self.player.close_player()
            self.player = None
        
        self.state = "stopped"
        self.position = 0
    
    async def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "state": self.state,
            "position": self._format_position(self.position)
        }
    
    def _format_position(self, seconds: int) -> str:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
