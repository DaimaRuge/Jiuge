"""
Apple Music 适配器
基于 Apple Music API 和 MusicKit

Apple Music API 提供以下能力：
- 音乐搜索
- 歌曲播放（通过 MusicKit JS）
- 歌单管理
- 收藏管理
- 获取推荐

注意：需要在 https://developer.apple.com/documentation/applemusicapi 申请开发者权限
"""

from typing import List, Optional, Dict, Any
import logging
import time
import hashlib
import hmac
import base64
import json

from .base import MusicPlatformAdapter, Track, Playlist

logger = logging.getLogger(__name__)


class AppleMusicAdapter(MusicPlatformAdapter):
    """Apple Music 适配器"""

    # API 基础地址
    API_BASE = "https://api.music.apple.com/v1"

    def __init__(
        self,
        developer_token: str = None,
        user_token: str = None,
        key_id: str = None,
        team_id: str = None,
        private_key: str = None
    ):
        """
        初始化 Apple Music 适配器

        Args:
            developer_token: 开发者令牌（JWT），可直接提供或通过密钥生成
            user_token: 用户音乐令牌（通过 MusicKit 获取）
            key_id: Apple Music API 密钥 ID
            team_id: Apple 开发者团队 ID
            private_key: Apple Music API 私钥（.p8 文件内容）
        """
        self.developer_token = developer_token
        self.user_token = user_token
        self.key_id = key_id
        self.team_id = team_id
        self.private_key = private_key
        self._session = None
        self._authenticated = bool(developer_token)

        # 如果提供了密钥但没有令牌，自动生成
        if not developer_token and key_id and team_id and private_key:
            self.developer_token = self._generate_developer_token()

    @property
    def name(self) -> str:
        """平台名称"""
        return "apple"

    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return self._authenticated and bool(self.user_token)

    def _generate_developer_token(self) -> str:
        """
        生成开发者令牌（JWT）

        Returns:
            JWT 格式的开发者令牌
        """
        try:
            # JWT Header
            header = {
                "alg": "ES256",
                "kid": self.key_id
            }

            # JWT Payload
            payload = {
                "iss": self.team_id,
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600 * 24 * 180,  # 180 天有效期
            }

            # 编码 header 和 payload
            header_b64 = base64.urlsafe_b64encode(
                json.dumps(header).encode()
            ).rstrip(b'=').decode()
            payload_b64 = base64.urlsafe_b64encode(
                json.dumps(payload).encode()
            ).rstrip(b'=').decode()

            # 签名
            message = f"{header_b64}.{payload_b64}"
            signature = hmac.new(
                self.private_key.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()

            return f"{message}.{signature_b64}"

        except Exception as e:
            logger.error(f"生成开发者令牌失败: {e}")
            return None

    def _get_session(self):
        """获取 HTTP 会话（懒加载）"""
        if self._session is None:
            try:
                import aiohttp
                self._session = aiohttp.ClientSession()
            except ImportError:
                logger.error("请安装 aiohttp: pip install aiohttp")
                raise
        return self._session

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Authorization": f"Bearer {self.developer_token}",
            "Content-Type": "application/json"
        }
        if self.user_token:
            headers["Music-User-Token"] = self.user_token
        return headers

    async def authenticate(self) -> bool:
        """
        认证

        验证开发者令牌是否有效

        Returns:
            认证是否成功
        """
        if not self.developer_token:
            logger.warning("未配置 Apple Music 开发者令牌")
            return False

        try:
            session = self._get_session()

            # 验证令牌有效性（获取商店信息）
            async with session.get(
                f"{self.API_BASE}/storefronts",
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    self._authenticated = True
                    logger.info("Apple Music 认证成功")
                    return True
                elif resp.status == 401:
                    logger.error("Apple Music 开发者令牌无效")
                else:
                    logger.error(f"Apple Music 认证失败: {resp.status}")

        except Exception as e:
            logger.error(f"Apple Music 认证失败: {e}")

        return False

    async def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "track"
    ) -> List[Track]:
        """
        搜索歌曲

        Args:
            query: 搜索关键词
            limit: 返回数量限制
            search_type: 搜索类型 (track/album/artist/playlist)

        Returns:
            歌曲列表
        """
        # 搜索类型映射
        type_map = {
            "track": "songs",
            "album": "albums",
            "artist": "artists",
            "playlist": "playlists"
        }

        try:
            session = self._get_session()

            # 构建搜索参数
            params = {
                "term": query,
                "limit": limit,
                "types": type_map.get(search_type, "songs")
            }

            async with session.get(
                f"{self.API_BASE}/catalog/cn/search",
                params=params,
                headers=self._get_headers()
            ) as resp:
                if resp.status != 200:
                    logger.error(f"搜索请求失败: {resp.status}")
                    return []

                data = await resp.json()

            # 解析搜索结果
            tracks = []
            results = data.get("results", {})
            songs = results.get("songs", {}).get("data", [])

            for song in songs:
                attrs = song.get("attributes", {})

                # 解析歌手
                artists = []
                if "artistName" in attrs:
                    artists = [attrs["artistName"]]

                track = Track(
                    id=f"apple:{song['id']}",
                    platform="apple",
                    platform_id=song["id"],
                    title=attrs.get("name", ""),
                    artists=artists,
                    album=attrs.get("albumName", ""),
                    duration=attrs.get("durationInMillis", 0) // 1000,
                    cover_url=attrs.get("artwork", {}).get("url", "").replace(
                        "{w}", "300"
                    ).replace("{h}", "300"),
                    isrc=attrs.get("isrc")
                )
                tracks.append(track)

            return tracks

        except Exception as e:
            logger.error(f"Apple Music 搜索失败: {e}")
            return []

    async def get_track_url(self, track_id: str) -> Optional[str]:
        """
        获取歌曲播放地址

        Apple Music 不直接提供音频 URL，需要通过 MusicKit JS 播放

        Args:
            track_id: 歌曲 ID

        Returns:
            None（Apple Music 需要通过 MusicKit JS 播放）
        """
        # Apple Music 不提供直接的音频 URL
        # 需要通过 MusicKit JS 在前端播放
        return None

    async def get_track_info(self, track_id: str) -> Optional[Track]:
        """
        获取歌曲详情

        Args:
            track_id: 歌曲 ID

        Returns:
            歌曲信息，失败返回 None
        """
        try:
            # 去掉平台前缀
            if ":" in track_id:
                track_id = track_id.split(":")[1]

            session = self._get_session()

            async with session.get(
                f"{self.API_BASE}/catalog/cn/songs/{track_id}",
                headers=self._get_headers()
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()

            song = data.get("data", [{}])[0]
            attrs = song.get("attributes", {})

            return Track(
                id=f"apple:{song['id']}",
                platform="apple",
                platform_id=song["id"],
                title=attrs.get("name", ""),
                artists=[attrs.get("artistName", "")],
                album=attrs.get("albumName", ""),
                duration=attrs.get("durationInMillis", 0) // 1000,
                cover_url=attrs.get("artwork", {}).get("url", "").replace(
                    "{w}", "300"
                ).replace("{h}", "300"),
                isrc=attrs.get("isrc")
            )

        except Exception as e:
            logger.error(f"获取 Apple Music 歌曲详情失败: {e}")

        return None

    async def get_playlists(self) -> List[Playlist]:
        """
        获取用户歌单列表

        Returns:
            歌单列表
        """
        if not self.user_token:
            logger.warning("未配置用户令牌，无法获取歌单")
            return []

        try:
            session = self._get_session()

            async with session.get(
                f"{self.API_BASE}/me/library/playlists",
                headers=self._get_headers()
            ) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()

            playlists = []
            for item in data.get("data", []):
                attrs = item.get("attributes", {})
                playlists.append(Playlist(
                    id=f"apple:{item['id']}",
                    name=attrs.get("name", ""),
                    platform="apple",
                    description=attrs.get("description", {}).get("standard", ""),
                    track_count=len(item.get("relationships", {}).get("tracks", {}).get("data", [])),
                    cover_url=attrs.get("artwork", {}).get("url", "").replace(
                        "{w}", "300"
                    ).replace("{h}", "300")
                ))

            return playlists

        except Exception as e:
            logger.error(f"获取 Apple Music 歌单失败: {e}")
            return []

    async def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """
        获取歌单详情

        Args:
            playlist_id: 歌单 ID

        Returns:
            歌单详情，失败返回 None
        """
        try:
            # 去掉平台前缀
            if ":" in playlist_id:
                playlist_id = playlist_id.split(":")[1]

            session = self._get_session()

            async with session.get(
                f"{self.API_BASE}/catalog/cn/playlists/{playlist_id}",
                headers=self._get_headers()
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()

            item = data.get("data", [{}])[0]
            attrs = item.get("attributes", {})

            # 解析歌曲列表
            tracks = []
            track_data = item.get("relationships", {}).get("tracks", {}).get("data", [])
            for song in track_data:
                song_attrs = song.get("attributes", {})
                tracks.append(Track(
                    id=f"apple:{song['id']}",
                    platform="apple",
                    platform_id=song["id"],
                    title=song_attrs.get("name", ""),
                    artists=[song_attrs.get("artistName", "")],
                    album=song_attrs.get("albumName", ""),
                    duration=song_attrs.get("durationInMillis", 0) // 1000,
                    isrc=song_attrs.get("isrc")
                ))

            return Playlist(
                id=f"apple:{item['id']}",
                name=attrs.get("name", ""),
                platform="apple",
                description=attrs.get("description", {}).get("standard", ""),
                track_count=attrs.get("trackCount", 0),
                cover_url=attrs.get("artwork", {}).get("url", "").replace(
                    "{w}", "300"
                ).replace("{h}", "300"),
                tracks=tracks
            )

        except Exception as e:
            logger.error(f"获取 Apple Music 歌单详情失败: {e}")

        return None

    async def create_playlist(
        self,
        name: str,
        description: str = ""
    ) -> Optional[Playlist]:
        """
        创建歌单

        Args:
            name: 歌单名称
            description: 歌单描述

        Returns:
            创建的歌单信息，失败返回 None
        """
        if not self.user_token:
            logger.warning("未配置用户令牌，无法创建歌单")
            return None

        try:
            session = self._get_session()

            data = {
                "attributes": {
                    "name": name,
                    "description": description
                }
            }

            async with session.post(
                f"{self.API_BASE}/me/library/playlists",
                json=data,
                headers=self._get_headers()
            ) as resp:
                if resp.status != 201:
                    return None

                result = await resp.json()

            item = result.get("data", [{}])[0]
            return Playlist(
                id=f"apple:{item['id']}",
                name=name,
                platform="apple",
                description=description
            )

        except Exception as e:
            logger.error(f"创建 Apple Music 歌单失败: {e}")

        return None

    async def add_to_playlist(
        self,
        playlist_id: str,
        track_ids: List[str]
    ) -> bool:
        """
        添加歌曲到歌单

        Args:
            playlist_id: 歌单 ID
            track_ids: 歌曲 ID 列表

        Returns:
            是否成功
        """
        if not self.user_token:
            logger.warning("未配置用户令牌，无法添加歌曲")
            return False

        try:
            # 去掉平台前缀
            if ":" in playlist_id:
                playlist_id = playlist_id.split(":")[1]

            # 处理歌曲 ID
            clean_ids = []
            for tid in track_ids:
                if ":" in tid:
                    clean_ids.append(tid.split(":")[1])
                else:
                    clean_ids.append(tid)

            session = self._get_session()

            data = {
                "data": [{"id": tid, "type": "songs"} for tid in clean_ids]
            }

            async with session.post(
                f"{self.API_BASE}/me/library/playlists/{playlist_id}/tracks",
                json=data,
                headers=self._get_headers()
            ) as resp:
                return resp.status in (200, 201, 204)

        except Exception as e:
            logger.error(f"添加歌曲到 Apple Music 歌单失败: {e}")

        return False

    async def favorite(self, track_id: str) -> bool:
        """
        收藏歌曲

        Args:
            track_id: 歌曲 ID

        Returns:
            是否成功
        """
        if not self.user_token:
            logger.warning("未配置用户令牌，无法收藏歌曲")
            return False

        try:
            # 去掉平台前缀
            if ":" in track_id:
                track_id = track_id.split(":")[1]

            session = self._get_session()

            data = {
                "ids": [track_id],
                "type": "songs"
            }

            async with session.post(
                f"{self.API_BASE}/me/library",
                json=data,
                headers=self._get_headers()
            ) as resp:
                return resp.status in (200, 201, 204)

        except Exception as e:
            logger.error(f"收藏 Apple Music 歌曲失败: {e}")

        return False

    async def unfavorite(self, track_id: str) -> bool:
        """
        取消收藏

        Args:
            track_id: 歌曲 ID

        Returns:
            是否成功
        """
        if not self.user_token:
            return False

        try:
            # 去掉平台前缀
            if ":" in track_id:
                track_id = track_id.split(":")[1]

            session = self._get_session()

            async with session.delete(
                f"{self.API_BASE}/me/library/songs/{track_id}",
                headers=self._get_headers()
            ) as resp:
                return resp.status in (200, 204)

        except Exception as e:
            logger.error(f"取消 Apple Music 收藏失败: {e}")

        return False

    async def get_favorites(self, limit: int = 50) -> List[Track]:
        """
        获取收藏列表

        Args:
            limit: 返回数量限制

        Returns:
            收藏的歌曲列表
        """
        if not self.user_token:
            return []

        try:
            session = self._get_session()

            params = {"limit": limit}

            async with session.get(
                f"{self.API_BASE}/me/library/songs",
                params=params,
                headers=self._get_headers()
            ) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()

            tracks = []
            for song in data.get("data", []):
                attrs = song.get("attributes", {})
                tracks.append(Track(
                    id=f"apple:{song['id']}",
                    platform="apple",
                    platform_id=song["id"],
                    title=attrs.get("name", ""),
                    artists=[attrs.get("artistName", "")],
                    album=attrs.get("albumName", ""),
                    duration=attrs.get("durationInMillis", 0) // 1000,
                    isrc=attrs.get("isrc")
                ))

            return tracks

        except Exception as e:
            logger.error(f"获取 Apple Music 收藏列表失败: {e}")
            return []

    async def get_recommendations(self, limit: int = 10) -> List[Track]:
        """
        获取推荐歌曲

        Args:
            limit: 返回数量限制

        Returns:
            推荐歌曲列表
        """
        try:
            session = self._get_session()

            # 获取推荐歌单
            async with session.get(
                f"{self.API_BASE}/catalog/cn/recommendations",
                params={"limit": 1},
                headers=self._get_headers()
            ) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()

            # 从推荐歌单中提取歌曲
            tracks = []
            for recommendation in data.get("data", []):
                relationships = recommendation.get("relationships", {})

                # 尝试从内容中获取歌曲
                contents = relationships.get("contents", {}).get("data", [])
                for item in contents[:limit]:
                    if item.get("type") == "songs":
                        attrs = item.get("attributes", {})
                        tracks.append(Track(
                            id=f"apple:{item['id']}",
                            platform="apple",
                            platform_id=item["id"],
                            title=attrs.get("name", ""),
                            artists=[attrs.get("artistName", "")],
                            album=attrs.get("albumName", ""),
                            duration=attrs.get("durationInMillis", 0) // 1000,
                            cover_url=attrs.get("artwork", {}).get("url", "").replace(
                                "{w}", "300"
                            ).replace("{h}", "300")
                        ))

            return tracks[:limit]

        except Exception as e:
            logger.error(f"获取 Apple Music 推荐失败: {e}")
            return []

    async def get_radio_stations(self) -> List[Dict[str, Any]]:
        """
        获取广播电台列表

        Returns:
            电台列表
        """
        try:
            session = self._get_session()

            async with session.get(
                f"{self.API_BASE}/catalog/cn/radio-stations",
                headers=self._get_headers()
            ) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()

            stations = []
            for station in data.get("data", []):
                attrs = station.get("attributes", {})
                stations.append({
                    "id": station["id"],
                    "name": attrs.get("name", ""),
                    "url": attrs.get("url", ""),
                    "artwork": attrs.get("artwork", {}).get("url", "").replace(
                        "{w}", "300"
                    ).replace("{h}", "300")
                })

            return stations

        except Exception as e:
            logger.error(f"获取 Apple Music 电台失败: {e}")
            return []

    async def close(self):
        """关闭会话，释放资源"""
        if self._session:
            await self._session.close()
            self._session = None
