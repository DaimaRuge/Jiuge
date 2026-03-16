# Jiuge 系统架构文档

**版本**: v1.0  
**日期**: 2026-03-17

---

## 1. 架构概览

### 1.1 分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                          │
│         (Feishu / Telegram / Discord / Voice / Web)             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Layer                               │
│                     (OpenClaw Skill)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Parser    │  │   Router    │  │  Response   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Unified Music Service                  │   │
│  │  search() | play() | playlist() | favorite() | upload() │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Platform Adapters                      │   │
│  │  Spotify | QQ Music | Netease | Apple Music             │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Audio Player                           │   │
│  │  Local (ffpyplayer) | Remote (Platform API)             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │  Tracks   │  │ Playlists │  │  History  │  │ Preferences│   │
│  │  (SQLite) │  │  (SQLite) │  │  (SQLite) │  │   (JSON)  │   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Services                            │
│  Spotify API | QQ Music API | Netease API | Apple Music API    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 组件职责

| 层级 | 组件 | 职责 |
|------|------|------|
| Presentation | Channel Handlers | 接收多渠道消息 |
| Agent | Parser | 解析用户指令 |
| Agent | Router | 路由到对应服务 |
| Agent | Response | 格式化响应 |
| Service | Unified Music Service | 统一音乐操作接口 |
| Service | Platform Adapters | 封装平台 API |
| Service | Audio Player | 本地音频播放 |
| Data | SQLite Store | 持久化存储 |

---

## 2. 核心组件设计

### 2.1 指令解析器 (Parser)

```python
from dataclasses import dataclass
from enum import Enum
import re

class CommandType(Enum):
    SEARCH = "search"
    PLAY = "play"
    PAUSE = "pause"
    RESUME = "resume"
    NEXT = "next"
    PREVIOUS = "previous"
    STOP = "stop"
    FAVORITE = "favorite"
    PLAYLIST_CREATE = "playlist_create"
    PLAYLIST_ADD = "playlist_add"
    RECOMMEND = "recommend"
    STATS = "stats"

@dataclass
class Command:
    type: CommandType
    params: dict
    raw_text: str

class CommandParser:
    PATTERNS = {
        CommandType.SEARCH: [
            r"^(?:听|搜索|找)(.+)(?:的歌|歌曲)?$",
            r"^search\s+(.+)$",
        ],
        CommandType.PLAY: [
            r"^播放\s*(\d+)$",
            r"^play\s+(\d+)$",
        ],
        CommandType.PAUSE: [
            r"^暂停$",
            r"^pause$",
        ],
        CommandType.RESUME: [
            r"^(?:继续|恢复)$",
            r"^resume$",
        ],
        CommandType.NEXT: [
            r"^(?:下一首|下一曲|跳过)$",
            r"^next$",
        ],
        CommandType.PREVIOUS: [
            r"^(?:上一首|上一曲)$",
            r"^prev(?:ious)?$",
        ],
        CommandType.STOP: [
            r"^停止$",
            r"^stop$",
        ],
        CommandType.FAVORITE: [
            r"^(?:收藏|加入收藏|喜欢)$",
            r"^favorite$",
        ],
        CommandType.PLAYLIST_CREATE: [
            r"^创建歌单\s+(.+)$",
            r"^new playlist\s+(.+)$",
        ],
        CommandType.RECOMMEND: [
            r"^(?:推荐|每日推荐|给我推荐)$",
            r"^recommend$",
        ],
        CommandType.STATS: [
            r"^(?:统计|听歌统计|播放记录)$",
            r"^stats$",
        ],
    }
    
    def parse(self, text: str) -> Command:
        text = text.strip()
        for cmd_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.match(pattern, text, re.IGNORECASE)
                if match:
                    params = match.groupdict() or {}
                    if match.groups():
                        params["match_groups"] = match.groups()
                    return Command(type=cmd_type, params=params, raw_text=text)
        return Command(type=None, params={}, raw_text=text)
```

### 2.2 平台适配器 (Adapter)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Track:
    id: str
    platform: str
    platform_id: str
    title: str
    artists: List[str]
    album: str
    duration: int
    cover_url: str
    audio_url: Optional[str] = None

class MusicPlatformAdapter(ABC):
    """音乐平台适配器基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """平台名称"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Track]:
        """搜索歌曲"""
        pass
    
    @abstractmethod
    async def get_track_url(self, track_id: str) -> Optional[str]:
        """获取播放地址"""
        pass
    
    @abstractmethod
    async def get_playlists(self) -> List[dict]:
        """获取用户歌单"""
        pass
    
    @abstractmethod
    async def create_playlist(
        self, 
        name: str, 
        description: str = ""
    ) -> dict:
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
    async def get_recommendations(
        self, 
        limit: int = 10
    ) -> List[Track]:
        """获取推荐"""
        pass
