# Jiuge 音乐智能体

**版本**: v1.0.0
**作者**: DaimaRuge

多平台音乐控制技能，通过 OpenClaw 实现统一的音乐搜索、播放和管理体验。

## 支持平台

| 平台 | 搜索 | 播放 | 歌单 | 收藏 | 上传 |
|------|------|------|------|------|------|
| 网易云音乐 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Spotify | ✅ | ✅ | ✅ | ✅ | ❌ |
| QQ 音乐 | ✅ | ✅ | ✅ | ✅ | ✅ |

## 功能

### 搜索
- 🔍 跨平台歌曲搜索
- 🎤 歌手搜索
- 💿 专辑搜索
- 📋 歌单搜索

### 播放控制
- ▶️ 播放指定歌曲
- ⏸ 暂停/继续播放
- ⏭ 下一首/上一首
- ⏹ 停止播放
- 🔊 音量控制
- 🔀 随机/循环模式

### 歌单管理
- 📋 查看歌单列表
- ➕ 创建歌单
- 🎵 添加歌曲到歌单

### 收藏功能
- ❤️ 收藏/取消收藏歌曲
- 📊 查看收藏列表

### 记忆系统
- 📝 播放历史记录
- 📊 听歌统计
- 💾 数据导出/导入

## 使用

在 OpenClaw 中启用此技能后，可通过以下 channel 发送指令：

### 搜索歌曲
```
听周杰伦的歌
搜索 晴天
找告白气球
```

### 播放控制
```
播放 1        # 播放搜索结果中的第1首
暂停
继续
下一首
上一首
停止
状态          # 查看播放状态
```

### 收藏功能
```
收藏          # 收藏当前歌曲
喜欢
❤️
```

### 推荐和统计
```
推荐          # 获取推荐歌曲
统计          # 查看听歌统计
```

### 帮助
```
帮助
help
?
```

## 配置

### 网易云音乐
```bash
export NETEASE_COOKIE="your_cookie_here"
```

### Spotify
```yaml
platforms:
  spotify:
    client_id: "your_client_id"
    client_secret: "your_client_secret"
    redirect_uri: "http://localhost:8888/callback"
```

### QQ 音乐
```yaml
platforms:
  qqmusic:
    app_id: "your_app_id"
    app_secret: "your_app_secret"
    # 或者使用 Cookie
    cookie: "your_cookie_here"
```

## 安装

```bash
# 从源码安装
git clone https://github.com/DaimaRuge/Jiuge.git
cd Jiuge
pip install -e .

# 或使用 pip
pip install jiuge
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
make test

# 代码检查
make lint
```

## 架构
```
Jiuge/
├── agent.py           # Agent 主逻辑，指令解析与路由
├── service.py         # 统一音乐服务
├── adapters/          # 平台适配器
│   ├── base.py        # 基类定义
│   ├── netease.py     # 网易云音乐
│   ├── spotify.py     # Spotify
│   └── qqmusic.py     # QQ 音乐
├── player/            # 播放器
│   └── local.py       # 本地播放器
└── memory/            # 记忆存储
    └── store.py       # SQLite 存储
```

## 扩展

### 添加新平台
1. 继承 `MusicPlatformAdapter` 基类
2. 实现所有抽象方法
3. 在配置中添加凭据
4. 在 `UnifiedMusicService` 中注册

### 添加新指令
1. 在 `CommandType` 中添加枚举值
2. 在 `CommandParser.PATTERNS` 中添加正则模式
3. 在 `JiugeAgent` 中添加处理方法

## License

MIT License

## 致谢
- [NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi)
- [spotipy](https://github.com/plamere/spotipy)
- OpenClaw
