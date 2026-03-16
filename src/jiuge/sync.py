"""
跨平台歌单同步服务

提供以下功能：
- 跨平台歌单同步
- 歌曲匹配（基于 ISRC 或歌曲名+歌手）
- 同步状态跟踪
- 冲突解决
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sqlite3
import json
import logging
import asyncio
from enum import Enum

from .adapters.base import MusicPlatformAdapter, Track, Playlist

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """同步状态"""
    PENDING = "pending"       # 待同步
    SYNCING = "syncing"       # 同步中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CONFLICT = "conflict"     # 冲突


class MatchMethod(Enum):
    """匹配方式"""
    ISRC = "isrc"             # ISRC 匹配（最准确）
    TITLE_ARTIST = "title_artist"  # 歌名+歌手匹配
    MANUAL = "manual"         # 手动匹配


@dataclass
class SyncTask:
    """同步任务"""
    id: str
    source_platform: str
    source_playlist_id: str
    target_platform: str
    target_playlist_id: Optional[str]
    status: SyncStatus = SyncStatus.PENDING
    total_tracks: int = 0
    synced_tracks: int = 0
    failed_tracks: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: str = ""


@dataclass
class TrackMatch:
    """歌曲匹配结果"""
    source_track: Track
    target_track: Optional[Track]
    match_method: MatchMethod
    confidence: float  # 0.0 - 1.0
    is_matched: bool


class PlaylistSyncService:
    """歌单同步服务"""

    def __init__(self, db_path: str = None):
        """
        初始化同步服务

        Args:
            db_path: 数据库路径，默认 ~/.jiuge/sync.db
        """
        if db_path is None:
            db_path = Path.home() / ".jiuge" / "sync.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- 同步任务表
                CREATE TABLE IF NOT EXISTS sync_tasks (
                    id TEXT PRIMARY KEY,
                    source_platform TEXT NOT NULL,
                    source_playlist_id TEXT NOT NULL,
                    target_platform TEXT NOT NULL,
                    target_playlist_id TEXT,
                    status TEXT DEFAULT 'pending',
                    total_tracks INTEGER DEFAULT 0,
                    synced_tracks INTEGER DEFAULT 0,
                    failed_tracks INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                );

                -- 歌曲映射表（用于跨平台匹配）
                CREATE TABLE IF NOT EXISTS track_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_platform TEXT NOT NULL,
                    source_track_id TEXT NOT NULL,
                    target_platform TEXT NOT NULL,
                    target_track_id TEXT,
                    match_method TEXT,
                    confidence REAL,
                    is_verified BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_platform, source_track_id, target_platform)
                );

                -- 同步历史表
                CREATE TABLE IF NOT EXISTS sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    source_track_id TEXT NOT NULL,
                    target_track_id TEXT,
                    status TEXT,
                    error_message TEXT,
                    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES sync_tasks(id)
                );

                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_sync_tasks_status ON sync_tasks(status);
                CREATE INDEX IF NOT EXISTS idx_track_mappings_source ON track_mappings(source_platform, source_track_id);
                CREATE INDEX IF NOT EXISTS idx_sync_history_task ON sync_history(task_id);
            """)

    async def create_sync_task(
        self,
        source_platform: str,
        source_playlist_id: str,
        target_platform: str,
        target_playlist_name: str = None
    ) -> SyncTask:
        """
        创建同步任务

        Args:
            source_platform: 源平台
            source_playlist_id: 源歌单 ID
            target_platform: 目标平台
            target_playlist_name: 目标歌单名称（可选，用于创建新歌单）

        Returns:
            同步任务
        """
        task_id = f"{source_platform}:{source_playlist_id}->{target_platform}"

        task = SyncTask(
            id=task_id,
            source_platform=source_platform,
            source_playlist_id=source_playlist_id,
            target_platform=target_platform,
            target_playlist_id=None
        )

        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sync_tasks
                (id, source_platform, source_playlist_id, target_platform,
                 target_playlist_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id, task.source_platform, task.source_playlist_id,
                task.target_platform, task.target_playlist_id, task.status.value,
                task.created_at.isoformat(), task.updated_at.isoformat()
            ))

        return task

    async def execute_sync(
        self,
        task: SyncTask,
        adapters: Dict[str, MusicPlatformAdapter],
        create_playlist: bool = True,
        playlist_name: str = None
    ) -> SyncTask:
        """
        执行同步任务

        Args:
            task: 同步任务
            adapters: 平台适配器字典
            create_playlist: 是否创建目标歌单
            playlist_name: 目标歌单名称

        Returns:
            更新后的同步任务
        """
        task.status = SyncStatus.SYNCING
        task.updated_at = datetime.now()
        self._update_task(task)

        try:
            # 获取源平台适配器
            source_adapter = adapters.get(task.source_platform)
            if not source_adapter:
                raise ValueError(f"未找到源平台适配器: {task.source_platform}")

            # 获取目标平台适配器
            target_adapter = adapters.get(task.target_platform)
            if not target_adapter:
                raise ValueError(f"未找到目标平台适配器: {task.target_platform}")

            # 获取源歌单
            source_playlist = await source_adapter.get_playlist(task.source_playlist_id)
            if not source_playlist:
                raise ValueError(f"无法获取源歌单: {task.source_playlist_id}")

            task.total_tracks = len(source_playlist.tracks)

            # 创建或获取目标歌单
            if not task.target_playlist_id:
                if create_playlist:
                    name = playlist_name or f"[同步] {source_playlist.name}"
                    target_playlist = await target_adapter.create_playlist(
                        name, source_playlist.description
                    )
                    if target_playlist:
                        task.target_playlist_id = target_playlist.id
                else:
                    raise ValueError("未指定目标歌单")

            self._update_task(task)

            # 匹配并同步歌曲
            matched_ids = []
            for source_track in source_playlist.tracks:
                try:
                    # 尝试匹配目标平台歌曲
                    match = await self._match_track(
                        source_track, target_adapter
                    )

                    if match.is_matched and match.target_track:
                        matched_ids.append(match.target_track.platform_id)

                        # 保存映射关系
                        self._save_mapping(
                            source_track.platform,
                            source_track.platform_id,
                            task.target_platform,
                            match.target_track.platform_id,
                            match.match_method.value,
                            match.confidence
                        )

                        # 记录同步历史
                        self._record_sync_history(
                            task.id,
                            source_track.platform_id,
                            match.target_track.platform_id,
                            "success"
                        )

                        task.synced_tracks += 1
                    else:
                        # 记录失败
                        self._record_sync_history(
                            task.id,
                            source_track.platform_id,
                            None,
                            "failed",
                            "无法匹配歌曲"
                        )
                        task.failed_tracks += 1

                except Exception as e:
                    logger.error(f"同步歌曲失败: {source_track.title} - {e}")
                    task.failed_tracks += 1

                # 更新进度
                self._update_task(task)

            # 批量添加歌曲到目标歌单
            if matched_ids and task.target_playlist_id:
                # 分批添加（每次最多 50 首）
                batch_size = 50
                for i in range(0, len(matched_ids), batch_size):
                    batch = matched_ids[i:i + batch_size]
                    await target_adapter.add_to_playlist(
                        task.target_playlist_id, batch
                    )

            # 标记完成
            task.status = SyncStatus.COMPLETED
            task.updated_at = datetime.now()

        except Exception as e:
            task.status = SyncStatus.FAILED
            task.error_message = str(e)
            task.updated_at = datetime.now()
            logger.error(f"同步任务失败: {e}")

        self._update_task(task)
        return task

    async def _match_track(
        self,
        source_track: Track,
        target_adapter: MusicPlatformAdapter
    ) -> TrackMatch:
        """
        匹配歌曲到目标平台

        优先级：
        1. 使用缓存的映射
        2. ISRC 匹配（最准确）
        3. 歌名+歌手匹配

        Args:
            source_track: 源歌曲
            target_adapter: 目标平台适配器

        Returns:
            匹配结果
        """
        target_platform = target_adapter.name

        # 1. 检查缓存映射
        cached = self._get_cached_mapping(
            source_track.platform,
            source_track.platform_id,
            target_platform
        )
        if cached:
            target_track = await target_adapter.get_track_info(cached["target_track_id"])
            if target_track:
                return TrackMatch(
                    source_track=source_track,
                    target_track=target_track,
                    match_method=MatchMethod(cached["match_method"]),
                    confidence=cached["confidence"],
                    is_matched=True
                )

        # 2. ISRC 匹配
        if source_track.isrc:
            results = await target_adapter.search(
                f"isrc:{source_track.isrc}",
                limit=1
            )
            if results:
                return TrackMatch(
                    source_track=source_track,
                    target_track=results[0],
                    match_method=MatchMethod.ISRC,
                    confidence=1.0,
                    is_matched=True
                )

        # 3. 歌名+歌手匹配
        # 构建搜索查询
        artists_str = " ".join(source_track.artists)
        query = f"{source_track.title} {artists_str}"

        results = await target_adapter.search(query, limit=5)

        if results:
            # 计算相似度并选择最佳匹配
            best_match = None
            best_score = 0.0

            for candidate in results:
                score = self._calculate_similarity(source_track, candidate)
                if score > best_score:
                    best_score = score
                    best_match = candidate

            # 设定阈值
            if best_match and best_score >= 0.7:
                return TrackMatch(
                    source_track=source_track,
                    target_track=best_match,
                    match_method=MatchMethod.TITLE_ARTIST,
                    confidence=best_score,
                    is_matched=True
                )

        # 无匹配
        return TrackMatch(
            source_track=source_track,
            target_track=None,
            match_method=MatchMethod.TITLE_ARTIST,
            confidence=0.0,
            is_matched=False
        )

    def _calculate_similarity(self, source: Track, target: Track) -> float:
        """
        计算两首歌曲的相似度

        Args:
            source: 源歌曲
            target: 目标歌曲

        Returns:
            相似度分数 (0.0 - 1.0)
        """
        score = 0.0

        # 1. 歌名相似度（权重 0.5）
        title_sim = self._string_similarity(
            source.title.lower(),
            target.title.lower()
        )
        score += title_sim * 0.5

        # 2. 歌手相似度（权重 0.3）
        if source.artists and target.artists:
            # 检查是否有共同歌手
            source_artists = set(a.lower() for a in source.artists)
            target_artists = set(a.lower() for a in target.artists)
            common = source_artists & target_artists
            artist_sim = len(common) / max(len(source_artists), len(target_artists))
            score += artist_sim * 0.3

        # 3. 专辑相似度（权重 0.1）
        if source.album and target.album:
            album_sim = self._string_similarity(
                source.album.lower(),
                target.album.lower()
            )
            score += album_sim * 0.1

        # 4. 时长相似度（权重 0.1）
        if source.duration and target.duration:
            duration_diff = abs(source.duration - target.duration)
            duration_sim = max(0, 1 - duration_diff / 30)  # 30秒内差异
            score += duration_sim * 0.1

        return score

    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        计算字符串相似度（使用编辑距离）

        Args:
            s1: 字符串1
            s2: 字符串2

        Returns:
            相似度 (0.0 - 1.0)
        """
        if not s1 or not s2:
            return 0.0

        # 简单的 Levenshtein 距离实现
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(
                        dp[i - 1][j] + 1,
                        dp[i][j - 1] + 1,
                        dp[i - 1][j - 1] + 1
                    )

        distance = dp[m][n]
        max_len = max(m, n)
        return 1.0 - distance / max_len if max_len > 0 else 0.0

    def _get_cached_mapping(
        self,
        source_platform: str,
        source_track_id: str,
        target_platform: str
    ) -> Optional[Dict]:
        """获取缓存的映射"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM track_mappings
                WHERE source_platform = ?
                  AND source_track_id = ?
                  AND target_platform = ?
            """, (source_platform, source_track_id, target_platform))

            row = cursor.fetchone()
            return dict(row) if row else None

    def _save_mapping(
        self,
        source_platform: str,
        source_track_id: str,
        target_platform: str,
        target_track_id: str,
        match_method: str,
        confidence: float
    ):
        """保存映射关系"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO track_mappings
                (source_platform, source_track_id, target_platform,
                 target_track_id, match_method, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source_platform, source_track_id, target_platform,
                target_track_id, match_method, confidence
            ))

    def _record_sync_history(
        self,
        task_id: str,
        source_track_id: str,
        target_track_id: str,
        status: str,
        error_message: str = None
    ):
        """记录同步历史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sync_history
                (task_id, source_track_id, target_track_id, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (task_id, source_track_id, target_track_id, status, error_message))

    def _update_task(self, task: SyncTask):
        """更新任务状态"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sync_tasks SET
                    status = ?,
                    target_playlist_id = ?,
                    total_tracks = ?,
                    synced_tracks = ?,
                    failed_tracks = ?,
                    updated_at = ?,
                    error_message = ?
                WHERE id = ?
            """, (
                task.status.value, task.target_playlist_id,
                task.total_tracks, task.synced_tracks, task.failed_tracks,
                task.updated_at.isoformat(), task.error_message, task.id
            ))

    def get_task(self, task_id: str) -> Optional[SyncTask]:
        """获取任务详情"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM sync_tasks WHERE id = ?", (task_id,)
            )
            row = cursor.fetchone()

            if row:
                return SyncTask(
                    id=row["id"],
                    source_platform=row["source_platform"],
                    source_playlist_id=row["source_playlist_id"],
                    target_platform=row["target_platform"],
                    target_playlist_id=row["target_playlist_id"],
                    status=SyncStatus(row["status"]),
                    total_tracks=row["total_tracks"],
                    synced_tracks=row["synced_tracks"],
                    failed_tracks=row["failed_tracks"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    error_message=row["error_message"] or ""
                )

        return None

    def get_pending_tasks(self) -> List[SyncTask]:
        """获取待处理的任务"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM sync_tasks
                WHERE status IN ('pending', 'syncing')
                ORDER BY created_at ASC
            """)

            tasks = []
            for row in cursor.fetchall():
                tasks.append(SyncTask(
                    id=row["id"],
                    source_platform=row["source_platform"],
                    source_playlist_id=row["source_playlist_id"],
                    target_platform=row["target_platform"],
                    target_playlist_id=row["target_playlist_id"],
                    status=SyncStatus(row["status"]),
                    total_tracks=row["total_tracks"],
                    synced_tracks=row["synced_tracks"],
                    failed_tracks=row["failed_tracks"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    error_message=row["error_message"] or ""
                ))

            return tasks

    def get_sync_stats(self) -> Dict[str, Any]:
        """获取同步统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 任务统计
            task_stats = conn.execute("""
                SELECT
                    status,
                    COUNT(*) as count
                FROM sync_tasks
                GROUP BY status
            """).fetchall()

            # 映射统计
            mapping_count = conn.execute(
                "SELECT COUNT(*) as count FROM track_mappings"
            ).fetchone()["count"]

            # 最近同步
            recent = conn.execute("""
                SELECT * FROM sync_tasks
                WHERE status = 'completed'
                ORDER BY updated_at DESC
                LIMIT 5
            """).fetchall()

            return {
                "task_stats": {r["status"]: r["count"] for r in task_stats},
                "total_mappings": mapping_count,
                "recent_syncs": [dict(r) for r in recent]
            }

    async def manual_match(
        self,
        source_platform: str,
        source_track_id: str,
        target_platform: str,
        target_track_id: str
    ) -> bool:
        """
        手动设置映射关系

        Args:
            source_platform: 源平台
            source_track_id: 源歌曲 ID
            target_platform: 目标平台
            target_track_id: 目标歌曲 ID

        Returns:
            是否成功
        """
        try:
            self._save_mapping(
                source_platform,
                source_track_id,
                target_platform,
                target_track_id,
                MatchMethod.MANUAL.value,
                1.0
            )

            # 标记为已验证
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE track_mappings
                    SET is_verified = 1
                    WHERE source_platform = ?
                      AND source_track_id = ?
                      AND target_platform = ?
                """, (source_platform, source_track_id, target_platform))

            return True

        except Exception as e:
            logger.error(f"手动设置映射失败: {e}")
            return False
