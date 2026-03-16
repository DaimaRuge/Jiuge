"""
同步服务单元测试
"""

import pytest
import tempfile
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jiuge.sync import (
    PlaylistSyncService, SyncStatus, MatchMethod,
    SyncTask, TrackMatch
)
from jiuge.adapters.base import Track


class TestSyncStatus:
    """同步状态枚举测试"""

    def test_status_values(self):
        """测试状态值"""
        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.SYNCING.value == "syncing"
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.FAILED.value == "failed"
        assert SyncStatus.CONFLICT.value == "conflict"


class TestMatchMethod:
    """匹配方式枚举测试"""

    def test_method_values(self):
        """测试匹配方式值"""
        assert MatchMethod.ISRC.value == "isrc"
        assert MatchMethod.TITLE_ARTIST.value == "title_artist"
        assert MatchMethod.MANUAL.value == "manual"


class TestSyncTask:
    """同步任务数据类测试"""

    def test_task_creation(self):
        """测试创建同步任务"""
        task = SyncTask(
            id="netease:123->spotify",
            source_platform="netease",
            source_playlist_id="123",
            target_platform="spotify",
            target_playlist_id=None
        )

        assert task.id == "netease:123->spotify"
        assert task.source_platform == "netease"
        assert task.status == SyncStatus.PENDING
        assert task.total_tracks == 0


class TestTrackMatch:
    """歌曲匹配结果测试"""

    def test_match_creation(self):
        """测试创建匹配结果"""
        source = Track(
            id="netease:123",
            platform="netease",
            platform_id="123",
            title="测试歌曲",
            artists=["歌手A"]
        )

        target = Track(
            id="spotify:456",
            platform="spotify",
            platform_id="456",
            title="Test Song",
            artists=["Artist A"]
        )

        match = TrackMatch(
            source_track=source,
            target_track=target,
            match_method=MatchMethod.TITLE_ARTIST,
            confidence=0.85,
            is_matched=True
        )

        assert match.is_matched
        assert match.confidence == 0.85
        assert match.match_method == MatchMethod.TITLE_ARTIST


class TestPlaylistSyncService:
    """歌单同步服务测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        os.unlink(f.name)

    def test_service_creation(self, temp_db):
        """测试创建服务"""
        service = PlaylistSyncService(db_path=temp_db)

        assert service.db_path == temp_db

    @pytest.mark.asyncio
    async def test_create_sync_task(self, temp_db):
        """测试创建同步任务"""
        service = PlaylistSyncService(db_path=temp_db)

        task = await service.create_sync_task(
            source_platform="netease",
            source_playlist_id="123456",
            target_platform="spotify"
        )

        assert task.id == "netease:123456->spotify"
        assert task.source_platform == "netease"
        assert task.target_platform == "spotify"
        assert task.status == SyncStatus.PENDING

    def test_get_task(self, temp_db):
        """测试获取任务"""
        service = PlaylistSyncService(db_path=temp_db)

        # 获取不存在的任务
        task = service.get_task("nonexistent")
        assert task is None

    def test_get_pending_tasks(self, temp_db):
        """测试获取待处理任务"""
        service = PlaylistSyncService(db_path=temp_db)

        tasks = service.get_pending_tasks()
        assert isinstance(tasks, list)

    def test_get_sync_stats(self, temp_db):
        """测试获取同步统计"""
        service = PlaylistSyncService(db_path=temp_db)

        stats = service.get_sync_stats()

        assert "task_stats" in stats
        assert "total_mappings" in stats
        assert "recent_syncs" in stats

    def test_calculate_similarity(self, temp_db):
        """测试相似度计算"""
        service = PlaylistSyncService(db_path=temp_db)

        source = Track(
            id="netease:1",
            platform="netease",
            platform_id="1",
            title="测试歌曲",
            artists=["歌手A", "歌手B"],
            album="测试专辑"
        )

        # 完全匹配
        target1 = Track(
            id="netease:2",
            platform="netease",
            platform_id="2",
            title="测试歌曲",
            artists=["歌手A"],
            album="测试专辑"
        )
        score1 = service._calculate_similarity(source, target1)
        assert score1 >= 0.7

        # 完全不匹配
        target2 = Track(
            id="netease:3",
            platform="netease",
            platform_id="3",
            title="完全不相关的歌曲",
            artists=["其他歌手"],
            album="其他专辑"
        )
        score2 = service._calculate_similarity(source, target2)
        assert score2 < 0.5

    def test_string_similarity(self, temp_db):
        """测试字符串相似度"""
        service = PlaylistSyncService(db_path=temp_db)

        # 完全相同
        assert service._string_similarity("hello", "hello") == 1.0

        # 完全不同
        assert service._string_similarity("hello", "world") < 0.5

        # 部分相同
        sim = service._string_similarity("hello world", "hello there")
        assert 0.5 < sim < 1.0
