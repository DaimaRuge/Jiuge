# Jiuge 音乐智能体 PRD (产品需求文档)

**版本**: v1.0  
**日期**: 2026-03-17  
**作者**: DaimaRuge

---

## 1. 产品概述

### 1.1 产品定位

Jiuge 是一个基于 OpenClaw 的个人音乐 AI Agent，通过多渠道（语音、飞书、Telegram、Discord）控制多平台音乐服务（Spotify、QQ音乐、网易云音乐、Apple Music），实现统一的音乐搜索、播放、管理和推荐体验。

### 1.2 目标用户

- 多平台音乐服务用户
- 需要统一音乐管理的个人用户
- 对音乐推荐有个性化需求的用户
- 有本地音乐库管理需求的用户

### 1.3 核心价值

1. **统一入口** - 一个 Agent 控制所有音乐平台
2. **智能聚合** - 跨平台歌曲去重、歌单同步
3. **随身记忆** - 音乐偏好可移植到不同 Agent
4. **AI 创作** - 支持个人音乐创作

---

## 2. 功能需求

### 2.1 核心功能模块

```
┌─────────────────────────────────────────────────────────────┐
│                      Jiuge Music Agent                       │
├─────────────────────────────────────────────────────────────┤
│  📱 多渠道接入                                                │
│  ├── 语音 (Siri/语音助手)                                     │
│  ├── 飞书 (Feishu)                                           │
│  ├── Telegram                                                │
│  └── Discord                                                 │
├─────────────────────────────────────────────────────────────┤
│  🎵 多平台音乐                                                │
│  ├── Spotify                                                 │
│  ├── QQ 音乐                                                  │
│  ├── 网易云音乐                                               │
│  └── Apple Music                                             │
├─────────────────────────────────────────────────────────────┤
│  🔧 核心能力                                                  │
│  ├── 搜索 (跨平台)                                           │
│  ├── 播放控制 (播放/暂停/上下首/收藏)                          │
│  ├── 歌单管理 (创建/编辑/同步)                                 │
│  ├── 本地上传 (本地→云盘/平台)                                │
│  ├── 听歌统计 (记录/分析)                                     │
│  ├── 智能推荐 (基于历史/偏好)                                  │
│  ├── 歌曲发现 (新歌/热门)                                     │
│  └── AI 创作 (生成音乐)                                       │
├─────────────────────────────────────────────────────────────┤
│  💾 记忆系统                                                  │
│  ├── 播放历史                                                │
│  ├── 收藏记录                                                │
│  ├── 偏好画像                                                │
│  └── 歌单数据                                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 功能清单

| 模块 | 功能 | 优先级 | 描述 |
|------|------|--------|------|
| **搜索** | 单曲搜索 | P0 | 跨平台搜索歌曲 |
| | 歌手搜索 | P0 | 按歌手搜索 |
| | 歌单搜索 | P1 | 搜索公开歌单 |
| | 专辑搜索 | P1 | 搜索专辑 |
| | 歌词搜索 | P2 | 按歌词搜索 |
| **播放** | 播放/暂停 | P0 | 基本控制 |
| | 上一首/下一首 | P0 | 切换歌曲 |
| | 进度控制 | P1 | 快进/快退 |
| | 音量控制 | P1 | 调节音量 |
| | 随机/循环 | P1 | 播放模式 |
| **歌单** | 创建歌单 | P0 | 新建歌单 |
| | 编辑歌单 | P0 | 添加/删除歌曲 |
| | 同步歌单 | P1 | 跨平台同步 |
| | 导入歌单 | P1 | 从文件导入 |
| | 导出歌单 | P1 | 导出为文件 |
| **收藏** | 收藏歌曲 | P0 | 添加到收藏 |
| | 取消收藏 | P0 | 移除收藏 |
| | 收藏列表 | P0 | 查看收藏 |
| **上传** | 本地扫描 | P1 | 扫描本地音乐 |
| | 上传到云盘 | P1 | 上传到平台云盘 |
| | 元数据匹配 | P2 | 自动匹配歌曲信息 |
| **统计** | 播放记录 | P1 | 记录播放历史 |
| | 统计报告 | P2 | 周/月统计 |
| | 听歌排行 | P2 | 热门歌曲 |
| **推荐** | 每日推荐 | P1 | 基于偏好推荐 |
| | 相似歌曲 | P1 | 推荐相似歌曲 |
| | 发现新歌 | P2 | 发现新发布 |
| **AI创作** | 生成旋律 | P2 | AI生成音乐 |
| | 风格迁移 | P3 | 风格转换 |
| | 混音制作 | P3 | 混音功能 |

### 2.3 多平台支持矩阵

| 平台 | 搜索 | 播放 | 歌单 | 收藏 | 上传 | API类型 |
|------|------|------|------|------|------|---------|
| Spotify | ✅ | ✅ | ✅ | ✅ | ❌ | 官方 REST API |
| QQ音乐 | ✅ | ✅ | ✅ | ✅ | ✅ | 官方开放平台 |
| 网易云音乐 | ✅ | ✅ | ✅ | ✅ | ✅ | 第三方 API |
| Apple Music | ✅ | ✅ | ✅ | ✅ | ❌ | MusicKit API |

---

## 3. 技术架构

### 3.1 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        OpenClaw Gateway                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│   │ Feishu  │  │Telegram │  │ Discord │  │  Voice  │            │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│        │            │            │            │                  │
│        └────────────┴─────┬──────┴────────────┘                  │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Jiuge Agent (Skill)                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Command Parser                            │ │
│  │  • 听周杰伦的歌 → search("周杰伦")                            │ │
│  │  • 播放第一首 → play(0)                                      │ │
│  │  • 加入收藏 → favorite()                                     │ │
│  │  • 创建歌单 → create_playlist()                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Platform Adapters                          │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │ │
│  │  │ Spotify │ │ QQ Music│ │ Netease │ │ Apple   │           │ │
│  │  │ Adapter │ │ Adapter │ │ Adapter │ │ Adapter │           │ │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │ │
│  └───────┼──────────┼──────────┼──────────┼───────────────────┘ │
│          │          │          │          │                     │
│  ┌───────┴──────────┴──────────┴──────────┴───────────────────┐ │
│  │                     Unified Music API                       │ │
│  │  search() | play() | pause() | next() | favorite() | ...   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Audio Player                              │ │
│  │  ffpyplayer / MPV / Platform Native                         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Music Memory Store                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │ Play History  │  │  Favorites    │  │  Preferences   │        │
│  │   (SQLite)    │  │   (SQLite)    │  │    (JSON)     │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│                                                                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │   Playlists   │  │   Statistics  │  │   AI Models   │        │
│  │   (SQLite)    │  │   (SQLite)    │  │   (Config)    │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **Agent框架** | OpenClaw | 已有框架 |
| **后端语言** | Python 3.11+ | 主要开发语言 |
| **API框架** | FastAPI | 可选的独立API服务 |
| **音频播放** | ffpyplayer / MPV | 本地播放 |
| **数据库** | SQLite | 轻量级存储 |
| **缓存** | Redis (可选) | 提升性能 |
| **任务队列** | Celery (可选) | 异步任务 |
| **AI音乐** | MusicGen / AudioLDM | AI创作 |

### 3.3 音乐平台 API

#### Spotify Web API
- **认证**: OAuth 2.0
- **端点**: `https://api.spotify.com/v1/`
- **主要功能**:
  - 搜索: `GET /search?q={query}&type=track`
  - 播放: `PUT /me/player/play`
  - 歌单: `GET /me/playlists`
  - 收藏: `PUT /me/tracks?ids={ids}`

