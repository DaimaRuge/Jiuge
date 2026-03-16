"""
Web API 集成测试
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jiuge.api import app, create_app


class TestAPIBasics:
    """API 基础测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestPlaybackAPI:
    """播放控制 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_get_status(self, client):
        """测试获取状态"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data

    def test_search_tracks(self, client):
        """测试搜索歌曲"""
        response = client.post(
            "/search",
            json={"query": "测试歌曲", "limit": 10}
        )
        # 注意：实际测试可能需要模拟适配器
        assert response.status_code in [200, 503]

    def test_stop_playback(self, client):
        """测试停止播放"""
        response = client.post("/stop")
        assert response.status_code in [200, 503]

    def test_pause_playback(self, client):
        """测试暂停播放"""
        response = client.post("/pause")
        assert response.status_code in [200, 503]


class TestLibraryAPI:
    """本地音乐库 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_get_library_stats(self, client):
        """测试获取音乐库统计"""
        response = client.get("/library/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_tracks" in data

    def test_get_library_tracks(self, client):
        """测试获取歌曲列表"""
        response = client.get("/library/tracks")
        assert response.status_code == 200

    def test_search_library(self, client):
        """测试搜索本地歌曲"""
        response = client.get("/library/search?query=test")
        assert response.status_code == 200


class TestSyncAPI:
    """同步服务 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_get_sync_stats(self, client):
        """测试获取同步统计"""
        response = client.get("/sync/stats")
        assert response.status_code == 200
        data = response.json()
        assert "task_stats" in data

    def test_get_sync_task_not_found(self, client):
        """测试获取不存在的同步任务"""
        response = client.get("/sync/nonexistent_task")
        assert response.status_code == 404


class TestRecommendAPI:
    """推荐服务 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_get_recommendations(self, client):
        """测试获取推荐"""
        response = client.post(
            "/recommend",
            json={"limit": 10, "strategy": "hybrid"}
        )
        assert response.status_code == 200

    def test_get_similar_tracks(self, client):
        """测试获取相似歌曲"""
        response = client.get("/recommend/similar/netease:123?limit=10")
        assert response.status_code == 200


class TestCreateApp:
    """应用创建测试"""

    def test_create_app_default(self):
        """测试默认创建应用"""
        app = create_app()
        assert app is not None
        assert app.title == "Jiuge Music Agent API"

    def test_create_app_with_config(self):
        """测试带配置创建应用"""
        config = {
            "netease": {"enabled": True},
            "spotify": {"enabled": False},
            "library_paths": ["/music"]
        }
        app = create_app(config)
        assert app is not None
