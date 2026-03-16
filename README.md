# 🎵 Jiuge - OpenClaw 网易云音乐控制方案

基于 OpenClaw 的网易云音乐控制代理，通过飞书、Telegram 等 channel 实现音乐搜索与播放控制。

## 项目概述

Jiuge 是一个集成到 OpenClaw 的音乐控制代理，允许用户通过聊天指令搜索和播放网易云音乐。

### 核心功能

| 功能 | 指令示例 | 说明 |
|------|---------|------|
| 🔍 搜索 | `听周杰伦的歌` | 搜索歌曲并显示列表 |
| ▶️ 播放 | `播放 1` | 播放列表中第1首 |
| ⏸️ 暂停 | `暂停` | 暂停当前播放 |
| ▶️ 继续 | `继续` | 继续播放 |
| ⏭️ 下一首 | `下一首` | 播放下一首 |
| ⏮️ 上一首 | `上一首` | 播放上一首 |
| ⏹️ 停止 | `停止` | 停止播放 |
| ℹ️ 状态 | `状态` | 查看当前播放状态 |
| 📋 歌单 | `歌单` | 查看播放列表 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                          │
├─────────────────────────────────────────────────────────────┤
│  飞书/Telegram/Discord ──► Message Handler ──► Music Skill   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Music Skill (Python)                       │
├─────────────────────────────────────────────────────────────┤
│  • search(keywords)     → 返回歌单列表                        │
│  • play(song_id)        → 播放指定歌曲                        │
│  • pause()              → 暂停                               │
│  • resume()             → 继续播放                           │
│  • next() / prev()      → 下一首/上一首                       │
│  • stop()               → 停止播放                           │
│  • status()             → 当前播放状态                        │
│  • playlist()           → 显示当前歌单                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              NeteaseCloudMusicApi + Audio Player             │
└─────────────────────────────────────────────────────────────┘
```

---

## 技术选型

| 组件 | 选择 | 说明 |
|------|------|------|
| API SDK | `NeteaseCloudMusicApi` (PyPI) | Python SDK，封装了200+接口 |
| 音频播放 | `ffpyplayer` | 本地音频播放 |
| 架构 | OpenClaw Skill | 作为技能集成到 OpenClaw |

---

## 核心 API

基于 [NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi) 封装：

```python
from NeteaseCloudMusic import NeteaseCloudMusicApi

api = NeteaseCloudMusicApi()

# 搜索歌曲
result = api.request("search", {"keywords": "周杰伦", "limit": 10})

# 获取歌曲播放 URL
result = api.request("song_url_v1", {"id": 33894312, "level": "exhigh"})

# 获取歌曲详情
result = api.request("song_detail", {"ids": "33894312"})
```

### 主要 API 接口

| 接口 | 说明 | 参数 |
|------|------|------|
| `/search` | 搜索歌曲 | `keywords`, `limit`, `type` |
| `/song/url/v1` | 获取播放地址 | `id`, `level` |
| `/song/detail` | 获取歌曲详情 | `ids` |

---

## 交互示例

```
用户: 听周杰伦的歌
Bot: 🎵 搜索到以下歌曲：
     1. 七里香 - 周杰伦 (4:59)
     2. 晴天 - 周杰伦 (4:29)
     3. 简单爱 - 周杰伦 (4:30)
     4. 稻香 - 周杰伦 (3:43)
     5. 夜曲 - 周杰伦 (4:47)
     ...
     回复序号播放，如"播放 1"

用户: 播放 1
Bot: ▶️ 正在播放：七里香 - 周杰伦
     [⏸暂停] [⏭下一首] [⏹停止]

用户: 暂停
Bot: ⏸️ 已暂停：七里香

用户: 继续
Bot: ▶️ 继续播放：七里香

用户: 下一首
Bot: ▶️ 正在播放：晴天 - 周杰伦

用户: 状态
Bot: 🎵 当前播放：晴天 - 周杰伦
     进度：1:23 / 4:29
     状态：播放中
```

---

## 项目结构

```
Jiuge/
├── docs/
│   └── design.md          # 本设计文档
├── src/
│   ├── netease_api.py     # 网易云 API 封装
│   ├── music_player.py    # 播放器核心
│   └── __init__.py        # 模块入口
├── skill/
│   ├── SKILL.md           # 技能说明
│   └── skill.json         # 技能配置
├── requirements.txt       # Python 依赖
└── README.md              # 项目说明
```

---

## 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

依赖包：
- `NeteaseCloudMusicApi>=0.1.0` - 网易云 API SDK
- `ffpyplayer>=4.3.0` - 音频播放器

### 2. 可选配置

设置网易云音乐 Cookie 以获取更高音质：

```bash
export NETEASE_COOKIE="your_netease_cookie"
```

### 3. 集成到 OpenClaw

将 `skill/` 目录复制到 OpenClaw 的 skills 目录：

```bash
cp -r skill/ ~/.openclaw/skills/netease-music/
```

---

## 模块说明

### netease_api.py - API 封装

```python
class NeteaseMusic:
    """网易云音乐 API 客户端"""
    
    def search(self, keywords: str, limit: int = 10) -> List[Dict]
        """搜索歌曲"""
    
    def get_song_url(self, song_id: int, level: str = "exhigh") -> Optional[str]
        """获取歌曲播放地址"""
    
    def get_song_detail(self, song_ids: List[int]) -> List[Dict]
        """获取歌曲详情"""
```

### music_player.py - 播放器

```python
class MusicPlayer:
    """音乐播放器"""
    
    def search(self, keywords: str) -> List[Dict]
        """搜索并添加到播放列表"""
    
    def play(self, index: int = None) -> Dict
        """播放指定歌曲"""
    
    def pause(self) -> Dict
        """暂停播放"""
    
    def resume(self) -> Dict
        """继续播放"""
    
    def next(self) -> Dict
        """下一首"""
    
    def stop(self) -> Dict
        """停止播放"""
    
    def get_status(self) -> Dict
        """获取播放状态"""
```

---

## 扩展功能（未来）

- [ ] 语音控制支持
- [ ] 歌词同步显示
- [ ] 收藏歌单管理
- [ ] 推荐歌曲
- [ ] 多房间播放
- [ ] Spotify/Apple Music 支持

---

## 相关链接

- [NeteaseCloudMusicApi (Node.js)](https://github.com/Binaryify/NeteaseCloudMusicApi)
- [NeteaseCloudMusicApi (Python SDK)](https://pypi.org/project/NeteaseCloudMusicApi/)
- [OpenClaw](https://github.com/openclaw/openclaw)
- [ffpyplayer](https://pypi.org/project/ffpyplayer/)

---

## License

MIT

## Author

DaimaRuge
