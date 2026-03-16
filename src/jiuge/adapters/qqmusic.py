"""
QQ音乐适配器
基于QQ音乐开放平台 API

QQ 音乐开放平台提供以下能力：
- 音乐搜索
- 歌曲播放
- 歌单管理
- 云盘上传

注意：需要在 https://y.qq.com/mopen/ 申请开放平台权限
"""

from typing import List, Optional, Dict, Any
import logging
import hashlib
import time
import json

from .base import MusicPlatformAdapter, Track, Playlist

logger = logging.getLogger(__name__)


class QQMusicAdapter(MusicPlatformAdapter):
    """QQ音乐适配器"""

    # API 基础地址
    API_BASE = "https://c.y.qq.com"

    def __init__(
        self,
        app_id: str = None,
        app_secret: str = None,
        cookie: str = None
    ):
        """
        初始化 QQ 音乐适配器

        Args:
            app_id: QQ 音乐开放平台应用 ID
            app_secret: QQ 音乐开放平台应用密钥
            cookie: QQ 音乐登录 Cookie（用于获取更高音质）
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.cookie = cookie
        self._session = None
        self._authenticated = bool(cookie)

    @property
    def name(self) -> str:
        """平台名称"""
        return "qqmusic"

    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return self._authenticated

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

    def _sign_request(self, params: Dict[str, Any]) -> str:
        """
        生成请求签名

        Args:
            params: 请求参数

        Returns:
            签名字符串
        """
        if not self.app_secret:
            return ""

        # 按字母顺序排序参数
        sorted_params = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params)

        # 添加密钥并计算 MD5
        sign_str = param_str + self.app_secret
        return hashlib.md5(sign_str.encode()).hexdigest()

    async def authenticate(self) -> bool:
        """
        认证

        使用 Cookie 进行认证，验证 Cookie 是否有效

        Returns:
            认证是否成功
        """
        if not self.cookie:
            logger.warning("未配置 QQ 音乐 Cookie")
            return False

        try:
            # 验证 Cookie 有效性（通过获取用户信息）
            session = self._get_session()
            headers = {"Cookie": self.cookie}

            async with session.get(
                f"{self.API_BASE}/user/info",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("code") == 0:
                        self._authenticated = True
                        logger.info("QQ 音乐认证成功")
                        return True
        except Exception as e:
            logger.error(f"QQ 音乐认证失败: {e}")

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
            "track": 0,      # 单曲
            "album": 8,      # 专辑
            "artist": 9,     # 歌手
            "playlist": 15   # 歌单
        }

        try:
            session = self._get_session()

            # 构建 API 请求参数
            params = {
                "w": query,           # 搜索关键词
                "p": 1,               # 页码
                "n": limit,           # 每页数量
                "format": "json"      # 返回格式
            }

            headers = {}
            if self.cookie:
                headers["Cookie"] = self.cookie

            # 调用搜索 API
            async with session.get(
                f"{self.API_BASE}/soso/fcgi-bin/search_for_qq_cp",
                params=params,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    logger.error(f"搜索请求失败: {resp.status}")
                    return []

                data = await resp.json()

            # 解析搜索结果
            songs = data.get("data", {}).get("song", {}).get("list", [])

            tracks = []
            for song in songs:
                # 解析歌手列表
                artists = []
                if "singer" in song:
                    artists = [s.get("name", "") for s in song["singer"]]

                track = Track(
                    id=f"qqmusic:{song['mid']}",
                    platform="qqmusic",
                    platform_id=song["mid"],
                    title=song.get("name", ""),
                    artists=artists,
                    album=song.get("albumname", ""),
                    duration=song.get("interval", 0),
                    cover_url=f"https://y.qq.com/music/photo_new/T002R300x300M000{song.get('albummid', '')}.jpg"
                )
                tracks.append(track)

            return tracks

        except Exception as e:
            logger.error(f"QQ 音乐搜索失败: {e}")
            return []

    async def get_track_url(self, track_id: str) -> Optional[str]:
        """
        获取歌曲播放地址

        Args:
            track_id: 歌曲 ID（可以是 qqmusic:xxx 格式或纯 mid）

        Returns:
            播放地址 URL，失败返回 None
        """
        try:
            # 去掉平台前缀
            if ":" in track_id:
                track_id = track_id.split(":")[1]

            session = self._get_session()

            # 构建请求参数
            params = {
                "songmid": track_id,
                "format": "json"
            }

            headers = {}
            if self.cookie:
                headers["Cookie"] = self.cookie

            # 获取歌曲 URL
            async with session.get(
                f"{self.API_BASE}/v8/fcg-bin/fcg_play_single_song.fcg",
                params=params,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()

            # 解析返回的 URL
            url_data = data.get("data", [])
            if url_data:
                return url_data[0].get("url")

        except Exception as e:
            logger.error(f"获取 QQ 音乐播放地址失败: {e}")

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

            params = {
                "songmid": track_id,
                "format": "json"
            }

            headers = {}
            if self.cookie:
                headers["Cookie"] = self.cookie

            async with session.get(
                f"{self.API_BASE}/v8/fcg-bin/fcg_play_single_song.fcg",
                params=params,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()

            songs = data.get("data", [])
            if not songs:
                return None

            song = songs[0]
            artists = [s.get("name", "") for s in song.get("singer", [])]

            return Track(
                id=f"qqmusic:{song['mid']}",
                platform="qqmusic",
                platform_id=song["mid"],
                title=song.get("name", ""),
                artists=artists,
                album=song.get("album", {}).get("name", ""),
                duration=song.get("interval", 0),
                cover_url=f"https://y.qq.com/music/photo_new/T002R300x300M000{song.get('album', {}).get('mid', '')}.jpg"
            )

        except Exception as e:
            logger.error(f"获取 QQ 音乐歌曲详情失败: {e}")

        return None

    async def get_playlists(self) -> List[Playlist]:
        """
        获取用户歌单列表

        Returns:
            歌单列表
        """
        if not self._authenticated:
            logger.warning("未认证，无法获取歌单")
            return []

        try:
            session = self._get_session()
            headers = {"Cookie": self.cookie}

            async with session.get(
                f"{self.API_BASE}/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg",
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()

            playlists = []
            for item in data.get("data", {}).get("cdlist", []):
                playlists.append(Playlist(
                    id=f"qqmusic:{item['dissid']}",
                    name=item.get("dissname", ""),
                    platform="qqmusic",
                    description=item.get("desc", ""),
                    track_count=item.get("songnum", 0),
                    cover_url=item.get("logo", "")
                ))

            return playlists

        except Exception as e:
            logger.error(f"获取 QQ 音乐歌单失败: {e}")
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

            params = {
                "disstid": playlist_id,
                "format": "json"
            }

            headers = {}
            if self.cookie:
                headers["Cookie"] = self.cookie

            async with session.get(
                f"{self.API_BASE}/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg",
                params=params,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()

            cdlist = data.get("data", {}).get("cdlist", [])
            if not cdlist:
                return None

            playlist_info = cdlist[0]

            # 解析歌曲列表
            tracks = []
            for song in playlist_info.get("songlist", []):
                artists = [s.get("name", "") for s in song.get("singer", [])]
                tracks.append(Track(
                    id=f"qqmusic:{song['mid']}",
                    platform="qqmusic",
                    platform_id=song["mid"],
                    title=song.get("name", ""),
                    artists=artists,
                    album=song.get("albumname", ""),
                    duration=song.get("interval", 0)
                ))

            return Playlist(
                id=f"qqmusic:{playlist_id}",
                name=playlist_info.get("dissname", ""),
                platform="qqmusic",
                description=playlist_info.get("desc", ""),
                track_count=playlist_info.get("songnum", 0),
                cover_url=playlist_info.get("logo", ""),
                tracks=tracks
            )

        except Exception as e:
            logger.error(f"获取 QQ 音乐歌单详情失败: {e}")

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
        if not self._authenticated:
            logger.warning("未认证，无法创建歌单")
            return None

        try:
            session = self._get_session()
            headers = {
                "Cookie": self.cookie,
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {
                "name": name,
                "desc": description
            }

            async with session.post(
                f"{self.API_BASE}/qzone/fcg-bin/fcg_ucc_createcd.fcg",
                data=data,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return None

                result = await resp.json()

                if result.get("code") == 0:
                    return Playlist(
                        id=f"qqmusic:{result.get('dissid', '')}",
                        name=name,
                        platform="qqmusic",
                        description=description
                    )

        except Exception as e:
            logger.error(f"创建 QQ 音乐歌单失败: {e}")

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
        if not self._authenticated:
            logger.warning("未认证，无法添加歌曲")
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
            headers = {
                "Cookie": self.cookie,
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {
                "disstid": playlist_id,
                "songmids": ",".join(clean_ids)
            }

            async with session.post(
                f"{self.API_BASE}/qzone/fcg-bin/fcg_ucc_addsong_tocd.fcg",
                data=data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("code") == 0

        except Exception as e:
            logger.error(f"添加歌曲到 QQ 音乐歌单失败: {e}")

        return False

    async def favorite(self, track_id: str) -> bool:
        """
        收藏歌曲

        Args:
            track_id: 歌曲 ID

        Returns:
            是否成功
        """
        if not self._authenticated:
            logger.warning("未认证，无法收藏歌曲")
            return False

        try:
            # 去掉平台前缀
            if ":" in track_id:
                track_id = track_id.split(":")[1]

            session = self._get_session()
            headers = {
                "Cookie": self.cookie,
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {"songmid": track_id}

            async with session.post(
                f"{self.API_BASE}/qzone/fcg-bin/fcg_ucc_addsong_to_fav.fcg",
                data=data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("code") == 0

        except Exception as e:
            logger.error(f"收藏 QQ 音乐歌曲失败: {e}")

        return False

    async def unfavorite(self, track_id: str) -> bool:
        """
        取消收藏

        Args:
            track_id: 歌曲 ID

        Returns:
            是否成功
        """
        if not self._authenticated:
            return False

        try:
            # 去掉平台前缀
            if ":" in track_id:
                track_id = track_id.split(":")[1]

            session = self._get_session()
            headers = {
                "Cookie": self.cookie,
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {"songmid": track_id}

            async with session.post(
                f"{self.API_BASE}/qzone/fcg-bin/fcg_ucc_delsong_from_fav.fcg",
                data=data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("code") == 0

        except Exception as e:
            logger.error(f"取消 QQ 音乐收藏失败: {e}")

        return False

    async def get_favorites(self, limit: int = 50) -> List[Track]:
        """
        获取收藏列表

        Args:
            limit: 返回数量限制

        Returns:
            收藏的歌曲列表
        """
        if not self._authenticated:
            return []

        try:
            session = self._get_session()
            headers = {"Cookie": self.cookie}

            params = {
                "num": limit,
                "format": "json"
            }

            async with session.get(
                f"{self.API_BASE}/qzone/fcg-bin/fcg_ucc_getfavsong_info.fcg",
                params=params,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()

            tracks = []
            for song in data.get("data", {}).get("songlist", []):
                artists = [s.get("name", "") for s in song.get("singer", [])]
                tracks.append(Track(
                    id=f"qqmusic:{song['mid']}",
                    platform="qqmusic",
                    platform_id=song["mid"],
                    title=song.get("name", ""),
                    artists=artists,
                    album=song.get("albumname", ""),
                    duration=song.get("interval", 0)
                ))

            return tracks

        except Exception as e:
            logger.error(f"获取 QQ 音乐收藏列表失败: {e}")
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

            params = {
                "num": limit,
                "format": "json"
            }

            headers = {}
            if self.cookie:
                headers["Cookie"] = self.cookie

            async with session.get(
                f"{self.API_BASE}/v8/fcg-bin/fcg_first_yqq.fcg",
                params=params,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()

            tracks = []
            songs = data.get("data", {}).get("song", [])

            for song in songs:
                artists = [s.get("name", "") for s in song.get("singer", [])]
                tracks.append(Track(
                    id=f"qqmusic:{song['mid']}",
                    platform="qqmusic",
                    platform_id=song["mid"],
                    title=song.get("name", ""),
                    artists=artists,
                    album=song.get("albumname", ""),
                    duration=song.get("interval", 0),
                    cover_url=f"https://y.qq.com/music/photo_new/T002R300x300M000{song.get('albummid', '')}.jpg"
                ))

            return tracks[:limit]

        except Exception as e:
            logger.error(f"获取 QQ 音乐推荐失败: {e}")
            return []

    async def upload_track(
        self,
        file_path: str,
        title: str = None,
        artists: List[str] = None
    ) -> Optional[Track]:
        """
        上传本地歌曲到 QQ 音乐云盘

        Args:
            file_path: 本地文件路径
            title: 歌曲标题（可选）
            artists: 歌手列表（可选）

        Returns:
            上传后的歌曲信息，失败返回 None
        """
        if not self._authenticated:
            logger.warning("未认证，无法上传歌曲")
            return None

        try:
            import os

            session = self._get_session()
            headers = {"Cookie": self.cookie}

            # 读取文件
            with open(file_path, "rb") as f:
                file_data = f.read()

            filename = os.path.basename(file_path)

            # 构建上传请求
            form_data = aiohttp.FormData()
            form_data.add_field(
                "file",
                file_data,
                filename=filename,
                content_type="audio/mpeg"
            )

            if title:
                form_data.add_field("title", title)
            if artists:
                form_data.add_field("artists", ",".join(artists))

            async with session.post(
                f"{self.API_BASE}/qzone/fcg-bin/fcg_ucc_upload_music.fcg",
                data=form_data,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return None

                result = await resp.json()

                if result.get("code") == 0:
                    song = result.get("data", {})
                    return Track(
                        id=f"qqmusic:{song.get('mid', '')}",
                        platform="qqmusic",
                        platform_id=song.get("mid", ""),
                        title=song.get("name", title or filename),
                        artists=artists or [],
                        album="云盘音乐"
                    )

        except ImportError:
            logger.error("需要安装 aiohttp: pip install aiohttp")
        except Exception as e:
            logger.error(f"上传歌曲到 QQ 音乐失败: {e}")

        return None

    async def close(self):
        """关闭会话，释放资源"""
        if self._session:
            await self._session.close()
            self._session = None
