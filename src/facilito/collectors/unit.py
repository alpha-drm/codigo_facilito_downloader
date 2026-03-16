from playwright.async_api import BrowserContext

from ..errors import UnitError
from ..helpers import clean_string, slugify
from ..models import TypeUnit, Unit
from ..utils import get_unit_type


async def fetch_unit(context: BrowserContext, url: str) -> Unit:
    """
    Fetch unit metadata (name, type, slug, url) from a unit URL.

    Parameters
    ----------
    context : BrowserContext
        Playwright browser context (must be authenticated).
    url : str
        Full URL of the unit (video, lecture, or quiz).

    Returns
    -------
    Unit
        Unit model with type, name, slug, url. Quizzes return a placeholder unit.

    Raises
    ------
    UnitError
        If the page cannot be loaded or the unit type is not recognized.
    """
    NAME_SELECTOR = ".title-section header h1"

    try:
        type = get_unit_type(url)

        if type == TypeUnit.QUIZ:
            # TODO: implement quiz fetching
            return Unit(
                type=type,
                url=url,
                name="quiz",
                slug="quiz",
            )
    except Exception:
        raise UnitError()

    page = None
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        name = await page.locator(NAME_SELECTOR).first.text_content()

        if not name:
            raise UnitError()

        type = get_unit_type(url)

    except Exception:
        raise UnitError()

    finally:
        if page is not None:
            await page.close()

    return Unit(
        type=type,
        name=clean_string(name),
        url=url,
        slug=slugify(name),
    )
