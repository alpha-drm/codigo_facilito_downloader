from playwright.async_api import BrowserContext, Page

from ..constants import BASE_URL
from ..errors import CourseError, UnitError
from ..helpers import clean_string, slugify
from ..models import Chapter, Course, Unit
from ..utils import get_unit_type


async def _fetch_course_chapters(page: Page) -> list[Chapter]:
    """Expand accordions and extract chapters (with units)."""
    CHAPTERS_SELECTOR = (
        ".collapsible.no-box-shadow.no-border.f-topics.no-time > .f-top-16"
    )

    ACCORDION_HEADER_SELECTOR = "header.collapsible-header"
    CHAPTER_NAME_SELECTOR = "header h4"
    UNITS_SELECTOR = ".collapsible-body ul a"
    UNIT_NAME_SELECTOR = "p.ibm"

    chapters_selectors = page.locator(CHAPTERS_SELECTOR)
    chapters_count = await chapters_selectors.count()

    if not chapters_count:
        raise CourseError("No chapters found")

    chapters: list[Chapter] = []

    for i in range(chapters_count):
        chapter_locator = chapters_selectors.nth(i)

        header = chapter_locator.locator(ACCORDION_HEADER_SELECTOR).first
        expanded = await header.get_attribute("aria-expanded")

        # Expand if collapsed
        if expanded != "true":
            await header.click()
            await page.wait_for_timeout(2000)

        chapter_name = await chapter_locator.locator(
            CHAPTER_NAME_SELECTOR
        ).first.text_content()

        if not chapter_name:
            raise CourseError("Chapter without name")

        units_locators = chapter_locator.locator(UNITS_SELECTOR)
        units_count = await units_locators.count()

        if not units_count:
            raise CourseError("Chapter without units")

        units: list[Unit] = []

        for j in range(units_count):
            unit_locator = units_locators.nth(j)

            unit_name = await unit_locator.locator(
                UNIT_NAME_SELECTOR
            ).first.text_content()

            unit_url = await unit_locator.get_attribute("href")

            if not unit_name or not unit_url:
                raise UnitError("Invalid unit data")

            units.append(
                Unit(
                    type=get_unit_type(unit_url),
                    name=clean_string(unit_name),
                    slug=slugify(unit_name),
                    url=BASE_URL + unit_url,
                )
            )

        chapters.append(
            Chapter(
                name=clean_string(chapter_name),
                slug=slugify(chapter_name),
                units=units,
            )
        )

    return chapters


async def fetch_course(context: BrowserContext, url: str) -> Course:
    """
    Fetch course metadata and structure (chapters and units) from a course URL.

    Parameters
    ----------
    context : BrowserContext
        Playwright browser context (must be authenticated).
    url : str
        Full URL of the course page.

    Returns
    -------
    Course
        Course model with name, slug, url, and chapters (each with units).

    Raises
    ------
    CourseError
        If the page cannot be loaded or structure cannot be extracted.
    """
    NAME_SELECTOR = ".f-course-presentation h1, .cover-with-image h1"

    page = await context.new_page()

    try:
        await page.goto(url)

        name = await page.locator(NAME_SELECTOR).first.text_content()

        if not name:
            raise CourseError("Course name not found")

        chapters = await _fetch_course_chapters(page)

        return Course(
            name=clean_string(name),
            slug=slugify(name),
            url=url,
            chapters=chapters,
        )

    except Exception as e:
        raise CourseError(str(e)) from e

    finally:
        await page.close()
