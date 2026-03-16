from pathlib import Path

from playwright.async_api import BrowserContext

from ..collectors import fetch_video
from ..models import TypeUnit, Unit
from ..utils import save_page
from .video import download_video


async def download_unit(
    context: BrowserContext, unit: Unit, path: Path, **kwargs
) -> None:
    """
    Download a single unit: video (via yt-dlp) or lecture/quiz page (as MHTML).

    Parameters
    ----------
    context : BrowserContext
        Playwright browser context (cookies for video, page capture for MHTML).
    unit : Unit
        Unit model with type, url, name.
    path : Path
        Output path (e.g. .mp4 for video, .mhtml for lecture/quiz).

    Other Parameters
    ----------------
    quality : Quality, optional
        Video quality. Default from caller.
    override : bool, optional
        Overwrite existing file. Default False.
    threads : int, optional
        Concurrent fragments for video. Default 10.
    progress_str : str, optional
        Prefix string for progress display (e.g. "3/10").
    """

    if unit.type == TypeUnit.VIDEO:
        video = await fetch_video(context, unit.url)
        await download_video(
            video.url,
            path=path,
            cookies=await context.cookies(),
            **kwargs,
        )  # type: ignore

    else:
        await save_page(context, unit.url, path)