#### QQ音乐开放平台
- **认证**: OAuth 2.0 + App Key
- **端点**: 需申请
- **主要功能**: 搜索、播放、歌单、云盘上传

#### 网易云音乐 API (NeteaseCloudMusicApi)
- **类型**: 第三方开源 API
- **主要接口**:
  - 搜索: `/search?keywords={query}`
  - 播放URL: `/song/url/v1?id={id}`
  - 歌单: `/playlist/detail?id={id}`
  - 云盘: `/cloud`

#### Apple Music API
- **认证**: Developer Token + Music User Token
- **框架**: MusicKit
- **主要功能**: 搜索、播放、库管理

---

## 4. 数据模型

### 4.1 核心实体

```python
# 歌曲
class Track:
    id: str              # 统一ID (platform:track_id)
    platform: str        # spotify / qq / netease / apple
    platform_id: str     # 平台原始ID
    title: str           # 歌曲名
    artists: List[str]   # 歌手列表
    album: str           # 专辑名
    duration: int        # 时长(秒)
    cover_url: str       # 封面URL
    audio_url: str       # 播放URL
    isrc: str           # 国际标准录音代码

# 歌单
class Playlist:
    id: str
    name: str
    description: str
    tracks: List[Track]
    created_at: datetime
    updated_at: datetime
    platform: str        # 来源平台
    is_synced: bool      # 是否已同步

# 播放记录
class PlayRecord:
    id: str
    track_id: str
    played_at: datetime
    duration_played: int  # 实际播放时长
    source: str           # 来源渠道

# 用户偏好
class UserPreference:
    favorite_artists: List[str]
    favorite_genres: List[str]
    favorite_platforms: List[str]
    listening_habits: Dict  # 按时段统计
```

