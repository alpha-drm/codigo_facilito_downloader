import asyncio
import os
import shutil
from pathlib import Path

from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
)
from rich.text import Text

from ..constants import APP_NAME
from ..helpers import hashify, write_json
from ..logger import logger
from ..models import Quality

TMP_DIR_PATH = Path(APP_NAME) / ".tmp"
# BIN_DIR_PATH = Path(APP_NAME) / ".bin"

TMP_DIR_PATH.mkdir(parents=True, exist_ok=True)
# BIN_DIR_PATH.mkdir(parents=True, exist_ok=True)

RETRIES = 10

console = Console()


def parse_int(value: str | None) -> int | None:
    """Parse a string as integer; return None for NA, empty, or None."""
    if value in ("NA", "", None):
        return None
    return int(float(value))


def parse_ytdlp_progress_line(line: str) -> dict | None:
    """
    Parse a single yt-dlp progress line (pipe-separated:
    downloaded|total|speed|eta|res|vcodec).

    Returns a dict with keys: completed, total, speed, eta, res, vcodec;
    or None if the line does not have exactly 6 fields. Caller can pass
    the result to Progress.update(task, **result).
    """
    parts = line.strip().split("|")
    if len(parts) != 6:
        return None
    downloaded, total_estimate, speed, eta, res, vcodec = parts
    downloaded = parse_int(downloaded)
    total = parse_int(total_estimate)
    if eta in ("NA", "Unknown"):
        eta = "--:--"
    return {
        "completed": downloaded or 0,
        "total": total,
        "speed": speed,
        "eta": eta,
        "res": res,
        "vcodec": vcodec,
    }


async def apply_metadata(path: str, title: str) -> None:
    """Write title, genre and comment metadata into the MP4 file using ffmpeg."""
    temp_path = path.replace(".mp4", "_tmp.mp4")

    with console.status("[bold blue]> Applying metadata...", spinner="bouncingBar"):
        cmd = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-i",
            path,
            "-metadata",
            f"title={title}",
            "-metadata",
            "genre=course",
            "-metadata",
            "comment=Downloaded with https://github.com/ivansaul/codigo_facilito_downloader",
            "-y",
            "-c",
            "copy",
            temp_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()

    if process.returncode != 0:
        logger.error("> Failed to apply metadata")
        return

    os.replace(temp_path, path)


async def download_video(
    url: str,
    path: Path,
    quality: Quality = Quality.P1080,
    **kwargs,
) -> None:
    """
    Download a video from a URL, with Rich progress display and optional metadata.

    Parameters
    ----------
    url : str
        Video stream URL (e.g. M3U8).
    path : Path
        Output file path (.mp4).
    quality : Quality, optional
        Max height for video selection. Default P1080.

    Other Parameters
    ----------------
    cookies : list[dict], optional
        Browser cookies for authenticated streams.
    override : bool, optional
        Overwrite existing file. Default False.
    threads : int, optional
        Concurrent fragments. Default 10.
    progress_str : str, optional
        Prefix for progress line (e.g. "3/10").
    """
    cookies = kwargs.get("cookies", None)
    override = kwargs.get("override", False)
    threads = kwargs.get("threads", 10)
    progress_str = kwargs.get("progress_str", "")
    prefix = f"[{progress_str}]" if progress_str else ""

    path.parent.mkdir(parents=True, exist_ok=True)

    if not override and path.exists():
        logger.info("[green]%s[%s] already exists.[/]", prefix, path.name)
        return

    TMP_COOKIES_PATH = TMP_DIR_PATH / f"{hashify(url)}.json"
    temp_file = str(TMP_DIR_PATH / "%(id)s.%(ext)s")

    write_json(TMP_COOKIES_PATH, cookies)

    progress_template = (
        "%(progress.downloaded_bytes)s|"
        "%(progress.total_bytes_estimate)s|"
        "%(progress._speed_str)s|"
        "%(progress._eta_str)s|"
        "%(info.resolution)s|"
        "%(info.vcodec)s"
    )

    command = [
        "yt-dlp",
        "--newline",
        "--progress-template",
        progress_template,
        "-f",
        f"bv[height<={quality.value}]+ba/b[height<={quality.value}]",
        "--add-headers",
        "Referer: https://codigofacilito.com/",
        "--retries",
        str(RETRIES),
        "--concurrent-fragments",
        str(threads),
        "-o",
        temp_file,
        url,
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )

        progress = Progress(
            TextColumn("[cyan]{task.description}"),
            BarColumn(
                complete_style="bold green",
                pulse_style="bold green",
            ),
            TaskProgressColumn(),
            DownloadColumn(),
            TextColumn("[bold cyan]{task.fields[speed]}"),
            TextColumn("[bold green]{task.fields[eta]}"),
            TextColumn("[bold green]{task.fields[res]}"),
            TextColumn("[bold green]{task.fields[vcodec]}"),
        )

        filename_text = Text(f"{prefix}[{path.name}]", style="bold gray")

        layout = Group(filename_text, progress)

        with Live(layout):
            task = progress.add_task(
                "Downloading...", speed="-", eta="-", res="-", vcodec="-", total=0
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace")
                fields = parse_ytdlp_progress_line(decoded)
                if fields is None:
                    continue
                progress.update(task, **fields)

            await process.wait()

            # force 100%
            task_data = progress.tasks[0]
            if task_data.total:
                progress.update(task, completed=task_data.total)
                progress.update(task, visible=False)

            # Update filename status
            filename_text.plain = f"{prefix}[{path.name}] >>> Done!"
            filename_text.stylize("bold green")

            if process.returncode != 0:
                raise RuntimeError("> Download failed")

        downloaded_file = next(TMP_DIR_PATH.glob("*.mp4"))
        shutil.move(downloaded_file, path)

        await asyncio.sleep(2)

        output_file = str(path)
        title = os.path.splitext(os.path.basename(path))[0]
        await apply_metadata(output_file, title)

    except RuntimeError as e:
        logger.error(str(e))
    except Exception:
        logger.exception(f"Error downloading [{path.name}]")
        import traceback

        traceback.print_exc()

    finally:
        if TMP_COOKIES_PATH.exists():
            TMP_COOKIES_PATH.unlink()
