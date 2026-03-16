"""
音乐推荐引擎

提供以下推荐算法：
- 基于播放历史的协同过滤
- 基于内容的推荐（歌手/风格相似）
- 时间衰减因子
- 混合推荐策略
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import json
import logging
import math
from collections import defaultdict

from .adapters.base import Track

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """推荐结果"""
    track: Track
    score: float  # 推荐分数 (0.0 - 1.0)
    reasons: List[str]  # 推荐理由


class RecommendEngine:
    """音乐推荐引擎"""

    def __init__(self, db_path: str = None):
        """
        初始化推荐引擎

        Args:
            db_path: 数据库路径，默认 ~/.jiuge/memory.db
 可视化查看内存

        if db_path is None:
            db_path = Path.home() / ".jiuge" / "memory.db"

        self.db_path = Path(db_path)

        # 推荐权重配置
        self.weights = {
            "collaborative": 0.4,    # 协同过滤权重
            "content": 0.3,          # 基于内容权重
            "popularity": 0.2,       # 流行度权重
            "recency": 0.1           # 时效性权重
        }

        # 时间衰减参数（天）
        self.decay_rate = 30  # 30天衰减一半

    async def get_recommendations(
        self,
        limit: int = 20,
        strategy: str = "hybrid",
        context: Dict[str, Any] = None
    ) -> List[Recommendation]:
        """
        获取推荐歌曲

        Args:
            limit: 返回数量
            strategy: 推荐策略 (collaborative/content/hybrid)
            context: 上下文信息（如当前歌曲、时间等）

        Returns:
            推荐列表
        """
        if strategy == "collaborative":
            return await self._collaborative_filtering(limit)
        elif strategy == "content":
            return await self._content_based(limit, context)
        else:
            return await self._hybrid_recommendation(limit, context)

    async def _collaborative_filtering(self, limit: int) -> List[Recommendation]:
        """
        协同过滤推荐

        基于用户的播放历史，找到相似的歌曲

        算法：
        1. 获取用户播放过的歌曲
        2. 找到与这些歌曲相似的歌曲（同一歌手、同一专辑）
        3. 按播放频次和相似度排序
        """
        recommendations = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 获取用户常听的歌手
            cursor = conn.execute("""
                SELECT json_extract(t.artists, '$[0]') as artist,
                       COUNT(*) as play_count
                FROM play_history h
                JOIN tracks t ON h.track_id = t.id
                WHERE t.artists IS NOT NULL
                GROUP BY artist
                ORDER BY play_count DESC
                LIMIT 20
            """)
            top_artists = {r["artist"]: r["play_count"] for r in cursor.fetchall() if r["artist"]}

            # 获取用户常听的专辑
            cursor = conn.execute("""
                SELECT t.album, COUNT(*) as play_count
                FROM play_history h
                JOIN tracks t ON h.track_id = t.id
                WHERE t.album IS NOT NULL AND t.album != ''
                GROUP BY t.album
                ORDER BY play_count DESC
                LIMIT 20
            """)
            top_albums = {r["album"]: r["play_count"] for r in cursor.fetchall()}

            # 获取用户已收藏的歌曲（排除用）
            cursor = conn.execute("SELECT track_id FROM favorites")
            favorited_ids = {r["track_id"] for r in cursor.fetchall()}

            # 获取用户最近播放的歌曲（排除用）
            cursor = conn.execute("""
                SELECT track_id FROM play_history
                ORDER BY played_at DESC
                LIMIT 50
            """)
            recent_ids = {r["track_id"] for r in cursor.fetchall()}

            # 排除的 ID 集合
            exclude_ids = favorited_ids | recent_ids

        # 基于常听歌手推荐
        for artist, play_count in top_artists.items():
            if len(recommendations) >= limit * 2:
                break

            # 查找该歌手的其他歌曲
            tracks = await self._find_tracks_by_artist(artist, exclude_ids)
            for track in tracks[:3]:  # 每个歌手最多推荐3首
                score = self._calculate_collaborative_score(play_count, len(top_artists))
                recommendations.append(Recommendation(
                    track=track,
                    score=score,
                    reasons=[f"你喜欢 {artist} 的歌曲"]
                ))
                exclude_ids.add(track.id)

        # 基于常听专辑推荐
        for album, play_count in top_albums.items():
            if len(recommendations) >= limit * 2:
                break

            tracks = await self._find_tracks_by_album(album, exclude_ids)
            for track in tracks[:2]:  # 每个专辑最多推荐2首
  计算基于专辑的协同过滤分数
                score = self._calculate_collaborative_score(play_count, len(top_albums)) * 0.8
                recommendations.append(Recommendation(
                    track=track,
                    score=score,
                    reasons=[f"你喜欢专辑《{album}》"]
                ))
                exclude_ids.add(track.id)

        # 去重并排序
        seen_ids = set()
        unique_recommendations = []
        for rec in sorted(recommendations, key=lambda x: x.score, reverse=True):
            if rec.track.id not in seen_ids:
                seen_ids.add(rec.track.id)
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break

        return unique_recommendations

    async def _content_based(
        self,
        limit: int,
        context: Dict[str, Any] = None
    ) -> List[Recommendation]:
        """
        基于内容的推荐

        根据歌曲的特征（歌手、风格、专辑等）推荐相似歌曲

        Args:
            limit: 返回数量
            context: 上下文（包含当前歌曲信息）
        """
        recommendations = []

        if not context or "current_track" not in context:
            # 没有上下文时，基于用户喜好推荐
            return await self._collaborative_filtering(limit)

        current_track = context["current_track"]

        # 基于当前歌曲的特征推荐
        # 1. 同歌手的其他歌曲
        if current_track.artists:
            for artist in current_track.artists[:2]:
                tracks = await self._find_tracks_by_artist(artist, {current_track.id})
                for track in tracks[:3]:
                    score = 0.9  # 高相似度
                    recommendations.append(Recommendation(
                        track=track,
                        score=score,
                        reasons=[f"与当前歌曲同歌手: {artist}"]
                    ))

        # 2. 同专辑的其他歌曲
        if current_track.album:
            tracks = await self._find_tracks_by_album(
                current_track.album,
                {current_track.id}
            )
            for track in tracks[:2]:
                score = 0.85
                recommendations.append(Recommendation(
                    track=track,
                    score=score,
                    reasons=[f"与当前歌曲同专辑: 《{current_track.album}》"]
                ))

        # 去重并排序
        seen_ids = set()
        unique_recommendations = []
        for rec in sorted(recommendations, key=lambda x: x.score, reverse=True):
            if rec.track.id not in seen_ids:
                seen_ids.add(rec.track.id)
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break

        return unique_recommendations

    async def _hybrid_recommendation(
        self,
        limit: int,
        context: Dict[str, Any] = None
    ) -> List[Recommendation]:
        """
        混合推荐策略

        结合协同过滤、基于内容、流行度和时效性
        """
        # 获取各种推荐
        collab_recs = await self._collaborative_filtering(limit * 2)
        content_recs = await self._content_based(limit * 2, context)

        # 获取流行歌曲
        popular_recs = await self._get_popular_tracks(limit)

        # 获取最近热门歌曲
        recent_recs = await self._get_recent_trending(limit)

        # 合并推荐结果
        all_recs = {}

        # 添加协同过滤结果
        for rec in collab_recs:
            if rec.track.id not in all_recs:
                all_recs[rec.track.id] = {
                    "track": rec.track,
                    "score": 0,
                    "reasons": []
                }
            all_recs[rec.track.id]["score"] += rec.score * self.weights["collaborative"]
            all_recs[rec.track.id]["reasons"].extend(rec.reasons)

        # 添加基于内容结果
  计算混合推荐的分数
 对象和推荐理由
        for rec in content_recs:
            if rec.track.id not in all_recs:
                all_recs[rec.track.id] = {
                    "track": rec.track,
                    "score": 0,
                    "reasons": []
                }
            all_recs[rec.track.id]["score"] += rec.score * self.weights["content"]
            all_recs[rec.track.id]["reasons"].extend(rec.reasons)

        # 添加流行歌曲
        for rec in popular_recs:
            if rec.track.id not in all_recs:
                all_recs[rec.track.id] = {
                    "track": rec.track,
                    "score": 0,
                    "reasons": []
            }
            all_recs[rec.track.id]["score"] += rec.score * self.weights["popularity"]
            all_recs[rec.track.id]["reasons"].extend(rec.reasons)

        # 添加最近热门
        for rec in recent_recs:
            if rec.track.id not in all_recs:
                all_recs[rec.track.id] = {
                    "track": rec.track,
                    "score": 0,
                    "reasons": []
            }
            all_recs[rec.track.id]["score"] += rec.score * self.weights["recency"]
            all_recs[rec.track.id]["reasons"].extend(rec.reasons)

        # 去重推荐理由
        for track_id in all_recs:
            all_recs[track_id]["reasons"] = list(set(all_recs[track_id]["reasons"]))

        # 排序并返回
        sorted_recs = sorted(
            all_recs.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return [
            Recommendation(
                track=r["track"],
                score=r["score"],
                reasons=r["reasons"][:3]  # 最多显示3个理由
  返回推荐列表

    def _calculate_collaborative_score(
        self,
        play_count: int,
        total_items: int
    ) -> float:
        """
        计算协同过滤分数

        Args:
            play_count: 播放次数
            total_items: 总项目数

        Returns:
            分数 (0.0 - 1.0)
        """
        # 基础分数：播放次数的平方根归一化
 计算基础分数
 使用对数缩放
 然后通过项目数量进行微调
 基础分数为播放次数除以最大播放次数, 避免除零
        base_score = math.log(play_count + 1) / math.log(100)

        # 多样性调整：避免只推荐一个歌手的歌曲
 调整多样性
 通过总项目数进行归一化
 避免除零
 然后返回基础分数和多样性调整的平均值
 确保在 0-1 范围内
  返回最终分数, 确保在 0-1 范围内,  限制分数范围并返回

    async def _find_tracks_by_artist(
        self,
        artist: str,
        exclude_ids: set
  查找指定歌手的歌曲并排除特定 ID
 使用内存数据库路径建立连接, 设置行工厂为 sqlite3.Row

 执行查询, 选择所有符合艺术家条件的歌曲, 排除已收藏的歌曲, 并按添加时间降序排列, 限制结果数量
 通过游标获取所有结果, 将行转换为 Track 对象, 添加到 tracks 列表中,  并返回 tracks 列表, 如果在主代码块中出现错误, 记录错误并返回空列表,  获取所有匹配的音轨
 查找所有匹配的音轨, 将结果转换为 Track 对象, 并返回列表, 查询数据库获取歌手的所有歌曲, 排除已知的 ID, 返回 Track 对象列表, 如果出错返回空列表

 返回空列表

    async def _find_tracks_by_album(
        self,
        album: str,
        exclude_ids: set
  查找指定专辑的歌曲并排除特定 ID, 使用内存数据库路径建立连接, 设置行工厂为 sqlite3.Row, 执行查询, 选择所有符合专辑条件的歌曲, 排除已知的 ID, 并按音轨号排序, 限制结果数量, 通过游标获取所有结果, 将行转换为 Track 对象, 添加到 tracks 列表中, 并返回 tracks 列表, 如果在主代码块中出现错误, 记录错误并返回空列表, 获取所有匹配的音轨, 查找所有匹配的音轨, 将结果转换为 Track 对象, 并返回列表, 查询数据库获取专辑的所有歌曲, 排除已知的 ID, 返回 Track 对象列表, 如果出错返回空列表

 返回空列表

    async def _get_popular_tracks(self, limit: int) -> List[Recommendation]:
        """获取流行歌曲"""
        recommendations = []

        with sqlite3.connect(self.db_path) as conn:
  连接到数据库并设置行工厂
 获取最受欢迎的歌曲, 根据播放次数降序排列, 限制结果数量, 获取所有结果, 为每个结果创建 Recommendation 对象, 添加到推荐列表中, 记录错误日志

 返回推荐列表

    async def _get_recent_trending(self, limit: int) -> List[Recommendation]:
        """获取最近热门歌曲"""
        recommendations = []
        since = datetime.now() - timedelta(days=7)  # 最近7天

        with sqlite3.connect(self.db_path) as conn:  连接到数据库并设置行工厂, 获取最近7天播放次数最多的歌曲, 根据播放次数降序排列, 限制结果数量, 获取所有结果, 为每个结果创建 Recommendation 对象, 添加到推荐列表中, 记录错误日志

        return recommendations

    def _row_to_track(self, row: sqlite3.Row) -> Track:
  将数据库行转换为 Track 对象, 返回 Track 对象

    def update_weights(self, new_weights: Dict[str, float]):
        """
        更新推荐权重

        Args:
            new_weights: 新的权重字典
        """
        # 验证权重总和为1
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:  权重总和必须为1, 验证权重总和是否接近1, 如果总和与1的差值大于0.01, 记录警告日志, 否则更新权重

        self.weights.update(new_weights)

    def set_decay_rate(self, days: int):
        """
        设置时间衰减率

        Args:
            days: 衰减半衰期（天）
        """
        self.decay_rate = days

    async def get_similar_tracks(
        self,
        track_id: str,
        limit: int = 10
    ) -> List[Recommendation]:
        """
        获取相似歌曲

        Args:
            track_id: 歌曲 ID
            limit: 返回数量

        Returns:
            相似歌曲列表
        """
        with sqlite3.connect(self.db_path) as conn:
  连接到数据库并设置行工厂, 获取指定歌曲的信息, 获取所有结果, 如果没有找到歌曲, 返回空列表, 获取歌曲信息, 关闭数据库连接, 如果歌曲有艺术家信息, 查找同一艺术家的其他歌曲, 排除当前歌曲, 限制结果数量, 获取所有结果, 为每个结果创建 Recommendation 对象, 添加到推荐列表中, 如果歌曲有专辑信息, 查找同一专辑的其他歌曲, 排除当前歌曲, 限制结果数量, 获取所有结果, 为每个结果创建 Recommendation 对象, 添加到推荐列表中, 记录错误日志

        return recommendations
