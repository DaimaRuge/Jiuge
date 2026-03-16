"""
Jiuge 命令行工具
"""

import typer
import asyncio
from typing import Optional, List
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="jiuge",
    help="🎵 Jiuge - 个人音乐 AI 助手",
    add_completion=False
)
console = Console()


class Platform(str, Enum):
    """音乐平台"""
    NETEASE = "netease"
    SPOTIFY = "spotify"
    QQMUSIC = "qqmusic"
    APPLE = "apple"


# === 搜索命令 ===

@app.command()
def search(
    query: str = typer.Argument(..., help="搜索关键词"),
    platforms: str = typer.Option("netease", "--platforms", "-p", help="平台，逗号分隔"),
    limit: int = typer.Option(10, "--limit", "-l", help="返回数量")
):
    """搜索歌曲"""
    async def _search():
        from jiuge.service import UnifiedMusicService
        from jiuge.memory.store import MusicMemoryStore
        
        config = _load_config()
        service = UnifiedMusicService(config.get("platforms", {}))
        
        platform_list = [p.strip() for p in platforms.split(",")]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"搜索中: {query}...", total=None)
            results = await service.search(query, platform_list, limit)
        
        if not results:
            console.print("[yellow]没有找到相关歌曲[/yellow]")
            return
        
        table = Table(title=f"搜索结果: {query}")
        table.add_column("#", style="cyan", width=3)
        table.add_column("歌曲", style="white")
        table.add_column("歌手", style="green")
        table.add_column("专辑", style="blue")
        table.add_column("时长", style="yellow")
        table.add_column("平台", style="magenta")
        
        for i, track in enumerate(results, 1):
            table.add_row(
                str(i),
                track.title,
                ", ".join(track.artists[:2]),
                track.album,
                _format_duration(track.duration),
                track.platform
            )
        
        console.print(table)
        console.print(f"\n[dim]使用 'jiuge play <序号>' 播放歌曲[/dim]")
    
    asyncio.run(_search())


# === 播放命令 ===

@app.command()
def play(
    track_id: str = typer.Argument(..., help="歌曲 ID 或序号")
):
    """播放歌曲"""
    async def _play():
        from jiuge.service import UnifiedMusicService
        
        config = _load_config()
        service = UnifiedMusicService(config.get("platforms", {}))
        
        # 如果是数字，尝试从最近搜索结果播放
        if track_id.isdigit():
            index = int(track_id) - 1
            result = await service.play(index)
        else:
            # 直接使用 ID
            console.print("[yellow]暂不支持直接 ID 播放，请先搜索[/yellow]")
            return
        
        if result:
            track = result
            console.print(Panel(
                f"[bold]{track['title']}[/bold]\n"
                f"[green]{', '.join(track['artists'])}[/green]\n"
                f"[blue]{track['album']}[/blue]",
                title="▶️ 正在播放",
                border_style="green"
            ))
        else:
            console.print("[red]播放失败[/red]")
    
    asyncio.run(_play())


# === 控制命令 ===

@app.command()
def pause():
    """暂停播放"""
    async def _pause():
        from jiuge.service import UnifiedMusicService
        
        config = _load_config()
        service = UnifiedMusicService(config.get("platforms", {}))
        await service.pause()
        console.print("[yellow]⏸️ 已暂停[/yellow]")
    
    asyncio.run(_pause())


@app.command()
def resume():
    """继续播放"""
    async def _resume():
        from jiuge.service import UnifiedMusicService
        
        config = _load_config()
        service = UnifiedMusicService(config.get("platforms", {}))
        await service.resume()
        console.print("[green]▶️ 继续播放[/green]")
    
    asyncio.run(_resume())


@app.command()
def next():
    """下一首"""
    async def _next():
        from jiuge.service import UnifiedMusicService
        
        config = _load_config()
        service = UnifiedMusicService(config.get("platforms", {}))
        track = await service.next()
        
        if track:
            console.print(f"[green]⏭️ 下一首: {track['title']} - {', '.join(track['artists'])}[/green]")
        else:
            console.print("[yellow]已经是最后一首了[/yellow]")
    
    asyncio.run(_next())


@app.command()
def stop():
    """停止播放"""
    async def _stop():
        from jiuge.service import UnifiedMusicService
        
        config = _load_config()
        service = UnifiedMusicService(config.get("platforms", {}))
        await service.stop()
        console.print("[red]⏹️ 已停止播放[/red]")
    
    asyncio.run(_stop())


