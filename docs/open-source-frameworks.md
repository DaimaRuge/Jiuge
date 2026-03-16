# Jiuge 开源框架参考

本文档记录了 Jiuge 项目使用的开源框架和参考资料。

---

## 1. 音乐平台 API

### 1.1 网易云音乐

| 项目 | 地址 | 说明 |
|------|------|------|
| NeteaseCloudMusicApi | https://github.com/Binaryify/NeteaseCloudMusicApi | Node.js 原版 API |
| NeteaseCloudMusicApi (Python) | https://pypi.org/project/NeteaseCloudMusicApi/ | Python SDK |

**安装：**
```bash
pip install NeteaseCloudMusicApi
```

**功能：**
- 搜索（歌曲/专辑/歌手/歌单）
- 获取播放 URL
- 歌单管理
- 云盘上传

---

### 1.2 Spotify

| 项目 | 地址 | 说明 |
|------|------|------|
| spotipy | https://github.com/plamere/spotipy | 官方 Python SDK |

**安装：**
```bash
pip install spotipy
```

**功能：**
- 搜索
- 音频特征分析 (danceability, energy, tempo...)
- 推荐系统
- 播放列表管理
- 用户收藏

**高级功能：**
```python
# 获取音频特征
features = sp.audio_features(track_id)
# danceability, energy, valence, tempo, loudness...

# 获取推荐
recommendations = sp.recommendations(
    seed_tracks=["track_id"],
    limit=10
)
```

---

### 1.3 QQ 音乐

| 项目 | 地址 | 说明 |
|------|------|------|
| QQ 音乐开放平台 | https://y.qq.com/mopen/ | 官方开放平台 |

**功能：**
- 音乐搜索
- 歌曲播放
- 歌单管理
- 云盘上传

**注意：** 需要申请开放平台权限

---

### 1.4 Apple Music

| 项目 | 地址 | 说明 |
|------|------|------|
| apple-music-python | https://pypi.org/project/apple-music-python/ | Python 封装 |
| MusicKit JS | https://developer.apple.com/documentation/musickitjs | 官方 JS SDK |
| Apple Music API | https://developer.apple.com/documentation/applemusicapi | 官方 REST API |

**安装：**
```bash
pip install apple-music-python
```

**功能：**
- 搜索
- 歌单管理
- 收藏管理

**注意：**
- 需要 Apple 开发者账号
- Developer Token 需要 JWT 生成
- User Token 需要通过 MusicKit JS 获取

---

## 2. 音乐元数据

### 2.1 MusicBrainz

| 项目 | 地址 | 说明 |
|------|------|------|
| musicbrainzngs | https://pypi.org/project/musicbrainzngs/ | Python SDK |

**安装：**
```bash
pip install musicbrainzngs
```

**功能：**
- 查询歌曲元数据
- 获取专辑信息
- 艺术家信息
- 封面图片

**示例：**
```python
import musicbrainzngs

musicbrainzngs.set_useragent("Jiuge", "1.0")

# 搜索歌曲
result = musicbrainzngs.search_recordings(
    query="七里香 周杰伦",
    limit=10
)

# 获取封面
cover = musicbrainzngs.get_image_list(release_id)
```

---

### 2.2 音频元数据解析

| 项目 | 地址 | 说明 |
|------|------|------|
| mutagen | https://mutagen.readthedocs.io/ | 元数据解析 |
| pydub | https://github.com/jiaaro/pydub | 音频处理 |

**安装：**
```bash
pip install mutagen pydub
```

**支持格式：**
- MP3 (ID3v1/ID3v2)
- FLAC (Vorbis Comment)
- M4A (iTunes Metadata)
- WAV (RIFF INFO)
- OGG (Vorbis Comment)

**示例：**
```python
from mutagen.mp3 import MP3

audio = MP3("song.mp3")
print(audio["TIT2"])  # 标题
print(audio["TPE1"])  # 艺术家
print(audio.info.length)  # 时长
```

---

## 3. 推荐算法

### 3.1 协同过滤

| 项目 | 地址 | 说明 |
|------|------|------|
| Implicit | https://github.com/benfred/implicit | ALS 协同过滤 |
| LightFM | https://github.com/lyst/lightfm | 矩阵分解 |

**安装：**
```bash
pip install implicit lightfm
```

**Implicit 示例：**
```python
from implicit.als import AlternatingLeastSquares

model = AlternatingLeastSquares(factors=64)
model.fit(user_item_matrix)

# 推荐给用户
ids, scores = model.recommend(user_id, user_items, N=10)
```

---

### 3.2 内容推荐

**特征：**
- 音频特征 (Spotify Audio Features)
- 歌曲元数据 (流派、年代、BPM)
- 歌词分析 (情感、主题)

**算法：**
- KNN (K-Nearest Neighbors)
- 余弦相似度
- 聚类

---

### 3.3 开源推荐项目

| 项目 | 地址 | 说明 |
|------|------|------|
| Anagnorisis | https://github.com/PantelisKsim /anagnorisis | 本地推荐系统 |
| Acai (Open MRS) | https://github.com/BerryAI/Acai | 开源音乐推荐 |
| Flask Music Recommender | GitHub 搜索 | Flask + Vue.js |

---

## 4. Web 框架

### 4.1 FastAPI

| 项目 | 地址 | 说明 |
|------|------|------|
| FastAPI | https://fastapi.tiangolo.com/ | 现代异步框架 |

**安装：**
```bash
pip install fastapi uvicorn websockets
```

**示例：**
```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.get("/api/v1/search")
async def search(q: str):
    return {"results": [...]}

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

---

## 5. 参考资料

### 5.1 官方文档

| 平台 | 文档地址 |
|------|---------|
| Spotify Web API | https://developer.spotify.com/documentation/web-api |
| Apple Music API | https://developer.apple.com/documentation/applemusicapi |
| MusicBrainz API | https://musicbrainz.org/doc/MusicBrainz_API |
| QQ 音乐开放平台 | https://y.qq.com/mopen/ |

### 5.2 教程和文章

- [Building a Music Recommender System](https://medium.com/@...)
- [Collaborative Filtering in Python](https://realpython.com/...)
- [Spotify Audio Features Analysis](https://developer.spotify.com/documentation/web-api/reference/#/operations/get-several-audio-features)

---

## 6. 依赖版本

详见 [requirements.txt](../requirements.txt)

核心依赖：
- Python >= 3.11
- NeteaseCloudMusicApi >= 0.1.0
- spotipy >= 2.23.0
- musicbrainzngs >= 0.7.1
- implicit >= 0.7.2
- FastAPI >= 0.100.0