```

### 2.3 网易云音乐适配器

```python
from .base import MusicPlatformAdapter, Track
from NeteaseCloudMusic import NeteaseCloudMusicApi
from typing import List, Optional
import os

class NeteaseAdapter(MusicPlatformAdapter):
    """网易云音乐适配器"""
    
    def __init__(self, cookie: Optional[str] = None):
        self.api = NeteaseCloudMusicApi()
        if cookie:
            self.api.cookie = cookie
        elif os.getenv("NETEASE_COOKIE"):
            self.api.cookie = os.getenv("NETEASE_COOKIE")
    
    @property
    def name(self) -> str:
        return "netease"
    
    async def search(self, query: str, limit: int = 10) -> List[Track]:
        result = self.api.request("search", {
            "keywords": query,
            "limit": limit,
            "type": 1
        })
        
        songs = result.get("result", {}).get("songs", [])
        return [
            Track(
                id=f"netease:{s['id']}",
                platform="netease",
                platform_id=str(s["id"]),
                title=s.get("name", ""),
                artists=[a["name"] for a in s.get("artists", [])],
                album=s.get("album", {}).get("name", ""),
                duration=s.get("duration", 0) // 1000,
                cover_url=s.get("album", {}).get("picUrl", "")
            )
            for s in songs
        ]
    
    async def get_track_url(self, track_id: str) -> Optional[str]:
        result = self.api.request("song_url_v1", {
            "id": track_id,
            "level": "exhigh"
        })
        data = result.get("data", [])
        return data[0].get("url") if data else None
    
    async def get_playlists(self) -> List[dict]:
        result = self.api.request("user_playlist", {
            "uid": self._get_user_id()
        })
        return result.get("playlist", [])
    
    async def create_playlist(self, name: str, description: str = "") -> dict:
        result = self.api.request("playlist_create", {
            "name": name,
            "privacy": 0  # 公开
        })
        return result
    
    async def add_to_playlist(
        self, 
        playlist_id: str, 
        track_ids: List[str]
    ) -> bool:
        result = self.api.request("playlist_tracks", {
            "op": "add",
            "pid": playlist_id,
            "tracks": ",".join(track_ids)
        })
        return result.get("code") == 200
    
    async def favorite(self, track_id: str) -> bool:
        result = self.api.request("like", {
            "id": track_id,
            "like": True
        })
        return result.get("code") == 200
    
    async def get_recommendations(self, limit: int = 10) -> List[Track]:
        result = self.api.request("recommend_songs", {})
        # 解析推荐结果...
        pass
    
    def _get_user_id(self) -> str:
        # 从 cookie 或 API 获取用户 ID
        pass
```

### 2.4 Spotify 适配器

```python
from .base import MusicPlatformAdapter, Track
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Optional

class SpotifyAdapter(MusicPlatformAdapter):
    """Spotify 适配器"""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-library-read user-library-modify "
                  "user-read-playback-state user-modify-playback-state "
                  "playlist-read-private playlist-modify-public playlist-modify-private"
        ))
    
    @property
    def name(self) -> str:
        return "spotify"
    
    async def search(self, query: str, limit: int = 10) -> List[Track]:
        results = self.sp.search(q=query, type='track', limit=limit)
        tracks = results['tracks']['items']
        
        return [
            Track(
                id=f"spotify:{t['id']}",
                platform="spotify",
                platform_id=t["id"],
                title=t["name"],
                artists=[a["name"] for a in t["artists"]],
                album=t["album"]["name"],
                duration=t["duration_ms"] // 1000,
                cover_url=t["album"]["images"][0]["url"] if t["album"]["images"] else ""
            )
            for t in tracks
        ]
    
    async def get_track_url(self, track_id: str) -> Optional[str]:
        # Spotify 需要通过 playback API 播放
        # 这里返回 track URI
        return f"spotify:track:{track_id}"
    
    async def play(self, track_uri: str):
        """在活跃设备上播放"""
        self.sp.start_playback(uris=[track_uri])
    
    async def pause(self):
        self.sp.pause_playback()
    
    async def get_playlists(self) -> List[dict]:
        results = self.sp.current_user_playlists()
        return results['items']
    
    async def create_playlist(self, name: str, description: str = "") -> dict:
        user_id = self.sp.current_user()['id']
        return self.sp.user_playlist_create(
            user=user_id,
            name=name,
            description=description
        )
    
    async def add_to_playlist(
        self, 
        playlist_id: str, 
        track_ids: List[str]
    ) -> bool:
        track_uris = [f"spotify:track:{tid}" for tid in track_ids]
        self.sp.playlist_add_items(playlist_id, track_uris)
        return True
    
    async def favorite(self, track_id: str) -> bool:
        self.sp.current_user_saved_tracks_add([track_id])
        return True
    
    async def get_recommendations(self, limit: int = 10) -> List[Track]:
        # 基于最近播放获取推荐
        recent = self.sp.current_user_recently_played(limit=5)
        seed_tracks = [item['track']['id'] for item in recent['items'][:5]]
        
        results = self.sp.recommendations(
            seed_tracks=seed_tracks,
            limit=limit
        )
        
        return [
            Track(
                id=f"spotify:{t['id']}",
                platform="spotify",
                platform_id=t["id"],
                title=t["name"],
                artists=[a["name"] for a in t["artists"]],
                album=t["album"]["name"],
                duration=t["duration_ms"] // 1000,
                cover_url=t["album"]["images"][0]["url"] if t["album"]["images"] else ""
            )
            for t in results['tracks']
        ]
