"""
适配器单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jiuge.adapters.base import Track, Playlist, MusicPlatformAdapter
from jiuge.adapters.apple import AppleMusicAdapter


class TestTrack:
    """Track 数据类测试"""

    def test_track_creation(self):
        """测试创建 Track 对象"""
        track = Track(
            id="netease:123",
            platform="netease",
            platform_id="123",
            title="测试歌曲",
            artists=["歌手A", "歌手B"],
            album="测试专辑",
            duration=240,
            cover_url="https://example.com/cover.jpg",
            isrc="CNXXX1234567"
        )

        assert track.id == "netease:123"
        assert track.platform == "netease"
        assert track.title == "测试歌曲"
        assert len(track.artists) == 2
        assert track.duration == 240
        assert track.isrc == "CNXXX1234567"

    def test_track_to_dict(self):
        """测试转换为字典"""
        track = Track(
            id="spotify:abc",
            platform="spotify",
            platform_id="abc",
            title="Test Song",
            artists=["Artist"]
        )

        data = track.to_dict()

        assert data["id"] == "spotify:abc"
        assert data["platform"] == "spotify"
        assert data["title"] == "Test Song"
        assert data["artists"] == ["Artist"]


class TestPlaylist:
    """Playlist 数据类测试"""

    def test_playlist_creation(self):
        """测试创建 Playlist 对象"""
        playlist = Playlist(
            id="netease:pl123",
            name="测试歌单",
            platform="netease",
            description="这是一个测试歌单",
            track_count=10
        )

        assert playlist.id == "netease:pl123"
        assert playlist.name == "测试歌单"
        assert playlist.track_count == 10


class TestAppleMusicAdapter:
    """Apple Music 适配器测试"""

    def test_adapter_creation(self):
        """测试创建适配器"""
        adapter = AppleMusicAdapter(developer_token="test_token")

        assert adapter.name == "apple"
        assert adapter.developer_token == "test_token"

    def test_adapter_with_key_generation(self):
        """测试使用密钥生成令牌"""
        adapter = AppleMusicAdapter(
            key_id="ABC123",
            team_id="TEAM123",
            private_key="test_private_key"
        )

        assert adapter.key_id == "ABC123"
        assert adapter.team_id == "TEAM123"

    @pytest.mark.asyncio
    async def test_search_mock(self):
        """测试搜索功能（模拟）"""
        adapter = AppleMusicAdapter(developer_token="test_token")

        # 模拟 HTTP 响应
        with patch.object(adapter, '_get_session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "results": {
                    "songs": {
                        "data": [
                            {
                                "id": "12345",
                                "attributes": {
                                    "name": "测试歌曲",
                                    "artistName": "测试歌手",
                                    "albumName": "测试专辑",
                                    "durationInMillis": 240000,
                                    "artwork": {"url": "https://example.com/{w}x{h}.jpg"},
                                    "isrc": "CNXXX1234567"
                                }
                            }
                        ]
                    }
                }
            })

            mock_session.return_value.get = AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response)
            )

            # 注意：实际测试需要更复杂的模拟
            # 这里只是展示测试结构


class TestAdapterBase:
    """适配器基类测试"""

    def test_abstract_methods(self):
        """测试抽象方法定义"""
        # 确保基类不能直接实例化
        with pytest.raises(TypeError):
            MusicPlatformAdapter()
