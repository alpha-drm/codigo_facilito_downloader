from urllib.parse import urljoin

from playwright.async_api import BrowserContext, Page

from ..constants import BASE_URL
from ..errors import CourseError, UnitError
from ..helpers import clean_string, slugify
from ..logger import logger
from ..models import Bootcamp, Module, Unit
from ..utils import get_unit_type

# =========================
# Selectors - Bootcamp Page
# =========================

ACCORDION_SELECTOR = "ul.collapsible.f-topics li.f-radius-small"
ACCORDION_HEADER_SELECTOR = "header.collapsible-header"
ACCORDION_MODULE_NAME_SELECTOR = ".collapsible-header span.f-green-text"

# =========================
# Selectors - Course Page
# =========================

CHAPTERS_SELECTOR = "ul.f-topics > div.f-top-16"
LESSONS_LINKS_SELECTOR = ".collapsible-body ul a, div.topics-li ul > a"
LESSON_NAME_SELECTOR = "p.ibm"

# ==========================================================
# Extract lessons from a course page
# ==========================================================


async def _extract_units_from_course(page: Page, url: str) -> list[Unit]:
    """
    Open a course page and extract all lesson units.
    """
    units: list[Unit] = []

    try:
        await page.goto(url, wait_until="domcontentloaded")

        accordions = page.locator(CHAPTERS_SELECTOR)
        accordion_count = await accordions.count()

        for i in range(accordion_count):
            chapter = accordions.nth(i)

            header = chapter.locator(ACCORDION_HEADER_SELECTOR).first
            expanded = await header.get_attribute("aria-expanded")

            # Expand if collapsed
            if expanded != "true":
                await header.click()
                await page.wait_for_timeout(1500)

        lessons = page.locator(LESSONS_LINKS_SELECTOR)
        lessons_count = await lessons.count()

        for i in range(lessons_count):
            lesson = lessons.nth(i)

            title_locator = lesson.locator(LESSON_NAME_SELECTOR).first
            name = await title_locator.text_content()
            href = await lesson.get_attribute("href")

            if not name or not href:
                continue

            final_url = urljoin(BASE_URL, href)

            units.append(
                Unit(
                    type=get_unit_type(final_url),
                    name=clean_string(name),
                    slug=slugify(name),
                    url=final_url,
                )
            )

    except Exception as e:
        logger.warning("Error extracting units from %s: %s", url, e)
        return []

    return units


# ==========================================================
# Extract modules (grouped by accordion)
# ==========================================================


async def _fetch_bootcamp_modules(page: Page) -> list[Module]:
    """
    Extract modules grouped by accordion.

    Each accordion becomes ONE Module.
    All intermediate links inside the accordion
    contribute units to that same module.
    """
    accordions = page.locator(ACCORDION_SELECTOR)
    accordion_count = await accordions.count()

    if not accordion_count:
        raise UnitError("No accordion modules found.")

    modules: list[Module] = []

    temp_page = await page.context.new_page()

    try:
        for i in range(accordion_count):
            accordion = accordions.nth(i)

            header = accordion.locator(ACCORDION_HEADER_SELECTOR).first
            expanded = await header.get_attribute("aria-expanded")

            # Expand if collapsed
            if expanded != "true":
                await header.click()
                await page.wait_for_timeout(1500)

            # Extract accordion name (THIS is folder name)
            module_name = await accordion.locator(
                ACCORDION_MODULE_NAME_SELECTOR
            ).first.text_content()

            # Clean module name: remove newlines, extra spaces, and tabs
            module_name = " ".join(module_name.strip().split())

            if not module_name:
                continue

            # Extract intermediate links
            links_locator = accordion.locator(LESSONS_LINKS_SELECTOR)
            links = await links_locator.all()

            if not links:
                continue

            module_units: list[Unit] = []

            for link in links:
                href = await link.get_attribute("href")
                if not href:
                    continue

                full_url = urljoin(BASE_URL, href)

                try:
                    # Accumulate units into SAME module
                    units = await _extract_units_from_course(
                        temp_page,
                        full_url,
                    )
                    module_units.extend(units)

                except Exception as e:
                    logger.warning("Failed extracting units from %s: %s", full_url, e)

            if not module_units:
                continue

            modules.append(
                Module(
                    name=module_name,
                    slug=slugify(module_name),
                    units=module_units,
                )
            )

    finally:
        await temp_page.close()

    return modules


# ==========================================================
# Public API
# ==========================================================


async def fetch_bootcamp(context: BrowserContext, url: str) -> Bootcamp:
    """
    Fetch bootcamp metadata and structure (modules and units) from a bootcamp URL.

    Parameters
    ----------
    context : BrowserContext
        Playwright browser context (must be authenticated).
    url : str
        Full URL of the bootcamp (program) page.

    Returns
    -------
    Bootcamp
        Bootcamp model with name, slug, url, and modules (each with units).

    Raises
    ------
    CourseError
        If the page cannot be loaded, name cannot be extracted, or no modules are found.
    """
    page: Page | None = None

    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        bootcamp_name = await page.locator("h1").first.text_content()

        if not bootcamp_name:
            raise CourseError("Unable to extract bootcamp name.")

        modules = await _fetch_bootcamp_modules(page)

        if not modules:
            raise CourseError("Bootcamp contains no modules.")

    except Exception as e:
        raise CourseError(f"Error fetching bootcamp: {str(e)}")

    finally:
        if page is not None:
            await page.close()

    return Bootcamp(
        name=clean_string(bootcamp_name),
        slug=slugify(bootcamp_name),
        url=url,
        modules=modules,
    )