### 4.2 数据库 Schema

```sql
-- 歌曲库
CREATE TABLE tracks (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    platform_id TEXT NOT NULL,
    title TEXT NOT NULL,
    artists TEXT,  -- JSON array
    album TEXT,
    duration INTEGER,
    cover_url TEXT,
    isrc TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, platform_id)
);

-- 歌单
CREATE TABLE playlists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    platform TEXT,
    is_synced BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 歌单-歌曲关联
CREATE TABLE playlist_tracks (
    playlist_id TEXT,
    track_id TEXT,
    position INTEGER,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, track_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

-- 播放历史
CREATE TABLE play_history (
    id TEXT PRIMARY KEY,
    track_id TEXT NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_played INTEGER,
    source TEXT,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

-- 收藏
CREATE TABLE favorites (
    track_id TEXT PRIMARY KEY,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

-- 用户偏好
CREATE TABLE user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT,  -- JSON
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. 接口设计

### 5.1 统一音乐 API

```python
class UnifiedMusicAPI:
    """统一音乐平台接口"""
    
    # 搜索
    async def search(
        self, 
        query: str, 
        platforms: List[str] = None,
        limit: int = 10
    ) -> List[Track]:
        """跨平台搜索"""
        pass
    
    # 播放控制
    async def play(self, track: Track) -> bool:
        """播放歌曲"""
        pass
    
    async def pause(self) -> bool:
        """暂停"""
        pass
    
    async def next(self) -> Track:
        """下一首"""
        pass
    
    async def previous(self) -> Track:
        """上一首"""
        pass
    
    async def seek(self, position: int) -> bool:
        """跳转到指定位置"""
        pass
    
    # 歌单管理
    async def create_playlist(
        self, 
        name: str, 
        description: str = ""
    ) -> Playlist:
        """创建歌单"""
        pass
    
    async def add_to_playlist(
        self, 
        playlist_id: str, 
        track_ids: List[str]
    ) -> bool:
        """添加歌曲到歌单"""
        pass
    
    async def sync_playlist(
        self, 
        playlist_id: str, 
        target_platform: str
    ) -> bool:
        """同步歌单到其他平台"""
        pass
    
    # 收藏
    async def favorite(self, track_id: str) -> bool:
        """收藏歌曲"""
        pass
    
    async def unfavorite(self, track_id: str) -> bool:
        """取消收藏"""
        pass
    
    # 上传
    async def upload_track(
        self, 
        file_path: str, 
        platform: str
    ) -> Track:
        """上传本地歌曲到平台"""
        pass
    
    # 推荐
    async def get_recommendations(
        self, 
        based_on: str = None,
        limit: int = 10
    ) -> List[Track]:
        """获取推荐歌曲"""
        pass
    
    # 统计
    async def get_stats(
        self, 
        period: str = "week"
    ) -> Dict:
        """获取播放统计"""
        pass
