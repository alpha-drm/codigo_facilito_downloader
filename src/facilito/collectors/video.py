import re

from playwright.async_api import BrowserContext

from ..errors import VideoError
from ..models import Video
from ..utils import is_video


async def fetch_video(context: BrowserContext, url: str) -> Video:
    """
    Fetch the M3U8 stream URL from a video page (used by the video downloader).

    Parameters
    ----------
    context : BrowserContext
        Playwright browser context.
    url : str
        Full URL of the video page.

    Returns
    -------
    Video
        Video model with the extracted stream URL.

    Raises
    ------
    VideoError
        If the URL is not a video page or videoUrl cannot be found in the page.
    """
    M3U8_PATTERN = r'videoUrl\s*=\s*"([^"]+)"'

    if not is_video(url):
        raise VideoError()

    page = await context.new_page()

    try:
        await page.goto(url, wait_until="domcontentloaded")

        html = await page.content()
        m3u8_urls = re.findall(M3U8_PATTERN, html)

        if not m3u8_urls:
            raise VideoError("videoUrl not found in page")

        return Video(url=m3u8_urls[0])

    except Exception as e:
        raise VideoError() from e

    finally:
        await page.close()