@app.command()
def status():
    """查看播放状态"""
    async def _status():
        from jiuge.service import UnifiedMusicService
        
        config = _load_config()
        service = UnifiedMusicService(config.get("platforms", {}))
        status = await service.get_status()
        
        if status["state"] == "stopped":
            console.print("[dim]当前没有播放[/dim]")
            return
        
        track = status.get("current_track")
        if track:
            console.print(Panel(
                f"[bold]{track['title']}[/bold]\n"
                f"[green]{', '.join(track['artists'])}[/green]\n"
                f"[blue]{track['album']}[/blue]\n\n"
                f"进度: {track.get('position', '0:00')} / {track.get('duration', '0:00')}\n"
                f"状态: {status['state']}",
                title="🎵 当前播放",
                border_style="cyan"
            ))
    
    asyncio.run(_status())


# === 歌单命令 ===

playlist_app = typer.Typer(help="歌单管理")
app.add_typer(playlist_app, name="playlist")


@playlist_app.command("list")
def list_playlists():
    """列出歌单"""
    console.print("[yellow]歌单列表功能开发中...[/yellow]")


@playlist_app.command("create")
def create_playlist(
    name: str = typer.Argument(..., help="歌单名称"),
    description: str = typer.Option("", "--desc", "-d", help="歌单描述")
):
    """创建歌单"""
    console.print(f"[green]创建歌单: {name}[/green]")


@playlist_app.command("sync")
def sync_playlist(
    source: str = typer.Argument(..., help="源歌单 ID"),
    target: str = typer.Option(..., "--to", "-t", help="目标平台")
):
    """同步歌单到其他平台"""
    console.print(f"[yellow]同步歌单 {source} 到 {target}...[/yellow]")


# === 推荐命令 ===

@app.command()
def recommend(
    limit: int = typer.Option(10, "--limit", "-l", help="推荐数量")
):
    """获取推荐歌曲"""
    async def _recommend():
        from jiuge.service import UnifiedMusicService
        
        config = _load_config()
        service = UnifiedMusicService(config.get("platforms", {}))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("生成推荐中...", total=None)
            results = await service.get_recommendations(limit)
        
        if not results:
            console.print("[yellow]暂无推荐[/yellow]")
            return
        
        table = Table(title="🎵 为你推荐")
        table.add_column("#", style="cyan", width=3)
        table.add_column("歌曲", style="white")
        table.add_column("歌手", style="green")
        table.add_column("平台", style="magenta")
        
        for i, track in enumerate(results, 1):
            table.add_row(
                str(i),
                track.title,
                ", ".join(track.artists[:2]),
                track.platform
            )
        
        console.print(table)
    
    asyncio.run(_recommend())


# === 统计命令 ===

@app.command()
def stats(
    period: str = typer.Option("week", "--period", "-p", help="统计周期: day/week/month/year")
):
    """查看听歌统计"""
    from jiuge.memory.store import MusicMemoryStore
    
    store = MusicMemoryStore()
    stats = store.get_stats(period)
    
    console.print(Panel(
        f"[bold]播放次数:[/bold] {stats['total_plays']}\n"
        f"[bold]听过歌曲:[/bold] {stats['unique_tracks']} 首",
        title=f"📊 最近{period}统计",
        border_style="blue"
    ))
    
    if stats['top_tracks']:
        table = Table(title="🔥 热门歌曲")
        table.add_column("#", width=3)
        table.add_column("歌曲")
        table.add_column("播放次数")
        
        for i, track in enumerate(stats['top_tracks'][:5], 1):
            table.add_row(
                str(i),
                track.get('title', 'Unknown'),
                str(track.get('play_count', 0))
            )
        
        console.print(table)


# === 上传命令 ===

@app.command()
def upload(
    directory: str = typer.Argument(..., help="音乐目录"),
    platform: Platform = typer.Option(Platform.NETEASE, "--platform", "-p", help="目标平台")
):
    """上传本地音乐"""
    console.print(f"[yellow]上传 {directory} 到 {platform.value}...[/yellow]")
    console.print("[dim]上传功能开发中...[/dim]")


# === 配置命令 ===

config_app = typer.Typer(help="配置管理")
app.add_typer(config_app, name="config")


@config_app.command("set")
def set_config(
    key: str = typer.Argument(..., help="配置键"),
    value: str = typer.Argument(..., help="配置值")
):
    """设置配置"""
    console.print(f"[green]设置 {key} = {value}[/green]")


@config_app.command("get")
def get_config(
    key: str = typer.Argument(..., help="配置键")
):
    """获取配置"""
    console.print(f"[dim]{key} = ...[/dim]")


# === 工具函数 ===

def _load_config() -> dict:
    """加载配置"""
    import yaml
    from pathlib import Path
    
    config_path = Path.home() / ".jiuge" / "config.yaml"
    
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    return {}


def _format_duration(seconds: int) -> str:
    """格式化时长"""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"


if __name__ == "__main__":
    app()