```

### 5.2 指令映射

| 用户指令 | 解析 | API调用 |
|---------|------|---------|
| 听周杰伦的歌 | `search("周杰伦")` | `search(query="周杰伦")` |
| 播放第一首 | `play(0)` | `play(track=tracks[0])` |
| 暂停 | `pause()` | `pause()` |
| 继续 | `resume()` | `resume()` |
| 下一首 | `next()` | `next()` |
| 加入收藏 | `favorite()` | `favorite(current_track)` |
| 创建歌单 叫做 | `create_playlist(name)` | `create_playlist(name)` |
| 每日推荐 | `recommend()` | `get_recommendations()` |
| 听歌统计 | `stats()` | `get_stats()` |

---

## 6. 部署方案

### 6.1 本地部署

```bash
# 克隆项目
git clone https://github.com/DaimaRuge/Jiuge.git
cd Jiuge

# 安装依赖
pip install -r requirements.txt

# 配置
cp config.example.yaml config.yaml
# 编辑 config.yaml 填入各平台 API 凭据

# 运行
python -m jiuge
```

### 6.2 Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "-m", "jiuge"]
```

### 6.3 目录结构

```
Jiuge/
├── docs/                    # 文档
│   ├── PRD-v1.md
│   ├── architecture.md
│   └── api-reference.md
├── src/
│   ├── jiuge/              # 主包
│   │   ├── __init__.py
│   │   ├── agent.py        # Agent 主逻辑
│   │   ├── parser.py       # 指令解析
│   │   ├── adapters/       # 平台适配器
│   │   │   ├── base.py
│   │   │   ├── spotify.py
│   │   │   ├── qqmusic.py
│   │   │   ├── netease.py
│   │   │   └── apple.py
│   │   ├── player/         # 播放器
│   │   │   ├── base.py
│   │   │   └── local.py
│   │   ├── memory/         # 记忆存储
│   │   │   ├── store.py
│   │   │   └── models.py
│   │   ├── ai/             # AI 功能
│   │   │   ├── recommend.py
│   │   │   └── create.py
│   │   └── utils/          # 工具
│   └── tests/              # 测试
├── skill/                   # OpenClaw 技能
│   ├── SKILL.md
│   └── skill.json
├── config/                  # 配置
│   └── config.example.yaml
├── requirements.txt
├── setup.py
└── README.md
```

---

## 7. 开发计划

### Phase 1: MVP (v1.0)
- [ ] 基础架构搭建
- [ ] 网易云音乐适配器
- [ ] 本地播放器
- [ ] 基本指令解析
- [ ] OpenClaw 技能集成

### Phase 2: 多平台 (v2.0)
- [ ] Spotify 适配器
- [ ] QQ音乐适配器
- [ ] Apple Music 适配器
- [ ] 跨平台搜索

### Phase 3: 高级功能 (v3.0)
- [ ] 歌单同步
- [ ] 本地上传
- [ ] 播放统计
- [ ] 智能推荐

### Phase 4: AI 能力 (v4.0)
- [ ] AI 音乐创作
- [ ] 风格迁移
- [ ] 高级推荐算法

### Phase 5: 生态 (v5.0)
- [ ] Web 界面
- [ ] 移动端支持
- [ ] 插件系统

---

## 8. 风险与限制

### 8.1 技术风险
- 部分平台 API 需要申请，可能无法获取
- 第三方 API 稳定性问题
- 版权限制导致部分歌曲无法播放

### 8.2 合规风险
- 需遵守各平台服务条款
- 用户数据隐私保护
- 音乐版权问题

### 8.3 缓解措施
- 优先使用官方 API
- 提供多平台备选方案
- 本地缓存减少 API 调用

---

## 附录

### A. 参考资料
- [Spotify Web API](https://developer.spotify.com/documentation/web-api)
- [Apple Music API](https://developer.apple.com/documentation/applemusicapi)
- [NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi)
- [QQ音乐开放平台](https://y.qq.com/mopen/)

### B. 术语表
- **Agent**: AI 代理，响应用户指令
- **Skill**: OpenClaw 技能模块
- **Adapter**: 平台适配器，封装不同音乐平台 API
- **Memory**: 用户音乐记忆存储
