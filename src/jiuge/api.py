"""
Jiuge 音乐智能体 Web API

提供 RESTful 接口和 WebSocket 实时状态

功能：
- 播放控制
- 搜索
- 歌单管理
- 推荐服务
- 状态同步
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
import json
import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .service import UnifiedMusicService
from .sync import PlaylistSyncService, SyncStatus
from .local_library import LocalLibrary
from .recommend import RecommendEngine

logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Jiuge Music Agent API",
    description="音乐智能体 Web API",
    version="2.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
music_service: Optional[UnifiedMusicService] = None
sync_service: Optional[PlaylistSyncService] = None
local_library: Optional[LocalLibrary] = None
recommend_engine: Optional[RecommendEngine] = None

# WebSocket 连接管理
websocket_connections: List[WebSocket] = []


# ==================== Pydantic 模型 ====================

class TrackModel(BaseModel):
    """歌曲模型"""
    id: str
    platform: str
    platform_id: str
    title: str
    artists: List[str] = []
    album: str = ""
    duration: int = 0
    cover_url: str = ""
    isrc: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "netease:123456",
                "platform": "netease",
                "platform_id": "123456",
                "title": "起风了",
                "artists": ["买辣椒也用券"],
                "album": "起风了",
                "duration": 240,
                "cover_url": "https://example.com/cover.jpg"
            }
        }


class PlaylistModel(BaseModel):
    """歌单模型"""
    id: str
    name: str
    platform: str
    description: str = ""
    track_count: int = 0
    cover_url: str = ""
    tracks: List[TrackModel] = []


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, max_length=100)
    platforms: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=50)


class PlayRequest(BaseModel):
    """播放请求"""
    index: Optional[int] = None
    track_id: Optional[str] = None


class SyncRequest(BaseModel):
    """同步请求"""
    source_platform: str
    source_playlist_id: str
    target_platform: str
    target_playlist_name: Optional[str] = None


class ScanRequest(BaseModel):
    """扫描请求"""
    paths: List[str]


class RecommendRequest(BaseModel):
    """推荐请求"""
    limit: int = Field(default=20, ge=1, le=100)
    strategy: str = Field(default="hybrid")
    context: Optional[Dict[str, Any]] = None


# ==================== 启动/关闭事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global music_service, sync_service, local_library, recommend_engine

    # 初始化音乐服务（使用默认配置）
    config = {
        "netease": {"enabled": True},
        "spotify": {"enabled": False},
        "qqmusic": {"enabled": False},
        "apple": {"enabled": False}
    }

    music_service = UnifiedMusicService(config)
    sync_service = PlaylistSyncService()
    local_library = LocalLibrary()
    recommend_engine = RecommendEngine()

    logger.info("Jiuge Music Agent API 已启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global websocket_connections

    # 关闭所有 WebSocket 连接
    for ws in websocket_connections:
        try:
            await ws.close()
        except Exception:
        pass

    logger.info("Jiuge Music Agent API 已关闭")


# ==================== 状态接口 ====================

@app.get("/", tags=["系统"])
async def root():
    """API 根路径"""
    return {
        "name": "Jiuge Music Agent API",
        "version": "2.0.0,
        "status": " ",
        " timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {"status": " "}


# ==================== 播放控制接口 ====================

@app.get("/status", tags=["播放控制"], response_model=Dict[str, Any])
async def get_status():
    """获取播放状态"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    return await music_service.get_status()