```

### 2.5 统一音乐服务

```python
from typing import List, Optional, Dict
from .adapters.base import Track
from .adapters.netease import NeteaseAdapter
from .adapters.spotify import SpotifyAdapter
from .player.local import LocalPlayer
from .memory.store import MusicMemoryStore

class UnifiedMusicService:
    """统一音乐服务"""
    
    def __init__(self, config: dict):
        self.adapters: Dict[str, MusicPlatformAdapter] = {}
        self.player = LocalPlayer()
        self.memory = MusicMemoryStore()
        self.current_playlist: List[Track] = []
        self.current_index = -1
        
        # 初始化适配器
        if config.get("netease"):
            self.adapters["netease"] = NeteaseAdapter(
                cookie=config["netease"].get("cookie")
            )
        
        if config.get("spotify"):
            self.adapters["spotify"] = SpotifyAdapter(
                client_id=config["spotify"]["client_id"],
                client_secret=config["spotify"]["client_secret"],
                redirect_uri=config["spotify"]["redirect_uri"]
            )
    
    async def search(
        self, 
        query: str, 
        platforms: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Track]:
        """跨平台搜索"""
        platforms = platforms or list(self.adapters.keys())
        all_tracks = []
        
        for platform in platforms:
            if platform in self.adapters:
                tracks = await self.adapters[platform].search(query, limit)
                all_tracks.extend(tracks)
        
        # 去重（基于歌曲名+歌手）
        seen = set()
        unique_tracks = []
        for track in all_tracks:
            key = (track.title.lower(), tuple(sorted(track.artists)))
            if key not in seen:
                seen.add(key)
                unique_tracks.append(track)
        
        # 保存到当前播放列表
        self.current_playlist = unique_tracks
        self.current_index = -1
        
        return unique_tracks[:limit]
    
    async def play(self, index: int = None) -> Optional[Track]:
        """播放歌曲"""
        if not self.current_playlist:
            return None
        
        if index is not None:
            self.current_index = index
        
        if self.current_index < 0:
            self.current_index = 0
        
        track = self.current_playlist[self.current_index]
        
        # 获取播放地址
        adapter = self.adapters.get(track.platform)
        if adapter:
            audio_url = await adapter.get_track_url(track.platform_id)
            if audio_url:
                await self.player.play(audio_url)
                
                # 记录播放历史
                self.memory.record_play(track)
                
                return track
        
        return None
    
    async def pause(self):
        """暂停"""
        await self.player.pause()
    
    async def resume(self):
        """继续"""
        await self.player.resume()
    
    async def next(self) -> Optional[Track]:
        """下一首"""
        if self.current_index < len(self.current_playlist) - 1:
            self.current_index += 1
            return await self.play()
        return None
    
    async def previous(self) -> Optional[Track]:
        """上一首"""
        if self.current_index > 0:
            self.current_index -= 1
            return await self.play()
        return None
    
    async def stop(self):
        """停止"""
        await self.player.stop()
        self.current_index = -1
    
    async def favorite(self) -> bool:
        """收藏当前歌曲"""
        if self.current_index < 0:
            return False
        
        track = self.current_playlist[self.current_index]
        adapter = self.adapters.get(track.platform)
        
        if adapter:
            success = await adapter.favorite(track.platform_id)
            if success:
                self.memory.add_favorite(track)
            return success
        
        return False
    
    async def get_recommendations(self, limit: int = 10) -> List[Track]:
        """获取推荐"""
        # 优先使用 Spotify 推荐
        if "spotify" in self.adapters:
            return await self.adapters["spotify"].get_recommendations(limit)
        
        # 回退到网易云
        if "netease" in self.adapters:
            return await self.adapters["netease"].get_recommendations(limit)
        
        return []
    
    def get_stats(self, period: str = "week") -> dict:
        """获取统计"""
        return self.memory.get_stats(period)
