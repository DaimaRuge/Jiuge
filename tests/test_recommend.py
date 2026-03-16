"""
推荐引擎单元测试
"""

import pytest
import tempfile
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jiuge.recommend import RecommendEngine, Recommendation
from jiuge.adapters.base import Track


class TestRecommendation:
    """推荐结果数据类测试"""

    def test_recommendation_creation(self):
        """测试创建推荐结果"""
        track = Track(
            id="netease:123",
            platform="netease",
            platform_id="123",
            title="推荐歌曲",
            artists=["歌手A"]
        )

        rec = Recommendation(
            track=track,
            score=0.85,
            reasons=["同歌手推荐", "热门歌曲"]
        )

        assert rec.track.title == "推荐歌曲"
        assert rec.score == 0.85
        assert len(rec.reasons) == 2


class TestRecommendEngine:
    """推荐引擎测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        os.unlink(f.name)

    def test_engine_creation(self, temp_db):
        """测试创建引擎"""
        engine = RecommendEngine(db_path=temp_db)

        assert engine.db_path == temp_db
        assert engine.decay_rate == 30

    def test_default_weights(self, temp_db):
        """测试默认权重"""
        engine = RecommendEngine(db_path=temp_db)

        assert "collaborative" in engine.weights
        assert "content" in engine.weights
        assert "popularity" in engine.weights
        assert "recency" in engine.weights

        # 权重总和应该接近 1
        total = sum(engine.weights.values())
        assert abs(total - 1.0) < 0.01

    def test_update_weights(self, temp_db):
        """测试更新权重"""
        engine = RecommendEngine(db_path=temp_db)

        # 有效更新
        engine.update_weights({
            "collaborative": 0.5,
            "content": 0.3,
            "popularity": 0.1,
            "recency": 0.1
        })

        assert engine.weights["collaborative"] == 0.5

        # 无效更新（总和不为1）应该被忽略
        engine.update_weights({
            "collaborative": 0.8,
            "content": 0.8
        })

        # 权重不应该改变
        assert engine.weights["collaborative"] == 0.5

    def test_set_decay_rate(self, temp_db):
        """测试设置衰减率"""
        engine = RecommendEngine(db_path=temp_db)

        engine.set_decay_rate(60)
        assert engine.decay_rate == 60

    def test_calculate_decay(self, temp_db):
        """测试时间衰减计算"""
        engine = RecommendEngine(db_path=temp_db)

        from datetime import datetime, timedelta

        # 最近播放
        recent = datetime.now() - timedelta(days=1)
        recent_decay = engine._calculate_decay(recent)
        assert recent_decay > 0.9

        # 一个月前
        month_ago = datetime.now() - timedelta(days=30)
        month_decay = engine._calculate_decay(month_ago)
        assert 0.4 < month_decay < 0.6

        # 很久以前
        long_ago = datetime.now() - timedelta(days=365)
        long_decay = engine._calculate_decay(long_ago)
        assert long_decay < 0.1

    @pytest.mark.asyncio
    async def test_get_recommendations_empty(self, temp_db):
        """测试空库推荐"""
        engine = RecommendEngine(db_path=temp_db)

        # 空数据库应该返回空列表
        recs = await engine.get_recommendations(limit=10)
        assert isinstance(recs, list)

    @pytest.mark.asyncio
    async def test_content_based_no_context(self, temp_db):
        """测试无上下文的内容推荐"""
        engine = RecommendEngine(db_path=temp_db)

        # 无上下文时应该使用协同过滤
        recs = await engine._content_based(limit=10, context=None)
        assert isinstance(recs, list)

    def test_row_to_track(self, temp_db):
        """测试数据库行转换"""
        engine = RecommendEngine(db_path=temp_db)

        import sqlite3

        # 创建模拟行
        with sqlite3.connect(temp_db) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_tracks (
                    id TEXT, platform TEXT, platform_id TEXT,
                    title TEXT, artists TEXT, album TEXT,
                    duration INTEGER, cover_url TEXT, isrc TEXT
                )
            """)
            conn.execute("""
                INSERT INTO test_tracks VALUES
                ('netease:1', 'netease', '1', '测试歌曲', '["歌手A"]', '测试专辑', 200, 'url', NULL)
            """)

            cursor = conn.execute("SELECT * FROM test_tracks")
            row = cursor.fetchone()

            track = engine._row_to_track(row)

            assert track is not None
            assert track.id == "netease:1"
            assert track.title == "测试歌曲"


class TestRecommendationStrategies:
    """推荐策略测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        os.unlink(f.name)

    @pytest.mark.asyncio
    async def test_hybrid_strategy(self, temp_db):
        """测试混合策略"""
        engine = RecommendEngine(db_path=temp_db)

        recs = await engine.get_recommendations(limit=10, strategy="hybrid")
        assert isinstance(recs, list)

    @pytest.mark.asyncio
    async def test_collaborative_strategy(self, temp_db):
        """测试协同过滤策略"""
        engine = RecommendEngine(db_path=temp_db)

        recs = await engine.get_recommendations(limit=10, strategy="collaborative")
        assert isinstance(recs, list)

    @pytest.mark.asyncio
    async def test_content_strategy(self, temp_db):
        """测试基于内容策略"""
        engine = RecommendEngine(db_path=temp_db)

        recs = await engine.get_recommendations(limit=10, strategy="content")
        assert isinstance(recs, list)
