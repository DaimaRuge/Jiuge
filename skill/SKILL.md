# Jiuge Skill

网易云音乐控制技能，通过 OpenClaw 实现搜索和播放网易云音乐。

## 功能

- 🔍 搜索歌曲（歌手、歌名）
- ▶️ 播放指定歌曲
- ⏸ 暂停/继续播放
- ⏭ 下一首/上一首
- ⏹ 停止播放
- 📋 查看播放列表
- ℹ️ 查看播放状态

## 使用

在 OpenClaw 中启用此技能后，可通过以下 channel 发送指令：

### 搜索歌曲
```
听周杰伦的歌
搜索 晴天
```

### 播放控制
```
播放 1        # 播放搜索结果中的第1首
暂停
继续
下一首
上一首
停止
状态
歌单
```

## 配置

可选：设置网易云音乐 Cookie 以获取更高音质

```bash
export NETEASE_COOKIE="your_cookie_here"
```

## 安装

```bash
pip install -r requirements.txt
```

## License

MIT