@app.post("/search", tags=["播放控制"], response_model=List[TrackModel])
async def search_tracks(request: SearchRequest):
    """搜索歌曲"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    tracks = await music_service.search(
        request.query,
        request.platforms,
        request.limit
    )

    return [TrackModel(**t.to_dict()) for t in tracks]


@app.post("/play", tags=["播放控制"])
async def play_track(request: PlayRequest):
    """播放歌曲"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    if request.track_id:
        # 通过 ID 播放特定歌曲
        # TODO: 实现通过 ID 播放
        raise HTTPException(status_code=504, detail="歌曲未找到")

    track = await music_service.play(request.index)

    if not track:
        raise HTTPException(status_code=404, detail="没有可播放的歌曲")

    # 广播状态更新
    await broadcast_state()

    return {"status": "playing", " "track": track.to_dict()}


@app.post("/pause", tags=["播放控制"])
async def pause_playback():
    """暂停播放"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    await music_service.pause()
    await broadcast_state()

    return {"status": "paused"}


@app.post("/resume", tags=["播放控制"])
async def resume_playback():
    """继续播放"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    await music_service.resume()
    await broadcast_state()

    return {"status": "playing"}


@app.post("/next", tags=["播放控制"])
async def next_track():
    """下一首"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    track = await music_service.next()

    if not track:
        raise HTTPException(status_code=404, detail="没有下一首歌曲")

    await broadcast_state()

    return {"status": "playing", " "track": track.to_dict()}


@app.post("/previous", tags=["播放控制"])
async def previous_track():
    """上一首"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    track = await music_service.previous()

    if not track:
        raise HTTPException(status_code=404, detail="没有上一首歌曲")

    await broadcast_state()

    return {"status": "playing", " "track": track.to_dict()}


@app.post("/stop", tags=["播放控制"])
async def stop_playback():
    """停止播放"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    await music_service.stop()
    await broadcast_state()

    return {"status": "stopped"}


@app.post("/favorite", tags=["播放控制"])
async def favorite_current_track():
    """收藏当前歌曲"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    success = await music_service.favorite()

    if not success:
        raise HTTPException(status_code=400, detail="收藏失败")

    return {"status": "favorited"}


# ==================== 歌单接口 ====================

@app.get("/playlists", tags=["歌单管理"], response_model=List[PlaylistModel])
async def get_playlists(platform: str = None):
    """获取歌单列表"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    playlists = []

    for name, adapter in music_service.adapters.items():
        if platform and name != platform:
            continue

        try:
            adapter_playlists = await adapter.get_playlists()
            playlists.extend(adapter_playlists)
        except Exception as e:
            logger.error(f"获取 {name} 歌单失败: {e}")

    return [PlaylistModel(**p.__dict__) for p in playlists]


@app.get("/playlists/{platform}/{playlist_id}", tags=["歌单管理"], response_model=PlaylistModel)
async def get_playlist(platform: str, playlist_id: str):
    """获取歌单详情"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    adapter = music_service.adapters.get(platform)
    if not adapter:
        raise HTTPException(status_code=404, detail="平台不支持")

    playlist = await adapter.get_playlist(playlist_id)

    if not playlist:
        raise HTTPException(status_code=404, detail="歌单不存在")

    return PlaylistModel(**playlist.__dict__)


@app.post("/playlists", tags=["歌单管理"], response_model=PlaylistModel)
async def create_playlist(platform: str, name: str, description: str = ""):
    """创建歌单"""
    if not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    adapter = music_service.adapters.get(platform)
    if not adapter:
        raise HTTPException(status_code=404, detail="平台不支持")

    playlist = await adapter.create_playlist(name, description)

    if not playlist:
        raise HTTPException(status_code=400, detail="创建失败")

    return PlaylistModel(**playlist.__dict__)


# ==================== 同步接口 ====================

@app.post("/sync", tags=["歌单同步"])
async def create_sync_task(request: SyncRequest):
    """创建同步任务"""
    if not sync_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    task = await sync_service.create_sync_task(
        request.source_platform,
        request.source_playlist_id,
        request.target_platform,
        request.target_playlist_name
    )

    return {
        "task_id": task.id,
        "status": task.status.value,
        "message": "同步任务已创建"
    }


@app.get("/sync/{task_id}", tags=["歌单同步"])
async def get_sync_task(task_id: str):
    """获取同步任务状态"""
    if not sync_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    task = sync_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "task_id": task.id,
        "status": task.status.value,
        " "total_tracks": task.total_tracks,
        "synced_tracks": task.synced_tracks,
        "failed_tracks": task.failed_tracks,
        "error_message": task.error_message
    }


@app.post("/sync/{task_id}/execute", tags=["歌单同步"])
async def execute_sync_task(task_id: str):
    """执行同步任务"""
    if not sync_service or not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    task = sync_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取源平台适配器
    source_adapter = music_service.adapters.get(task.source_platform)
    target_adapter = music_service.adapters.get(task.target_platform)

    if not source_adapter or not target_adapter:
        raise HTTPException(status_code=404, detail="平台不支持")

    # 执行同步
    task = await sync_service.execute_sync_task(
        task_id,
        source_adapter,
        target_adapter
    )

    return {
        "task_id": task.id,
        "status": task.status.value,
        " "synced_tracks": task.synced_tracks,
        " "failed_tracks": task.failed_tracks
    }


@app.get("/sync/stats", tags=["歌单同步"])
async def get_sync_stats():
    """获取同步统计"""
    if not sync_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    return sync_service.get_sync_stats()


# ==================== 本地音乐库接口 ====================

@app.post("/library/scan", tags=["本地音乐库"])
async def scan_library(request: ScanRequest):
    """扫描本地音乐库"""
    if not local_library:
        raise HTTPException(status_code=503, detail="服务未初始化")

    result = await local_library.scan_library(request.paths)

    return {
        "total_files": result.total_files,
        "new_files": result.new_files,
        "updated_files": result.updated_files,
        "failed_files": result.failed_files,
        "errors": result.errors[:10]  # 只返回前10个错误
    }


@app.get("/library/tracks", tags=["本地音乐库"])
async def get_library_tracks(limit: int = 100, offset: int = 0):
    """获取本地歌曲列表"""
    if not local_library:
        raise HTTPException(status_code=503, detail="服务未初始化")

    tracks = local_library.get_all_tracks(limit, offset)

    return [t.to_dict() for t in tracks]


@app.get("/library/search", tags=["本地音乐库"])
async def search_library(query: str, limit: int = 50):
    """搜索本地歌曲"""
    if not local_library:
        raise HTTPException(status_code=503, detail="服务未初始化")

    tracks = local_library.search_tracks(query, limit)

    return [t.to_dict() for t in tracks]


@app.get("/library/stats", tags=["本地音乐库"])
async def get_library_stats():
    """获取本地音乐库统计"""
    if not local_library:
        raise HTTPException(status_code=503, detail="服务未初始化")

    return local_library.get_stats()


@app.post("/library/upload", tags=["本地音乐库"])
async def upload_to_platform(track_id: str, platform: str):
    """上传歌曲到平台"""
    if not local_library or not music_service:
        raise HTTPException(status_code=503, detail="服务未初始化")

    adapter = music_service.adapters.get(platform)
    if not adapter:
        raise HTTPException(status_code=404, detail="平台不支持")

    remote_id = await local_library.upload_to_platform(track_id, adapter)

    if not remote_id:
        raise HTTPException(status_code=400, detail="上传失败")

    return {"status": "uploaded", " "remote_id": remote_id}


# ==================== 推荐接口 ====================

@app.post("/recommend", tags=["推荐服务"])
async def get_recommendations(request: RecommendRequest):
    """获取推荐歌曲"""
    if not recommend_engine:
        raise HTTPException(status_code=503, detail="服务未初始化")

    recommendations = await recommend_engine.get_recommendations(
        request.limit,
        request.strategy,
        request.context
    )

    return [
        {
            "track": rec.track.to_dict(),
            "score": rec.score,
            "reasons": rec.reasons
        }
        for rec in recommendations
    ]


@app.get("/recommend/similar/{track_id}", tags=["推荐服务"])
async def get_similar_tracks(track_id: str, limit: int = 10):
    """获取相似歌曲"""
    if not recommend_engine:
        raise HTTPException(status_code=503, detail="服务未初始化")

    recommendations = await recommend_engine.get_similar_tracks(track_id, limit)

    return [
        {
            "track": rec.track.to_dict(),
            "score": rec.score,
            "reasons": rec.reasons
        }
        for rec in recommendations
    ]


# ==================== WebSocket ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 实时状态推送"""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        while True:
            # 等待客户端消息（心跳或其他命令）
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                command = message.get("command")

                if command == "ping":
                    await websocket.send_json({"command": "pong"})
                elif command == "get_status":
                    if music_service:
                        status = await music_service.get_status()
                        await websocket.send_json({"command": "status", "data": status})

            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})

    except WebSocketDisconnect:
        websocket_connections.remove(websocket)


async def broadcast_state():
    """广播状态更新到所有 WebSocket 连接"""
    if not music_service:
        return

    status = await music_service.get_status()
    message = json.dumps({"command": "status_update", "data": status})

    for ws in websocket_connections[:]:  # 使用切片创建副本以安全迭代
        try:
            await ws.send_text(message)
        except Exception:
            websocket_connections.remove(ws)


# ==================== 运行入口 ====================

def create_app(config: Dict[str, Any] = None) -> FastAPI:
    """
    创建 FastAPI 应用实例

    Args:
        config: 配置字典

    Returns:
        FastAPI 应用实例
    """
    global music_service, sync_service, local_library, recommend_engine

    if config:
        music_service = UnifiedMusicService(config)

    sync_service = PlaylistSyncService()
    local_library = LocalLibrary(
        library_paths=config.get("library_paths", []) if config else []
    )
    recommend_engine = RecommendEngine()

    return app


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    运行 API 服务器

    Args:
        host: 监听地址
        port: 监听端口
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