```

### 2.6 记忆存储

```python
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import json

class MusicMemoryStore:
    """音乐记忆存储"""
    
    def __init__(self, db_path: str = "~/.jiuge/memory.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id TEXT PRIMARY KEY,
                    platform TEXT,
                    platform_id TEXT,
                    title TEXT,
                    artists TEXT,
                    album TEXT,
                    duration INTEGER,
                    cover_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS play_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id TEXT,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_played INTEGER,
                    source TEXT,
                    FOREIGN KEY (track_id) REFERENCES tracks(id)
                );
                
                CREATE TABLE IF NOT EXISTS favorites (
                    track_id TEXT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (track_id) REFERENCES tracks(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_play_history_played_at 
                ON play_history(played_at);
            """)
    
    def save_track(self, track: dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tracks 
                (id, platform, platform_id, title, artists, album, duration, cover_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                track["id"],
                track["platform"],
                track["platform_id"],
                track["title"],
                json.dumps(track["artists"], ensure_ascii=False),
                track["album"],
                track["duration"],
                track["cover_url"]
            ))
    
    def record_play(self, track: dict, source: str = "unknown"):
        self.save_track(track)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO play_history (track_id, source)
                VALUES (?, ?)
            """, (track["id"], source))
    
    def add_favorite(self, track: dict):
        self.save_track(track)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO favorites (track_id)
                VALUES (?)
            """, (track["id"],))
    
    def remove_favorite(self, track_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM favorites WHERE track_id = ?", (track_id,))
    
    def get_favorites(self, limit: int = 100) -> List[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT t.*, f.added_at
                FROM favorites f
                JOIN tracks t ON f.track_id = t.id
                ORDER BY f.added_at DESC
                LIMIT ?
            """, (limit,))
            
            return [self._row_to_track(row) for row in cursor]
    
    def get_play_history(
        self, 
        days: int = 30, 
        limit: int = 100
    ) -> List[dict]:
        since = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT t.*, h.played_at, h.source
                FROM play_history h
                JOIN tracks t ON h.track_id = t.id
                WHERE h.played_at >= ?
                ORDER BY h.played_at DESC
                LIMIT ?
            """, (since.isoformat(), limit))
            
            return [self._row_to_track(row) for row in cursor]
    
    def get_stats(self, period: str = "week") -> dict:
        days = {"day": 1, "week": 7, "month": 30, "year": 365}.get(period, 7)
        since = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 总播放次数
            total_plays = conn.execute("""
                SELECT COUNT(*) as count FROM play_history
                WHERE played_at >= ?
            """, (since.isoformat(),)).fetchone()["count"]
            
            # 独立歌曲数
            unique_tracks = conn.execute("""
                SELECT COUNT(DISTINCT track_id) as count FROM play_history
                WHERE played_at >= ?
            """, (since.isoformat(),)).fetchone()["count"]
            
            # 热门歌曲
            top_tracks = conn.execute("""
                SELECT t.*, COUNT(*) as play_count
                FROM play_history h
                JOIN tracks t ON h.track_id = t.id
                WHERE h.played_at >= ?
                GROUP BY h.track_id
                ORDER BY play_count DESC
                LIMIT 10
            """, (since.isoformat(),)).fetchall()
            
            # 热门歌手
            top_artists = conn.execute("""
                SELECT json_extract(t.artists, '$[0]') as artist, COUNT(*) as play_count
                FROM play_history h
                JOIN tracks t ON h.track_id = t.id
                WHERE h.played_at >= ?
                GROUP BY artist
                ORDER BY play_count DESC
                LIMIT 10
            """, (since.isoformat(),)).fetchall()
            
            return {
                "period": period,
                "total_plays": total_plays,
                "unique_tracks": unique_tracks,
                "top_tracks": [self._row_to_track(t) for t in top_tracks],
                "top_artists": [
                    {"artist": r["artist"], "plays": r["play_count"]} 
                    for r in top_artists
                ]
            }
    
    def _row_to_track(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "platform": row["platform"],
            "platform_id": row["platform_id"],
            "title": row["title"],
            "artists": json.loads(row["artists"]) if row["artists"] else [],
            "album": row["album"],
            "duration": row["duration"],
            "cover_url": row["cover_url"]
        }
    
    def export(self) -> dict:
        """导出记忆数据"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            tracks = conn.execute("SELECT * FROM tracks").fetchall()
            history = conn.execute("SELECT * FROM play_history").fetchall()
            favorites = conn.execute("SELECT * FROM favorites").fetchall()
            
            return {
                "tracks": [dict(t) for t in tracks],
                "history": [dict(h) for h in history],
                "favorites": [dict(f) for f in favorites],
                "exported_at": datetime.now().isoformat()
            }
    
    def import_data(self, data: dict):
        """导入记忆数据"""
        with sqlite3.connect(self.db_path) as conn:
            for track in data.get("tracks", []):
                conn.execute("""
                    INSERT OR REPLACE INTO tracks 
                    (id, platform, platform_id, title, artists, album, duration, cover_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    track["id"], track["platform"], track["platform_id"],
                    track["title"], track["artists"], track["album"],
                    track["duration"], track["cover_url"]
                ))
            
            for record in data.get("history", []):
                conn.execute("""
                    INSERT INTO play_history (track_id, played_at, source)
                    VALUES (?, ?, ?)
                """, (record["track_id"], record["played_at"], record.get("source")))
            
            for fav in data.get("favorites", []):
                conn.execute("""
                    INSERT OR REPLACE INTO favorites (track_id, added_at)
                    VALUES (?, ?)
                """, (fav["track_id"], fav.get("added_at")))
```

---

## 3. 配置管理

### 3.1 配置文件结构

```yaml
# config.yaml

# 音乐平台配置
platforms:
  netease:
    enabled: true
    cookie: ${NETEASE_COOKIE}
  
  spotify:
    enabled: true
    client_id: ${SPOTIFY_CLIENT_ID}
    client_secret: ${SPOTIFY_CLIENT_SECRET}
    redirect_uri: http://localhost:8888/callback
  
  qqmusic:
    enabled: false
    app_id: ${QQMUSIC_APP_ID}
    app_secret: ${QQMUSIC_APP_SECRET}
  
  apple:
    enabled: false
    developer_token: ${APPLE_DEVELOPER_TOKEN}

# 播放器配置
player:
  backend: ffpyplayer  # ffpyplayer / mpv / platform
  volume: 80

# 记忆存储配置
memory:
  db_path: ~/.jiuge/memory.db
  auto_backup: true
  backup_interval: 86400  # 每天备份

# Agent 配置
agent:
  default_platform: netease
  search_priority:
    - netease
    - spotify
    - qqmusic
  language: zh-CN
```

---

## 4. 部署架构

### 4.1 单机部署

```
┌─────────────────────────────────────────┐
│              Host Machine               │
│  ┌───────────────────────────────────┐  │
│  │         OpenClaw Gateway          │  │
│  └───────────────────────────────────┘  │
│                   │                      │
│  ┌───────────────────────────────────┐  │
│  │         Jiuge Agent               │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │ Unified Music Service       │  │  │
│  │  ├─────────────────────────────┤  │  │
│  │  │ Platform Adapters           │  │  │
│  │  ├─────────────────────────────┤  │  │
│  │  │ Local Player                │  │  │
│  │  ├─────────────────────────────┤  │  │
│  │  │ Memory Store (SQLite)       │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 4.2 分布式部署（可选）

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Gateway   │────▶│  Jiuge API  │────▶│   Redis     │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  Spotify  │   │  Netease  │   │   Apple   │
    │  Adapter  │   │  Adapter  │   │  Adapter  │
    └───────────┘   └───────────┘   └───────────┘
```

---

## 5. 扩展点

### 5.1 添加新平台

1. 继承 `MusicPlatformAdapter`
2. 实现所有抽象方法
3. 在配置中添加凭据
4. 在 `UnifiedMusicService` 中注册

### 5.2 添加新指令

1. 在 `CommandParser.PATTERNS` 中添加正则
2. 在 `UnifiedMusicService` 中实现方法
3. 在 Agent 中添加路由

### 5.3 添加新渠道

通过 OpenClaw 的 channel 机制自动支持，只需确保消息格式一致。

---

## 6. 安全考虑

- API 凭据存储在环境变量或加密配置中
- OAuth token 定期刷新
- 用户数据本地存储，不上传云端
- 敏感操作需要确认
