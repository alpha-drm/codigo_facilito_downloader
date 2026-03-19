import asyncio
import functools
from pathlib import Path

from colorama import Fore, Style
from playwright.async_api import BrowserContext, Page
from pyfiglet import Figlet
from rich.console import Console

from .errors import UnitError
from .helpers import read_json, write_json
from .logger import logger
from .models import TypeUnit


def login_required(func):
    """Decorator that ensures the method is called on an authenticated
    AsyncFacilito instance."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        from .async_api import AsyncFacilito

        self = args[0]
        if not isinstance(self, AsyncFacilito):
            logger.error(f"{login_required.__name__} can only decorate Facilito class.")
            return
        if not self.authenticated:
            logger.error("Login first!")
            return
        return await func(*args, **kwargs)

    return wrapper


def try_except_request(func):
    """Decorator that catches exceptions in async methods and logs them;
    returns None on exception."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if str(e):
                logger.exception(e)
        return

    return wrapper


async def save_state(context: BrowserContext, path: Path | None = None) -> None:
    """Persist browser cookies to a JSON file at the given path."""
    if path is None:
        path = Path.cwd() / "state.json"

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    cookies = await context.cookies()
    write_json(path, cookies)  # type: ignore


async def load_state(context: BrowserContext, path: Path) -> None:
    """Load cookies from a JSON file into the browser context.
    No-op if the file does not exist."""
    if not path.exists():
        return
    cookies = read_json(path)
    await context.add_cookies(cookies)  # type: ignore


async def progressive_scroll(page: Page, delay: float = 0.1, steps: int = 400) -> None:
    """Scroll the page to the bottom in steps until no new content loads
    (e.g. for lazy-loaded content)."""
    last_height = await page.evaluate("document.body.scrollHeight")

    while True:
        await page.mouse.wheel(0, steps)
        await asyncio.sleep(delay)

        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


async def open_accordions(page: Page) -> None:
    """Expand all collapsible accordion headers on the page."""
    headers = page.locator(".collapsible-header")
    count = await headers.count()

    for i in range(count):
        header = headers.nth(i)

        expanded = await header.get_attribute("aria-expanded")

        if expanded != "true":
            try:
                await header.click()
                await page.wait_for_timeout(1000)
            except Exception:
                pass


@try_except_request
async def save_page(
    context: BrowserContext,
    src: str | Page,
    path: str | Path = "source.mhtml",
    **kwargs,
) -> None:
    """Save a page as MHTML: scroll, expand accordions, then capture snapshot.
    Accepts URL (str) or Page."""
    EXCEPTION = Exception(f"Error saving page as mhtml {path}")

    progress_str = kwargs.get("progress_str", "")
    prefix = progress_str if progress_str else ""
    override = kwargs.get("override", False)

    if not override and path.exists():
        logger.info("[green][%s][%s] already exists.[/]", prefix, path.name)
        return

    try:
        console = Console()
        with console.status(
            "[green]Saving page...[/]\n", spinner="bouncingBar", spinner_style="green"
        ):
            if isinstance(src, str):
                page = await context.new_page()
                await page.goto(src, wait_until="networkidle")
            else:
                page = src

            await page.wait_for_timeout(2000)
            await progressive_scroll(page)
            await open_accordions(page)
            await page.wait_for_timeout(1000)

            # Fix Material Icons
            await page.evaluate("""
                document.querySelectorAll('.material-icons').forEach(el => {
                    const icon = el.textContent.trim();

                    if (icon === 'done_all') {
                        el.textContent = '✔✔';
                        el.style.fontFamily = 'inherit';
                        el.style.fontSize = '16px';
                    } else {
                        el.textContent = '';
                    }
                });
            """)

            await page.wait_for_timeout(3000)

            client = await page.context.new_cdp_session(page)
            response = await client.send("Page.captureSnapshot")

            with open(path, "w", encoding="utf-8", newline="\n") as file:
                file.write(response["data"])

        if prefix:
            logger.info(f"[green][{prefix}][{path.name}] >>> Done!")

    except Exception:
        raise EXCEPTION

    finally:
        if isinstance(src, str):
            await page.close()


def is_video(url: str) -> bool:
    """
    Check if a URL is a video.

    :param str url: URL to check.
    :return bool: True if the URL is a video, False otherwise.

    Example
    -------
    >>> is_video("https: ..../videos/...")
    True
    """
    return "/videos/" in url


def is_lecture(url: str) -> bool:
    """
    Check if a URL is a lecture.

    :param str url: URL to check.
    :return bool: True if the URL is a lecture, False otherwise.

    Example
    -------
    >>> is_lecture("https: ..../articulos/...")
    True
    """
    return "/articulos/" in url


def is_course(url: str) -> bool:
    """
    Check if a URL is a course.

    :param str url: URL to check.
    :return bool: True if the URL is a course, False otherwise.

    Example
    -------
    >>> is_course("https: ..../cursos/...")
    True
    """
    return "/cursos/" in url


def is_bootcamp(url: str) -> bool:
    """
    Check if a URL is a bootcamp.

    :param str url: URL to check.
    :return bool: True if the URL is a bootcamp, False otherwise.

    Example
    -------
    >>> is_bootcamp("https://codigofacilito.com/programas/...")
    True
    """
    return "/programas/" in url


def is_quiz(url: str) -> bool:
    """
    Check if a URL is a quiz.

    :param str url: URL to check.
    :return bool: True if the URL is a quiz, False otherwise.

    Example
    -------
    >>> is_quiz("https: ..../quizzes/...")
    True
    """
    return "/quizzes/" in url


def get_unit_type(url: str) -> TypeUnit:
    """
    Get the type of a unit from its URL.

    :param str url: URL of the unit.
    :return TypeUnit: Type of the unit.
    :raises UnitError: If the unit type is not recognized.

    Example
    -------
    >>> get_unit_type("https: ..../videos/...")
    TypeUnit.VIDEO
    """

    if is_video(url):
        return TypeUnit.VIDEO

    if is_lecture(url):
        return TypeUnit.LECTURE

    if is_quiz(url):
        return TypeUnit.QUIZ

    raise UnitError()


def normalize_cookies(cookies: list[dict]) -> list[dict]:
    """
    Normalize cookies to a common format.

    :param list[dict] cookies: List of cookies to normalize.
    :return list[dict]: Normalized list of cookies.
    """
    import copy

    same_site_valid_values = {"Lax", "Strict", "None"}
    same_site_key = "sameSite"

    cookies = copy.deepcopy(cookies)
    for cookie in cookies:
        same_site = cookie.get(same_site_key) or "None"
        same_site = same_site.replace("unspecified", "Lax").capitalize()
        same_site = same_site if same_site in same_site_valid_values else "None"
        cookie[same_site_key] = same_site

    return cookies


def banner() -> None:
    """Print the CLI banner (ASCII art title) to stdout."""
    console = Console()
    print()

    title = "Coco Downloader"
    width = console.size.width
    f = Figlet(font="ansi_shadow", width=width, justify="center")
    ascii_text = f.renderText(title)
    print(Fore.GREEN + Style.BRIGHT + ascii_text)
