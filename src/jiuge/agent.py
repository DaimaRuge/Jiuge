"""
Jiuge Agent - OpenClaw 音乐智能体核心
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import re
import logging

from .service import UnifiedMusicService
from .memory import MusicMemoryStore
from .adapters.base import Track

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """指令类型"""
    SEARCH = "search"
    PLAY = "play"
    PAUSE = "pause"
    RESUME = "resume"
    NEXT = "next"
    PREVIOUS = "previous"
    STOP = "stop"
    FAVORITE = "favorite"
    UNFAVORITE = "unfavorite"
    PLAYLIST_CREATE = "playlist_create"
    PLAYLIST_ADD = "playlist_add"
    PLAYLIST_LIST = "playlist_list"
    RECOMMEND = "recommend"
    STATS = "stats"
    STATUS = "status"
    VOLUME = "volume"
    SHUFFLE = "shuffle"
    LOOP = "loop"
    UPLOAD = "upload"
    HELP = "help"


@dataclass
class Command:
    """解析后的指令"""
    type: Optional[CommandType]
    params: Dict[str, Any]
    raw_text: str


class CommandParser:
    """指令解析器"""
    
    PATTERNS = {
        CommandType.SEARCH: [
            r"^(?:听|搜索|找|播放)(.+)(?:的歌|歌曲|音乐)?$",
            r"^search\s+(.+)$",
            r"^play\s+(.+)$",
        ],
        CommandType.PLAY: [
            r"^播放\s*第?\s*(\d+)\s*首?$",
            r"^play\s+(\d+)$",
        ],
        CommandType.PAUSE: [
            r"^暂停$",
            r"^pause$",
        ],
        CommandType.RESUME: [
            r"^(?:继续|恢复)$",
            r"^resume$",
            r"^continue$",
        ],
        CommandType.NEXT: [
            r"^(?:下一首|下一曲|跳过|切歌)$",
            r"^next$",
            r"^skip$",
        ],
        CommandType.PREVIOUS: [
            r"^(?:上一首|上一曲|返回)$",
            r"^prev(?:ious)?$",
            r"^back$",
        ],
        CommandType.STOP: [
            r"^停止$",
            r"^stop$",
        ],
        CommandType.FAVORITE: [
            r"^(?:收藏|加入收藏|喜欢|爱心)$",
            r"^favorite$",
            r"^like$",
            r"^❤️?$",
        ],
        CommandType.UNFAVORITE: [
            r"^(?:取消收藏|取消喜欢|移除收藏)$",
            r"^unfavorite$",
            r"^unlike$",
        ],
        CommandType.PLAYLIST_CREATE: [
            r"^创建歌单\s+(.+)$",
            r"^新建歌单\s+(.+)$",
            r"^new playlist\s+(.+)$",
        ],
        CommandType.PLAYLIST_ADD: [
            r"^添加到歌单\s+(.+)$",
            r"^add to\s+(.+)$",
        ],
        CommandType.PLAYLIST_LIST: [
            r"^(?:歌单列表|我的歌单|歌单)$",
            r"^playlists$",
        ],
        CommandType.RECOMMEND: [
            r"^(?:推荐|每日推荐|给我推荐|推荐歌曲)$",
            r"^recommend$",
        ],
        CommandType.STATS: [
            r"^(?:统计|听歌统计|播放记录|听歌记录)$",
            r"^stats$",
        ],
        CommandType.STATUS: [
            r"^(?:状态|播放状态|当前播放)$",
            r"^status$",
        ],
        CommandType.VOLUME: [
            r"^(?:音量|声音)\s*(\d+)%?$",
            r"^volume\s+(\d+)$",
        ],
        CommandType.SHUFFLE: [
            r"^(?:随机播放|乱序)$",
            r"^shuffle$",
        ],
        CommandType.LOOP: [
            r"^(?:循环|单曲循环|列表循环)$",
            r"^loop$",
        ],
        CommandType.HELP: [
            r"^(?:帮助|help|\?)$",
        ],
    }
    
    def parse(self, text: str) -> Command:
        """解析用户输入"""
        text = text.strip()
        
        for cmd_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.match(pattern, text, re.IGNORECASE)
                if match:
                    params = {}
                    groups = match.groups()
                    if groups:
                        if len(groups) == 1:
                            params["arg"] = groups[0]
                        else:
                            params["args"] = groups
                    
                    return Command(
                        type=cmd_type,
                        params=params,
                        raw_text=text
                    )
        
        # 未知指令，尝试作为搜索
        if len(text) > 1:
            return Command(
                type=CommandType.SEARCH,
                params={"arg": text},
                raw_text=text
            )
        
        return Command(
            type=None,
            params={},
            raw_text=text
        )


class JiugeAgent:
    """Jiuge 音乐智能体"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.parser = CommandParser()
        self.service = UnifiedMusicService(config.get("platforms", {}))
        self.memory = MusicMemoryStore(config.get("memory", {}).get("db_path"))
        
        self._last_results: List[Track] = []
    
    async def handle_message(self, message: str, context: Dict = None) -> str:
        """
        处理用户消息
        
        Args:
            message: 用户输入
            context: 上下文信息（channel, user_id 等）
        
        Returns:
            响应文本
        """
        command = self.parser.parse(message)
        
        if command.type is None:
            return self._help_response()
        
        handler = getattr(self, f"_handle_{command.type.value}", None)
        if handler:
            try:
                return await handler(command.params, context)
            except Exception as e:
                logger.error(f"处理指令失败: {e}")
                return f"处理失败：{str(e)}"
        
        return self._help_response()
    
    async def _handle_search(self, params: Dict, context: Dict) -> str:
        """处理搜索"""
        query = params.get("arg", "")
        if not query:
            return "请输入要搜索的歌曲或歌手名"
        
        results = await self.service.search(query)
        self._last_results = results
        
        if not results:
            return f"没有找到「{query}」相关的歌曲"
        
        lines = [f"🎵 搜索「{query}」找到 {len(results)} 首歌曲：\n"]
        for i, track in enumerate(results[:10], 1):
            artists = "、".join(track.artists[:2])
            duration = self._format_duration(track.duration)
            platform_icon = self._get_platform_icon(track.platform)
            lines.append(f"{i}. {track.title} - {artists} ({duration}) {platform_icon}")
        
        lines.append("\n回复序号播放，如「播放 1」")
        return "\n".join(lines)
    
    async def _handle_play(self, params: Dict, context: Dict) -> str:
        """处理播放"""
        try:
            index = int(params.get("arg", "1")) - 1
        except ValueError:
            return "请输入有效的序号"
        
        if not self._last_results:
            return "请先搜索歌曲"
        
        if index < 0 or index >= len(self._last_results):
            return f"无效序号，请选择 1-{len(self._last_results)}"
        
        track = await self.service.play(index)
        if track:
            artists = "、".join(track.artists)
            return f"▶️ 正在播放：{track.title} - {artists}"
        
        return "播放失败"
    
    async def _handle_pause(self, params: Dict, context: Dict) -> str:
        """处理暂停"""
        await self.service.pause()
        return "⏸️ 已暂停"
    
    async def _handle_resume(self, params: Dict, context: Dict) -> str:
        """处理继续"""
        await self.service.resume()
        return "▶️ 继续播放"
    
    async def _handle_next(self, params: Dict, context: Dict) -> str:
        """处理下一首"""
        track = await self.service.next()
        if track:
            artists = "、".join(track.artists)
            return f"⏭️ 下一首：{track.title} - {artists}"
        return "已经是最后一首了"
    
    async def _handle_previous(self, params: Dict, context: Dict) -> str:
        """处理上一首"""
        track = await self.service.previous()
        if track:
            artists = "、".join(track.artists)
            return f"⏮️ 上一首：{track.title} - {artists}"
        return "已经是第一首了"
    
    async def _handle_stop(self, params: Dict, context: Dict) -> str:
        """处理停止"""
        await self.service.stop()
        return "⏹️ 已停止播放"
    
    async def _handle_favorite(self, params: Dict, context: Dict) -> str:
        """处理收藏"""
        success = await self.service.favorite()
        if success:
            return "❤️ 已添加到收藏"
        return "收藏失败"
    
    async def _handle_recommend(self, params: Dict, context: Dict) -> str:
        """处理推荐"""
        tracks = await self.service.get_recommendations()
        
        if not tracks:
            return "暂时没有推荐"
        
        lines = ["🎵 为你推荐：\n"]
        for i, track in enumerate(tracks[:10], 1):
            artists = "、".join(track.artists[:2])
            lines.append(f"{i}. {track.title} - {artists}")
        
        self._last_results = tracks
        lines.append("\n回复序号播放")
        return "\n".join(lines)
    
    async def _handle_stats(self, params: Dict, context: Dict) -> str:
        """处理统计"""
        stats = self.memory.get_stats("week")
        
        lines = [
            "📊 最近7天听歌统计：",
            f"• 播放次数：{stats['total_plays']}",
            f"• 听过歌曲：{stats['unique_tracks']} 首",
            "",
            "🔥 热门歌曲："
        ]
        
        for i, track in enumerate(stats["top_tracks"][:5], 1):
            lines.append(f"  {i}. {track['title']} ({track.get('play_count', 0)}次)")
        
        return "\n".join(lines)
    
    async def _handle_status(self, params: Dict, context: Dict) -> str:
        """处理状态查询"""
        status = await self.service.get_status()
        
        if status["state"] == "stopped":
            return "当前没有播放"
        
        track = status.get("current_track")
        if track:
            lines = [
                f"🎵 正在播放：{track['title']}",
                f"👤 歌手：{', '.join(track['artists'])}",
                f"💿 专辑：{track['album']}",
                f"⏱️ 进度：{track.get('position', '0:00')} / {track.get('duration', '0:00')}",
                f"📊 状态：{status['state']}"
            ]
            return "\n".join(lines)
        
        return "状态未知"
    
    async def _handle_help(self, params: Dict, context: Dict) -> str:
        """处理帮助"""
        return self._help_response()
    
    def _help_response(self) -> str:
        """帮助信息"""
        return """
🎵 Jiuge 音乐助手

可用指令：
• 听周杰伦的歌 - 搜索歌曲
• 播放 1 - 播放第1首
• 暂停 / 继续 - 播放控制
• 下一首 / 上一首 - 切换歌曲
• 收藏 - 收藏当前歌曲
• 推荐 - 获取推荐
• 统计 - 查看听歌统计
• 状态 - 查看播放状态
• 帮助 - 显示此帮助
        """.strip()
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """格式化时长"""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
    
    @staticmethod
    def _get_platform_icon(platform: str) -> str:
        """获取平台图标"""
        icons = {
            "spotify": "🟢",
            "netease": "🔴",
            "qqmusic": "🟢",
            "apple": "🔴"
        }
        return icons.get(platform, "🎵")
