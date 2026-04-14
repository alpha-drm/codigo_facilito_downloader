from pathlib import Path

from playwright.async_api import BrowserContext, Page, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

from . import collectors
from .constants import BASE_URL, LOGIN_URL, SESSION_FILE
from .errors import LoginError
from .helpers import get_cached_bootcamp, get_cached_course, read_json
from .logger import logger
from .utils import (
    load_state,
    login_required,
    normalize_cookies,
    save_state,
    try_except_request,
)


class AsyncFacilito:
    """
    Async client to interact with Codigo Facilito.

    Use as a context manager to manage browser lifecycle. After entering the context,
    call login() (or set_cookies()) to authenticate, then use fetch_* and download()
    as needed.

    Example
    -------
    >>> async with AsyncFacilito(headless=True) as client:
    ...     await client.login()
    ...     course = await client.fetch_course("https://codigofacilito.com/cursos/...")
    ...     await client.download("https://codigofacilito.com/cursos/...")
    """

    def __init__(self, headless: bool = True) -> None:
        """
        Initialize the client.

        Parameters
        ----------
        headless : bool, optional
            If True, run the browser in headless mode. Default is True.
        """
        self.headless = headless
        self.authenticated = False
        self._playwright = None
        self._browser = None
        self._context = None

    async def __aenter__(self) -> "AsyncFacilito":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)

        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self._context = await self._browser.new_context(
            user_agent=user_agent,
            java_script_enabled=True,
            viewport={"width": 1280, "height": 800},
        )

        stealth = Stealth(init_scripts_only=True)

        await stealth.apply_stealth_async(self._context)

        await load_state(self._context, SESSION_FILE)

        await self._set_profile()

        return self

    async def __aexit__(
        self, exc_type: type | None, exc: BaseException | None, tb: object
    ) -> None:
        """Close browser and release resources."""
        await self._context.close()
        await self._browser.close()
        await self._playwright.stop()

    @property
    def context(self) -> BrowserContext:
        """Playwright browser context (e.g. for passing to collectors/downloaders)."""
        return self._context

    @property
    async def page(self) -> Page:
        """Create and return a new browser page."""
        return await self._context.new_page()

    @try_except_request
    async def login(self) -> None:
        logger.info("Please login, in the opened browser")
        logger.info("You have to login manually, you have 2 minutes to do it")

        SELECTOR = "h1.h1.f-text-34"
        page = await self.page

        try:
            await page.goto(LOGIN_URL, wait_until="domcontentloaded")

            await page.wait_for_selector(
                SELECTOR,
                timeout=2 * 60 * 1000,
            )

            self.authenticated = True
            await save_state(self.context, SESSION_FILE)
            logger.info("Logged in successfully")

        except PlaywrightTimeoutError:
            logger.error("Login timed out.")
            raise LoginError("Login timed out.")
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            raise LoginError()
        finally:
            await page.close()

    @try_except_request
    async def logout(self) -> None:
        """Remove saved session (cookies) from disk. Does not require prior login."""
        SESSION_FILE.unlink(missing_ok=True)
        logger.info("Logged out successfully")

    @try_except_request
    @login_required
    async def fetch_unit(self, url: str):
        """Fetch a single unit (video, lecture, or quiz) metadata from its URL."""
        return await collectors.fetch_unit(self.context, url)

    @try_except_request
    @login_required
    async def fetch_course(self, url: str):
        """Fetch course structure (chapters and units) from a course URL."""
        return await collectors.fetch_course(self.context, url)

    @try_except_request
    @login_required
    async def fetch_bootcamp(self, url: str):
        """Fetch bootcamp structure (modules and units) from a bootcamp URL."""
        return await collectors.fetch_bootcamp(self.context, url)

    @try_except_request
    @login_required
    async def download(self, url: str, **kwargs) -> None:
        """
        Download content from a URL (video, lecture, course, or bootcamp).

        For courses and bootcamps, uses cached JSON when available to skip web scraping.
        Pass-through kwargs are forwarded to the underlying downloaders (e.g. quality,
        override, threads).
        """
        from pathlib import Path

        from .downloaders import download_bootcamp, download_course, download_unit
        from .models import TypeUnit
        from .utils import is_bootcamp, is_course, is_lecture, is_quiz, is_video

        console = Console()

        if is_video(url) or is_lecture(url) or is_quiz(url):
            unit = await self.fetch_unit(url)
            extension = ".mp4" if unit.type == TypeUnit.VIDEO else ".mhtml"
            await download_unit(
                self.context,
                unit,
                Path(unit.name + extension),
                **kwargs,
            )

        elif is_course(url):
            logger.info(f"[cyan]Checking local cache for:[/] {url}")
            course = get_cached_course(url)

            if course:
                logger.info("[green]Cache hit. Loading course data from cache[/]\n")
            else:
                with console.status(
                    "[yellow]No local cache. Fetching data from web...[/]\n",
                    spinner="bouncingBar",
                    spinner_style="yellow",
                ):
                    course = await self.fetch_course(url)

                logger.info("[green]Data successfully saved to cache.\n")

            await download_course(self.context, course, **kwargs)

        elif is_bootcamp(url):
            logger.info(f"[cyan]Checking local cache for:[/] {url}")
            bootcamp = get_cached_bootcamp(url)

            if bootcamp:
                logger.info("[green]Cache hit. Loading course data from cache.[/]\n")
            else:
                with console.status(
                    "[yellow]No local cache. Fetching data from web...[/]\n",
                    spinner="bouncingBar",
                    spinner_style="yellow",
                ):
                    bootcamp = await self.fetch_bootcamp(url)

                logger.info("[green]Data successfully saved to cache.\n")

            await download_bootcamp(self.context, bootcamp, **kwargs)

        else:
            raise Exception(
                "Please provide a valid URL, either a video, lecture, "
                "course, or bootcamp."
            )

    @try_except_request
    async def set_cookies(self, path: Path) -> None:
        """
        Load cookies from a JSON file and set them in the browser context.

        Marks the client as authenticated if the cookies are valid. Saves state to disk.

        Parameters
        ----------
        path : Path
            Path to a JSON file containing cookies (e.g. exported from browser).
        """
        cookies = normalize_cookies(read_json(path))  # type: ignore
        await self.context.add_cookies(cookies)  # type: ignore

        await self._set_profile()

        if self.authenticated:
            await save_state(self.context, SESSION_FILE)
            logger.info("Cookies imported, Logged in successfully!\n")
        else:
            logger.error(
                "Login failed. The cookies provided may be invalid or expired."
            )

    @try_except_request
    async def _set_profile(self) -> None:
        """Check if the current context is authenticated by loading the home page and
        detecting the welcome message."""
        SELECTOR = "h1.h1.f-text-34"
        TIMEOUT = 5 * 1000

        page = await self.page

        try:
            await page.goto(BASE_URL, wait_until="domcontentloaded")

            await page.wait_for_selector(SELECTOR, timeout=TIMEOUT)

            welcome_message = await page.locator(SELECTOR).first.text_content()

            if welcome_message:
                self.authenticated = True
                console = Console()

                panel = Panel.fit(
                    welcome_message,
                    border_style="cyan",
                    style="green",
                )
                console.print(Align.center(panel))
                print()

        except PlaywrightTimeoutError:
            self.authenticated = False
        except Exception as e:
            logger.debug(f"Could not fetch profile: {e}")
        finally:
            await page.close()
