"""
本地音乐库管理

提供以下功能：
- 扫描本地音乐文件（MP3/FLAC/M4A）
- 解析元数据（ID3/Vorbis/MusicBrainz）
- 上传到平台云盘
- 本地歌曲管理
"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import sqlite3
import json
import logging
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .adapters.base import Track

logger = logging.getLogger(__name__)


# 支持的音频格式
SUPPORTED_FORMATS = {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".wma"}


@dataclass
class LocalTrack:
    """本地歌曲信息"""
    id: str
    file_path: str
    title: str
    artists: List[str] = field(default_factory=list)
    album: str = ""
    album_artist: str = ""
    year: int = 0
    track_number: int = 0
    disc_number: int = 0
    duration: int = 0
    genre: str = ""
    cover_path: Optional[str] = None
    cover_data: Optional[bytes] = None
    bitrate: int = 0
    sample_rate: int = 0
    channels: int = 0
    file_size: int = 0
    file_format: str = ""
    isrc: Optional[str] = None
    musicbrainz_id: Optional[str] = None
    added_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

    def to_track(self) -> Track:
        """转换为通用 Track 对象"""
        return Track(
            id=f"local:{self.id}",
            platform="local",
            platform_id=self.id,
            title=self.title,
            artists=self.artists,
            album=self.album,
            duration=self.duration,
            cover_url=self.cover_path,
            isrc=self.isrc
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "title": self.title,
            "artists": self.artists,
            "album": self.album,
            "album_artist": self.album_artist,
            "year": self.year,
            "track_number": self.track_number,
            "disc_number": self.disc_number,
            "duration": self.duration,
            "genre": self.genre,
            "bitrate": self.bitrate,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "file_size": self.file_size,
            "file_format": self.file_format,
            "isrc": self.isrc,
            "musicbrainz_id": self.musicbrainz_id,
            "added_at": self.added_at.isoformat(),
            "last_modified": self.last_modified.isoformat()
        }


@dataclass
class ScanResult:
    """扫描结果"""
    total_files: int = 0
    new_files: int = 0
    updated_files: int = 0
    failed_files: int = 0
    total_size: int = 0
    duration: float = 0.0
    errors: List[str] = field(default_factory=list)


class LocalLibrary:
    """本地音乐库"""

    def __init__(self, db_path: str = None, library_paths: List[str] = None):
        """
        初始化本地音乐库

        Args:
            db_path: 数据库路径，默认 ~/.jiuge/local_library.db
            library_paths: 音乐库路径列表
        """
        if db_path is None:
            db_path = Path.home() / ".jiuge" / "local_library.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.library_paths = library_paths or []
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- 本地歌曲表
                CREATE TABLE IF NOT EXISTS local_tracks (
                    id TEXT PRIMARY KEY,
                    file_path TEXT UNIQUE NOT NULL,
                    title TEXT,
                    artists TEXT,
                    album TEXT,
                    album_artist TEXT,
                    year INTEGER,
                    track_number INTEGER,
                    disc_number INTEGER,
                    duration INTEGER,
                    genre TEXT,
                    cover_path TEXT,
                    bitrate INTEGER,
                    sample_rate INTEGER,
                    channels INTEGER,
                    file_size INTEGER,
                    file_format TEXT,
                    isrc TEXT,
                    musicbrainz_id TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- 扫描历史表
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    library_path TEXT,
                    total_files INTEGER,
                    new_files INTEGER,
                    updated_files INTEGER,
                    failed_files INTEGER,
                    duration REAL,
                    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- 上传历史表
                CREATE TABLE IF NOT EXISTS upload_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    local_track_id TEXT,
                    platform TEXT,
                    remote_track_id TEXT,
                    status TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (local_track_id) REFERENCES local_tracks(id)
                );

                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_local_tracks_album ON local_tracks(album);
                CREATE INDEX IF NOT EXISTS idx_local_tracks_artists ON local_tracks(artists);
                CREATE INDEX IF NOT EXISTS idx_upload_history_track ON upload_history(local_track_id);
            """)

    def add_library_path(self, path: str):
        """添加音乐库路径"""
        if path not in self.library_paths:
            self.library_paths.append(path)

    def remove_library_path(self, path: str):
        """移除音乐库路径"""
        if path in self.library_paths:
            self.library_paths.remove(path)

    async def scan_library(
        self,
        paths: List[str] = None,
        progress_callback: Callable[[int, int], None] = None
    ) -> ScanResult:
        """
        扫描音乐库

        Args:
            paths: 要扫描的路径列表，默认使用 library_paths
            progress_callback: 进度回调函数 (current, total)

        Returns:
            扫描结果
        """
        import time
        start_time = time.time()

        paths = paths or self.library_paths
        result = ScanResult()

        # 收集所有音频文件
        all_files = []
        for lib_path in paths:
            files = self._collect_audio_files(lib_path)
            all_files.extend(files)

        result.total_files = len(all_files)

        # 并行处理文件
        with ThreadPoolExecutor(max_workers=4) as executor:
            loop = asyncio.get_event_loop()

            futures = []
            for i, file_path in enumerate(all_files):
                future = loop.run_in_executor(
                    executor,
                    self._process_file,
                    file_path
                )
                futures.append((i, future))

            # 收集结果
            for i, future in futures:
                try:
                    track = await future
                    if track:
                        # 检查是否已存在
                        existing = self._get_track_by_path(track.file_path)
                        if existing:
                            # 检查是否需要更新
                            if track.last_modified > existing.last_modified:
                                self._update_track(track)
                                result.updated_files += 1
                        else:
                            self._save_track(track)
                            result.new_files += 1

                        result.total_size += track.file_size
                except Exception as e:
                    result.failed_files += 1
                    result.errors.append(f"{all_files[i]}: {str(e)}")

                if progress_callback:
                    progress_callback(i + 1, result.total_files)

        result.duration = time.time() - start_time

        # 记录扫描历史
        self._record_scan(result)

        return result

    def _collect_audio_files(self, path: str) -> List[str]:
        """收集目录下的所有音频文件"""
        files = []
        path = Path(path)

        if not path.exists():
            return files

        if path.is_file():
            if path.suffix.lower() in SUPPORTED_FORMATS:
                files.append(str(path))
            return files

        # 递归遍历目录
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if Path(filename).suffix.lower() in SUPPORTED_FORMATS:
                    files.append(str(Path(root) / filename))

        return files

    def _process_file(self, file_path: str) -> Optional[LocalTrack]:
        """处理单个音频文件"""
        try:
            # 获取文件信息
            stat = os.stat(file_path)
            file_size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime)

            # 生成 ID
            track_id = self._generate_id(file_path)

            # 获取文件格式
            file_format = Path(file_path).suffix.lower()[1:]

            # 解析元数据
            metadata = self._parse_metadata(file_path)

            return LocalTrack(
                id=track_id,
                file_path=file_path,
                title=metadata.get("title") or Path(file_path).stem,
                artists=metadata.get("artists", []),
                album=metadata.get("album", ""),
                album_artist=metadata.get("album_artist", ""),
                year=metadata.get("year", 0),
                track_number=metadata.get("track_number", 0),
                disc_number=metadata.get("disc_number", 0),
                duration=metadata.get("duration", 0),
                genre=metadata.get("genre", ""),
                cover_path=metadata.get("cover_path"),
                cover_data=metadata.get("cover_data"),
                bitrate=metadata.get("bitrate", 0),
                sample_rate=metadata.get("sample_rate", 0),
                channels=metadata.get("channels", 0),
                file_size=file_size,
                file_format=file_format,
                isrc=metadata.get("isrc"),
                musicbrainz_id=metadata.get("musicbrainz_id"),
                last_modified=last_modified
            )

        except Exception as e:
            logger.error(f"处理文件失败: {file_path} - {e}")
            return None

    def _parse_metadata(self, file_path: str) -> Dict[str, Any]:
        """解析音频文件元数据"""
        metadata = {}
        suffix = Path(file_path).suffix.lower()

        try:
            if suffix == ".mp3":
                metadata = self._parse_id3(file_path)
            elif suffix == ".flac":
                metadata = self._parse_flac(file_path)
            elif suffix in (".m4a", ".aac"):
                metadata = self._parse_mp4(file_path)
            elif suffix == ".ogg":
                metadata = self._parse_vorbis(file_path)
            else:
                # 使用通用方法
                metadata = self._parse_generic(file_path)

        except Exception as e:
            logger.warning(f"解析元数据失败: {file_path} - {e}")
            # 尝试使用 mutagen 作为后备
            try:
                metadata = self._parse_with_mutagen(file_path)
            except Exception:
                pass

        return metadata

    def _parse_id3(self, file_path: str) -> Dict[str, Any]:
        """解析 ID3 标签（MP3）"""
        metadata = {}

        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TDRC, TRCK, TPOS, TCON, USLT, APIC

            audio = MP3(file_path, ID3=ID3)

            # 基本信息
            metadata["duration"] = int(audio.info.length)
            metadata["bitrate"] = int(audio.info.bitrate)
            metadata["sample_rate"] = int(audio.info.sample_rate)
            metadata["channels"] = 2 if audio.info.mode == 0 else 1

            # ID3 标签
            tags = audio.tags
            if tags:
                for frame in tags.values():
                    if isinstance(frame, TIT2):
                        metadata["title"] = str(frame)
                    elif isinstance(frame, TPE1):
                        metadata["artists"] = [a.strip() for a in str(frame).split("/")]
                    elif isinstance(frame, TALB):
                        metadata["album"] = str(frame)
                    elif isinstance(frame, TPE2):
                        metadata["album_artist"] = str(frame)
                    elif isinstance(frame, TDRC):
                        year_str = str(frame)[:4]
                        metadata["year"] = int(year_str) if year_str.isdigit() else 0
                    elif isinstance(frame, TRCK):
                        track_str = str(frame)
                        if "/" in track_str:
                            metadata["track_number"] = int(track_str.split("/")[0])
                        else:
                            metadata["track_number"] = int(track_str) if track_str.isdigit() else 0
                    elif isinstance(frame, TPOS):
                        disc_str = str(frame)
                        metadata["disc_number"] = int(disc_str) if disc_str.isdigit() else 0
                    elif isinstance(frame, TCON):
                        metadata["genre"] = str(frame)
                    elif isinstance(frame, APIC):
                        metadata["cover_data"] = frame.data

        except ImportError:
            logger.debug("mutagen 未安装，尝试其他方法")
        except Exception as e:
            logger.debug(f"ID3 解析失败: {e}")

        return metadata

    def _parse_flac(self, file_path: str) -> Dict[str, Any]:
        """解析 FLAC 元数据"""
        metadata = {}

        try:
            from mutagen.flac import FLAC

            audio = FLAC(file_path)

            # 基本信息
            metadata["duration"] = int(audio.info.length)
            metadata["bitrate"] = int(audio.info.bitrate)
            metadata["sample_rate"] = int(audio.info.sample_rate)
            metadata["channels"] = audio.info.channels

            # Vorbis 注释
            if "title" in audio:
                metadata["title"] = audio["title"][0]
            if "artist" in audio:
                metadata["artists"] = audio["artist"]
            if "album" in audio:
                metadata["album"] = audio["album"][0]
            if "albumartist" in audio:
                metadata["album_artist"] = audio["albumartist"][0]
            if "date" in audio:
                year_str = audio["date"][0][:4]
                metadata["year"] = int(year_str) if year_str.isdigit() else 0
            if "tracknumber" in audio:
                track_str = audio["tracknumber"][0]
                metadata["track_number"] = int(track_str) if track_str.isdigit() else 0
            if "discnumber" in audio:
                disc_str = audio["discnumber"][0]
                metadata["disc_number"] = int(disc_str) if disc_str.isdigit() else 0
            if "genre" in audio:
                metadata["genre"] = audio["genre"][0]
            if "isrc" in audio:
                metadata["isrc"] = audio["isrc"][0]
            if "musicbrainz_trackid" in audio:
                metadata["musicbrainz_id"] = audio["musicbrainz_trackid"][0]

            # 封面
            if audio.pictures:
                metadata["cover_data"] = audio.pictures[0].data

        except ImportError:
            logger.debug("mutagen 未安装")
        except Exception as e:
            logger.debug(f"FLAC 解析失败: {e}")

        return metadata

    def _parse_mp4(self, file_path: str) -> Dict[str, Any]:
        """解析 MP4/M4A 元数据"""
        metadata = {}

        try:
            from mutagen.mp4 import MP4

            audio = MP4(file_path)

            # 基本信息
            metadata["duration"] = int(audio.info.length)
            metadata["bitrate"] = int(audio.info.bitrate)
            metadata["sample_rate"] = int(audio.info.sample_rate)
            metadata["channels"] = audio.info.channels

            # MP4 标签
            if "\xa9nam" in audio:  # title
                metadata["title"] = audio["\xa9nam"][0]
            if "\xa9ART" in audio:  # artist
                metadata["artists"] = audio["\xa9ART"]
            if "\xa9alb" in audio:  # album
                metadata["album"] = audio["\xa9alb"][0]
            if "aART" in audio:  # album artist
                metadata["album_artist"] = audio["aART"][0]
            if "\xa9day" in audio:  # year
                year_str = str(audio["\xa9day"][0])[:4]
                metadata["year"] = int(year_str) if year_str.isdigit() else 0
            if "trkn" in audio:  # track number
                metadata["track_number"] = audio["trkn"][0][0]
            if "disk" in audio:  # disc number
                metadata["disc_number"] = audio["disk"][0][0]
            if "\xa9gen" in audio:  # genre
                metadata["genre"] = audio["\xa9gen"][0]
            if "covr" in audio:  # cover
                metadata["cover_data"] = audio["covr"][0]

        except ImportError:
            logger.debug("mutagen 未安装")
        except Exception as e:
            logger.debug(f"MP4 解析失败: {e}")

        return metadata

    def _parse_vorbis(self, file_path: str) -> Dict[str, Any]:
        """解析 Ogg Vorbis 元数据"""
        metadata = {}

        try:
            from mutagen.oggvorbis import OggVorbis

            audio = OggVorbis(file_path)

            # 基本信息
            metadata["duration"] = int(audio.info.length)
            metadata["bitrate"] = int(audio.info.bitrate)
            metadata["sample_rate"] = int(audio.info.sample_rate)
            metadata["channels"] = audio.info.channels

            # Vorbis 注释
            if "title" in audio:
                metadata["title"] = audio["title"][0]
            if "artist" in audio:
                metadata["artists"] = audio["artist"]
            if "album" in audio:
                metadata["album"] = audio["album"][0]
            if "albumartist" in audio:
                metadata["album_artist"] = audio["albumartist"][0]
            if "date" in audio:
                year_str = audio["date"][0][:4]
                metadata["year"] = int(year_str) if year_str.isdigit() else 0
            if "tracknumber" in audio:
                metadata["track_number"] = int(audio["tracknumber"][0])
            if "genre" in audio:
                metadata["genre"] = audio["genre"][0]

        except ImportError:
            logger.debug("mutagen 未安装")
        except Exception as e:
            logger.debug(f"Vorbis 解析失败: {e}")

        return metadata

    def _parse_generic(self, file_path: str) -> Dict[str, Any]:
        """使用 mutagen 通用方法解析"""
        return self._parse_with_mutagen(file_path)

    def _parse_with_mutagen(self, file_path: str) -> Dict[str, Any]:
        """使用 mutagen 解析（通用方法）"""
        metadata = {}

        try:
            import mutagen

            audio = mutagen.File(file_path)
            if audio:
                metadata["duration"] = int(audio.info.length)

                if hasattr(audio.info, "bitrate"):
                    metadata["bitrate"] = int(audio.info.bitrate)
                if hasattr(audio.info, "sample_rate"):
                    metadata["sample_rate"] = int(audio.info.sample_rate)
                if hasattr(audio.info, "channels"):
                    metadata["channels"] = audio.info.channels

        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"通用解析失败: {e}")

        return metadata

    def _generate_id(self, file_path: str) -> str:
        """生成歌曲 ID"""
        import hashlib
        return hashlib.md5(file_path.encode()).hexdigest()[:16]

    def _save_track(self, track: LocalTrack):
        """保存歌曲到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO local_tracks
                (id, file_path, title, artists, album, album_artist,
                 year, track_number, disc_number, duration, genre,
                 cover_path, bitrate, sample_rate, channels, file_size,
                 file_format, isrc, musicbrainz_id, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                track.id, track.file_path, track.title,
                json.dumps(track.artists, ensure_ascii=False),
                track.album, track.album_artist, track.year,
                track.track_number, track.disc_number, track.duration,
                track.genre, track.cover_path, track.bitrate,
                track.sample_rate, track.channels, track.file_size,
                track.file_format, track.isrc, track.musicbrainz_id,
                track.last_modified.isoformat()
            ))

    def _update_track(self, track: LocalTrack):
        """更新歌曲信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE local_tracks SET
                    title = ?, artists = ?, album = ?, album_artist = ?,
                    year = ?, track_number = ?, disc_number = ?, duration = ?,
                    genre = ?, cover_path = ?, bitrate = ?, sample_rate = ?,
                    channels = ?, file_size = ?, isrc = ?, musicbrainz_id = ?,
                    last_modified = ?
                WHERE id = ?
            """, (
                track.title,
                json.dumps(track.artists, ensure_ascii=False),
                track.album, track.album_artist, track.year,
                track.track_number, track.disc_number, track.duration,
                track.genre, track.cover_path, track.bitrate,
                track.sample_rate, track.channels, track.file_size,
                track.isrc, track.musicbrainz_id,
                track.last_modified.isoformat(),
                track.id
            ))

    def _get_track_by_path(self, file_path: str) -> Optional[LocalTrack]:
        """根据路径获取歌曲"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM local_tracks WHERE file_path = ?",
                (file_path,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_track(row)

        return None

    def _row_to_track(self, row: sqlite3.Row) -> LocalTrack:
        """转换数据库行到 LocalTrack"""
        return LocalTrack(
            id=row["id"],
            file_path=row["file_path"],
            title=row["title"] or "",
            artists=json.loads(row["artists"]) if row["artists"] else [],
            album=row["album"] or "",
            album_artist=row["album_artist"] or "",
            year=row["year"] or 0,
            track_number=row["track_number"] or 0,
            disc_number=row["disc_number"] or 0,
            duration=row["duration"] or 0,
            genre=row["genre"] or "",
            cover_path=row["cover_path"],
            bitrate=row["bitrate"] or 0,
            sample_rate=row["sample_rate"] or 0,
            channels=row["channels"] or 0,
            file_size=row["file_size"] or 0,
            file_format=row["file_format"] or "",
            isrc=row["isrc"],
            musicbrainz_id=row["musicbrainz_id"],
            added_at=datetime.fromisoformat(row["added_at"]),
            last_modified=datetime.fromisoformat(row["last_modified"])
        )

    def _record_scan(self, result: ScanResult):
        """记录扫描历史"""
        with sqlite3.connect(self.db_path) as conn:
            for lib_path in self.library_paths:
                conn.execute("""
                    INSERT INTO scan_history
                    (library_path, total_files, new_files, updated_files,
                     failed_files, duration)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    lib_path, result.total_files, result.new_files,
                    result.updated_files, result.failed_files, result.duration
                ))

    def get_all_tracks(self, limit: int = 100, offset: int = 0) -> List[LocalTrack]:
        """获取所有歌曲"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM local_tracks
                ORDER BY added_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            return [self._row_to_track(row) for row in cursor.fetchall()]

    def search_tracks(self, query: str, limit: int = 50) -> List[LocalTrack]:
        """搜索歌曲"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 构建搜索条件
            search_pattern = f"%{query}%"

            cursor = conn.execute("""
                SELECT * FROM local_tracks
                WHERE title LIKE ?
                   OR artists LIKE ?
                   OR album LIKE ?
                ORDER BY title
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, limit))

            return [self._row_to_track(row) for row in cursor.fetchall()]

    def get_track_by_id(self, track_id: str) -> Optional[LocalTrack]:
        """根据 ID 获取歌曲"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM local_tracks WHERE id = ?",
                (track_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_track(row)

        return None

    def delete_track(self, track_id: str) -> bool:
        """删除歌曲记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM local_tracks WHERE id = ?",
                (track_id,)
            )
            return cursor.rowcount > 0

    def get_albums(self) -> List[Dict[str, Any]]:
        """获取所有专辑"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute("""
                SELECT album, album_artist, year,
                       COUNT(*) as track_count,
                       SUM(duration) as total_duration,
                       MIN(cover_path) as cover_path
                FROM local_tracks
                WHERE album IS NOT NULL AND album != ''
                GROUP BY album, album_artist
                ORDER BY album
            """)

            return [dict(row) for row in cursor.fetchall()]

    def get_artists(self) -> List[Dict[str, Any]]:
        """获取所有歌手"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute("""
                SELECT DISTINCT
                    json_extract(artists, '$[0]') as artist,
                    COUNT(*) as track_count,
                    COUNT(DISTINCT album) as album_count
                FROM local_tracks
                WHERE artists IS NOT NULL AND artists != '[]'
                GROUP BY artist
                ORDER BY track_count DESC
            """)

            return [dict(row) for row in cursor.fetchall() if row["artist"]]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            stats = {}

            # 总歌曲数
            stats["total_tracks"] = conn.execute(
                "SELECT COUNT(*) as count FROM local_tracks"
            ).fetchone()["count"]

            # 总大小
            stats["total_size"] = conn.execute(
                "SELECT SUM(file_size) as size FROM local_tracks"
            ).fetchone()["size"] or 0

            # 总时长
            stats["total_duration"] = conn.execute(
                "SELECT SUM(duration) as duration FROM local_tracks"
            ).fetchone()["duration"] or 0

            # 专辑数
            stats["total_albums"] = conn.execute("""
                SELECT COUNT(DISTINCT album) as count
                FROM local_tracks
                WHERE album IS NOT NULL AND album != ''
            """).fetchone()["count"]

            # 歌手数
            stats["total_artists"] = conn.execute("""
                SELECT COUNT(DISTINCT json_extract(artists, '$[0]')) as count
                FROM local_tracks
                WHERE artists IS NOT NULL AND artists != '[]'
            """).fetchone()["count"]

            # 格式分布
            format_dist = conn.execute("""
                SELECT file_format, COUNT(*) as count
                FROM local_tracks
                GROUP BY file_format
                ORDER BY count DESC
            """).fetchall()

            stats["format_distribution"] = {
                r["file_format"]: r["count"] for r in format_dist
            }

            return stats

    async def upload_to_platform(
        self,
        track_id: str,
        adapter: Any,  # MusicPlatformAdapter
        title: str = None,
        artists: List[str] = None
    ) -> Optional[str]:
        """
        上传歌曲到平台云盘

        Args:
            track_id: 本地歌曲 ID
            adapter: 目标平台适配器
            title: 覆盖标题
            artists: 覆盖歌手

        Returns:
            远程歌曲 ID，失败返回 None
        """
        track = self.get_track_by_id(track_id)
        if not track:
            logger.error(f"歌曲不存在: {track_id}")
            return None

        # 检查适配器是否支持上传
        if not hasattr(adapter, "upload_track"):
            logger.error(f"平台 {adapter.name} 不支持上传")
            return None

        try:
            # 执行上传
            remote_track = await adapter.upload_track(
                track.file_path,
                title=title or track.title,
                artists=artists or track.artists
            )

            if remote_track:
                # 记录上传历史
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO upload_history
                        (local_track_id, platform, remote_track_id, status)
                        VALUES (?, ?, ?, 'success')
                    """, (track_id, adapter.name, remote_track.platform_id))

                return remote_track.platform_id

        except Exception as e:
            logger.error(f"上传失败: {e}")

            # 记录失败
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO upload_history
                    (local_track_id, platform, remote_track_id, status)
                    VALUES (?, ?, NULL, 'failed')
                """, (track_id, adapter.name))

        return None

    async def batch_upload(
        self,
        track_ids: List[str],
        adapter: Any,
        progress_callback: Callable[[int, int], None] = None
    ) -> Dict[str, str]:
        """
        批量上传歌曲

        Args:
            track_ids: 歌曲 ID 列表
            adapter: 目标平台适配器
            progress_callback: 进度回调

        Returns:
            映射字典 {local_id: remote_id}
        """
        results = {}

        for i, track_id in enumerate(track_ids):
            remote_id = await self.upload_to_platform(track_id, adapter)
            if remote_id:
                results[track_id] = remote_id

            if progress_callback:
                progress_callback(i + 1, len(track_ids))

        return results
