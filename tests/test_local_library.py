"""
本地音乐库单元测试
"""

import pytest
import tempfile
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jiuge.local_library import (
    LocalLibrary, LocalTrack, ScanResult, SUPPORTED_FORMATS
)


class TestLocalTrack:
    """本地歌曲数据类测试"""

    def test_track_creation(self):
        """测试创建本地歌曲"""
        track = LocalTrack(
            id="abc123",
            file_path="/music/song.mp3",
            title="测试歌曲",
            artists=["歌手A", "歌手B"],
            album="测试专辑",
            year=2024,
            duration=240,
            bitrate=320,
            file_size=10240000,
            file_format="mp3"
        )

        assert track.id == "abc123"
        assert track.file_path == "/music/song.mp3"
        assert track.title == "测试歌曲"
        assert track.year == 2024
        assert track.file_format == "mp3"

    def test_to_track(self):
        """测试转换为通用 Track"""
        local_track = LocalTrack(
            id="xyz",
            file_path="/music/test.flac",
            title="Test Song",
            artists=["Artist"],
            album="Album",
            duration=180,
            isrc="USXXX1234567"
        )

        track = local_track.to_track()

        assert track.id == "local:xyz"
        assert track.platform == "local"
        assert track.title == "Test Song"
        assert track.isrc == "USXXX1234567"

    def test_to_dict(self):
        """测试转换为字典"""
        track = LocalTrack(
            id="test",
            file_path="/path/to/file.mp3",
            title="Song",
            artists=["Artist"],
            duration=200
        )

        data = track.to_dict()

        assert data["id"] == "test"
        assert data["file_path"] == "/path/to/file.mp3"
        assert data["duration"] == 200


class TestScanResult:
    """扫描结果测试"""

    def test_result_creation(self):
        """测试创建扫描结果"""
        result = ScanResult(
            total_files=100,
            new_files=80,
            updated_files=10,
            failed_files=10,
            total_size=1024000000,
            duration=5.5,
            errors=["错误1", "错误2"]
        )

        assert result.total_files == 100
        assert result.new_files == 80
        assert result.failed_files == 10
        assert len(result.errors) == 2


class TestSupportedFormats:
    """支持格式测试"""

    def test_supported_formats(self):
        """测试支持的音频格式"""
        assert ".mp3" in SUPPORTED_FORMATS
        assert ".flac" in SUPPORTED_FORMATS
        assert ".m4a" in SUPPORTED_FORMATS
        assert ".aac" in SUPPORTED_FORMATS
        assert ".ogg" in SUPPORTED_FORMATS
        assert ".wav" in SUPPORTED_FORMATS

        # 不支持的格式
        assert ".txt" not in SUPPORTED_FORMATS
        assert ".pdf" not in SUPPORTED_FORMATS


class TestLocalLibrary:
    """本地音乐库测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def temp_music_dir(self):
        """创建临时音乐目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_library_creation(self, temp_db):
        """测试创建音乐库"""
        library = LocalLibrary(db_path=temp_db)

        assert library.db_path == temp_db

    def test_library_paths(self, temp_db):
        """测试音乐库路径管理"""
        library = LocalLibrary(
            db_path=temp_db,
            library_paths=["/music/pop", "/music/rock"]
        )

        assert len(library.library_paths) == 2

        # 添加路径
        library.add_library_path("/music/jazz")
        assert len(library.library_paths) == 3

        # 移除路径
        library.remove_library_path("/music/jazz")
        assert len(library.library_paths) == 2

    def test_get_stats_empty(self, temp_db):
        """测试获取空库统计"""
        library = LocalLibrary(db_path=temp_db)

        stats = library.get_stats()

        assert stats["total_tracks"] == 0
        assert stats["total_size"] == 0
        assert stats["total_duration"] == 0

    def test_get_albums_empty(self, temp_db):
        """测试获取空库专辑"""
        library = LocalLibrary(db_path=temp_db)

        albums = library.get_albums()

        assert isinstance(albums, list)
        assert len(albums) == 0

    def test_get_artists_empty(self, temp_db):
        """测试获取空库歌手"""
        library = LocalLibrary(db_path=temp_db)

        artists = library.get_artists()

        assert isinstance(artists, list)

    def test_save_track(self, temp_db):
        """测试保存歌曲"""
        library = LocalLibrary(db_path=temp_db)

        track = LocalTrack(
            id="test123",
            file_path="/music/test.mp3",
            title="测试歌曲",
            artists=["歌手A"],
            album="测试专辑",
            duration=200,
            file_size=5000000,
            file_format="mp3"
        )

        library._save_track(track)

        # 验证保存
        saved = library.get_track_by_id("test123")
        assert saved is not None
        assert saved.title == "测试歌曲"

    def test_delete_track(self, temp_db):
        """测试删除歌曲"""
        library = LocalLibrary(db_path=temp_db)

        # 先保存
        track = LocalTrack(
            id="delete_me",
            file_path="/music/delete.mp3",
            title="要删除的歌曲",
            artists=["歌手"],
            duration=180
        )
        library._save_track(track)

        # 删除
        result = library.delete_track("delete_me")
        assert result

        # 验证删除
        deleted = library.get_track_by_id("delete_me")
        assert deleted is None

    def test_search_tracks(self, temp_db):
        """测试搜索歌曲"""
        library = LocalLibrary(db_path=temp_db)

        # 添加几首歌
        tracks = [
            LocalTrack(id="1", file_path="/a.mp3", title="流行歌曲", artists=["歌手A"], album="专辑A"),
            LocalTrack(id="2", file_path="/b.mp3", title="摇滚歌曲", artists=["歌手B"], album="专辑B"),
            LocalTrack(id="3", file_path="/c.mp3", title="流行乐", artists=["歌手C"], album="专辑C"),
        ]

        for t in tracks:
            library._save_track(t)

        # 搜索
        results = library.search_tracks("流行")
        assert len(results) >= 2

    def test_collect_audio_files(self, temp_db, temp_music_dir):
        """测试收集音频文件"""
        library = LocalLibrary(db_path=temp_db)

        # 创建一些测试文件
        open(os.path.join(temp_music_dir, "song1.mp3"), 'w').close()
        open(os.path.join(temp_music_dir, "song2.flac"), 'w').close()
        open(os.path.join(temp_music_dir, "song3.m4a"), 'w').close()
        open(os.path.join(temp_music_dir, "readme.txt"), 'w').close()  # 非音频文件

        files = library._collect_audio_files(temp_music_dir)

        # 应该只收集音频文件
        assert len(files) == 3
        assert all(any(f.endswith(ext) for ext in SUPPORTED_FORMATS) for f in files)
