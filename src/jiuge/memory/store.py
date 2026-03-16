"""
音乐记忆存储
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class MusicMemoryStore:
    """音乐记忆存储"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path.home() / ".jiuge" / "memory.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, platform_id)
                );
                
                CREATE TABLE IF NOT EXISTS play_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id TEXT,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    FOREIGN KEY (track_id) REFERENCES tracks(id)
                );
                
                CREATE TABLE IF NOT EXISTS favorites (
                    track_id TEXT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (track_id) REFERENCES tracks(id)
                );
                
                CREATE TABLE IF NOT EXISTS playlists (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    platform TEXT,
                    track_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_play_history_played_at 
                ON play_history(played_at);
            """)
    
    def save_track(self, track: dict):
        """保存歌曲信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tracks 
                (id, platform, platform_id, title, artists, album, duration, cover_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                track["id"],
                track.get("platform"),
                track.get("platform_id"),
                track.get("title"),
                json.dumps(track.get("artists", []), ensure_ascii=False),
                track.get("album"),
                track.get("duration"),
                track.get("cover_url")
            ))
    
    def record_play(self, track: dict, source: str = "unknown"):
        """记录播放"""
        self.save_track(track)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO play_history (track_id, source)
                VALUES (?, ?)
            """, (track["id"], source))
    
    def add_favorite(self, track: dict):
        """添加收藏"""
        self.save_track(track)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO favorites (track_id)
                VALUES (?)
            """, (track["id"],))
    
    def remove_favorite(self, track_id: str):
        """移除收藏"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM favorites WHERE track_id = ?", (track_id,))
    
    def get_favorites(self, limit: int = 100) -> List[dict]:
        """获取收藏列表"""
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
    
    def get_stats(self, period: str = "week") -> dict:
        """获取统计"""
        days = {"day": 1, "week": 7, "month": 30, "year": 365}.get(period, 7)
        since = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 总播放次数
            total = conn.execute("""
                SELECT COUNT(*) as count FROM play_history
                WHERE played_at >= ?
            """, (since.isoformat(),)).fetchone()["count"]
            
            # 独立歌曲数
            unique = conn.execute("""
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
                "total_plays": total,
                "unique_tracks": unique,
                "top_tracks": [self._row_to_track(t) for t in top_tracks],
                "top_artists": [
                    {"artist": r["artist"], "plays": r["play_count"]}
                    for r in top_artists if r["artist"]
                ]
            }
    
    def _row_to_track(self, row: sqlite3.Row) -> dict:
        """转换行到歌曲"""
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
        """导出数据"""
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
        """导入数据"""
        with sqlite3.connect(self.db_path) as conn:
            for track in data.get("tracks", []):
                conn.execute("""
                    INSERT OR REPLACE INTO tracks 
                    (id, platform, platform_id, title, artists, album, duration, cover_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    track["id"], track.get("platform"), track.get("platform_id"),
                    track["title"], track.get("artists"), track.get("album"),
                    track.get("duration"), track.get("cover_url")
                ))
            
            for record in data.get("history", []):
                conn.execute("""
                    INSERT INTO play_history (track_id, played_at, source)
                    VALUES (?, ?, ?)
                """, (record["track_id"], record.get("played_at"), record.get("source")))
            
            for fav in data.get("favorites", []):
                conn.execute("""
                    INSERT OR REPLACE INTO favorites (track_id, added_at)
                    VALUES (?, ?)
                """, (fav["track_id"], fav.get("added_at")))
