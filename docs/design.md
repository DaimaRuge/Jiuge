# Jiuge 设计文档

## 1. 项目背景

用户希望通过 OpenClaw 的多个 channel（飞书、Telegram、Discord 等）控制网易云音乐播放，实现：
- 搜索歌曲
- 播放/暂停/切换
- 查看播放状态

## 2. 系统设计

### 2.1 架构图

```
┌──────────────────────────────────────────────────────────────┐
│                      OpenClaw Gateway                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │  Feishu  │  │ Telegram │  │ Discord  │  ...               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                    │
│       │             │             │                           │
│       └─────────────┼─────────────┘                           │
│                     │                                         │
│                     ▼                                         │
│            ┌────────────────┐                                 │
│            │ Message Router │                                 │
│            └───────┬────────┘                                 │
│                    │                                          │
└────────────────────┼──────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                   Music Skill (Jiuge)                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   Command Parser                         │ │
│  │  - 听.*的歌 → search()                                    │ │
│  │  - 播放 \d+ → play(index)                                │ │
│  │  - 暂停 → pause()                                        │ │
│  │  - 继续 → resume()                                       │ │
│  │  - 下一首 → next()                                       │ │
│  │  - 停止 → stop()                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │    Netease API      │  │   Audio Player      │           │
│  │  - search()         │  │  - play(url)        │           │
│  │  - get_song_url()   │  │  - pause()          │           │
│  │  - get_detail()     │  │  - resume()         │           │
│  └─────────────────────┘  └─────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户消息 → OpenClaw Gateway → Music Skill
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              解析指令        调用 API         播放音频
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                              返回结果 → 用户
```

## 3. 核心模块

### 3.1 NeteaseMusic API 封装

负责与网易云音乐 API 交互：

```python
class NeteaseMusic:
    def __init__(self, cookie: str = None)
    def search(self, keywords: str, limit: int = 10) -> List[Dict]
    def get_song_url(self, song_id: int, level: str = "exhigh") -> str
    def get_song_detail(self, song_ids: List[int]) -> List[Dict]
```

### 3.2 MusicPlayer 播放器

负责音频播放控制：

```python
class MusicPlayer:
    def __init__(self)
    def search(self, keywords: str) -> List[Dict]
    def play(self, index: int = None) -> Dict
    def pause(self) -> Dict
    def resume(self) -> Dict
    def next(self) -> Dict
    def prev(self) -> Dict
    def stop(self) -> Dict
    def get_status(self) -> Dict
    def get_playlist(self) -> List[Dict]
```

### 3.3 指令解析

正则表达式匹配用户指令：

| 指令 | 正则 | 函数 |
|------|------|------|
| 搜索 | `^(听\|搜索)\s*(.+)` | `search(keywords)` |
| 播放 | `^播放\s*(\d+)` | `play(index)` |
| 暂停 | `^暂停$` | `pause()` |
| 继续 | `^继续$` | `resume()` |
| 下一首 | `^下一首$` | `next()` |
| 上一首 | `^上一首$` | `prev()` |
| 停止 | `^停止$` | `stop()` |
| 状态 | `^状态$` | `get_status()` |
| 歌单 | `^歌单$` | `get_playlist()` |

## 4. 接口设计

### 4.1 搜索接口

**请求：**
```python
search("周杰伦", limit=10)
```

**响应：**
```json
[
  {
    "id": 1868553,
    "name": "七里香",
    "artist": "周杰伦",
    "album": "七里香",
    "duration": 299,
    "cover": "https://..."
  },
  ...
]
```

### 4.2 播放接口

**请求：**
```python
play(index=0)
```

**响应：**
```json
{
  "success": true,
  "song": {
    "name": "七里香",
    "artist": "周杰伦",
    "album": "七里香",
    "duration": "4:59"
  },
  "state": "playing"
}
```

### 4.3 状态接口

**响应：**
```json
{
  "state": "playing",
  "current_song": {
    "name": "七里香",
    "artist": "周杰伦",
    "position": "1:23",
    "duration": "4:59"
  },
  "playlist_count": 10,
  "current_index": 1
}
```

## 5. 依赖

### 5.1 Python 包

```
NeteaseCloudMusicApi>=0.1.0
ffpyplayer>=4.3.0
```

### 5.2 系统要求

- Python 3.8+
- FFmpeg（ffpyplayer 依赖）

## 6. 配置

### 6.1 环境变量

```bash
# 可选：网易云音乐 Cookie（获取更高音质）
NETEASE_COOKIE=your_cookie_here
```

### 6.2 skill.json 配置

```json
{
  "name": "netease-music",
  "version": "0.1.0",
  "triggers": [
    "听.*的歌",
    "搜索.*歌",
    "播放.*",
    "暂停",
    "继续",
    "下一首",
    "停止"
  ]
}
```

## 7. 测试计划

### 7.1 单元测试

- [ ] API 搜索功能
- [ ] API 获取播放地址
- [ ] 播放器状态切换
- [ ] 指令解析

### 7.2 集成测试

- [ ] 完整播放流程
- [ ] 多 channel 响应
- [ ] 并发控制

## 8. 部署

### 8.1 本地部署

```bash
# 安装依赖
pip install -r requirements.txt

# 复制到 OpenClaw skills 目录
cp -r . ~/.openclaw/skills/jiuge/
```

### 8.2 Docker 部署（未来）

```dockerfile
FROM python:3.11
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## 9. 未来扩展

- 语音控制
- 歌词同步
- 歌单管理
- 推荐系统
- 多音乐平台支持
