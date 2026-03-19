import json
import time
from pathlib import Path

from playwright.async_api import BrowserContext
from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from ..constants import APP_NAME
from ..models import Course, TypeUnit
from ..utils import save_page
from .unit import download_unit

DIR_PATH = Path(APP_NAME)


async def download_course(context: BrowserContext, course: Course, **kwargs) -> None:
    """
    Download a course: save structure as JSON, optionally save course page as MHTML,
    then download each unit.

    Parameters
    ----------
    context : BrowserContext
        Playwright browser context (used for saving pages and delegating to
        download_unit).
    course : Course
        Course model with chapters and units.

    Other Parameters
    ----------------
    override : bool, optional
        If True, re-download even when files exist. Default False.
    threads : int, optional
        Number of concurrent fragments for video downloads. Default 10.
    """
    COURSE_DIR_PATH = DIR_PATH / course.name
    COURSE_DIR_PATH.mkdir(parents=True, exist_ok=True)

    JSON_PATH = COURSE_DIR_PATH / f"{course.name}.json"

    override = kwargs.get("override", False)

    if override or not JSON_PATH.exists():
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(
                course, f, default=lambda o: o.__dict__, indent=4, ensure_ascii=False
            )

    source_path = COURSE_DIR_PATH / "source.mhtml"

    if override or not source_path.exists():
        await save_page(context, course.url, source_path)

    # --- Course Details Table ---
    table = Table(
        title=course.name,
        border_style="cyan",
        caption="processing...",
        caption_style="green",
        title_style="green",
        header_style="green",
        footer_style="green",
        show_footer=True,
        box=box.ROUNDED,
    )
    table.add_column("Modules", style="green", footer="Total", no_wrap=True)
    table.add_column("Lessons", style="green", footer="0", justify="center")

    total_units = 0

    with Live(Align.left(table), refresh_per_second=4):
        for idx, section in enumerate(course.chapters, 1):
            time.sleep(0.3)  # arbitrary delay
            num_units = len(section.units)
            total_units += num_units
            table.add_row(f"{idx} - {section.name}", str(len(section.units)))
            table.columns[1].footer = str(total_units)  # Update footer dynamically

    print()

    console = Console()
    total_units = sum(len(chapter.units) for chapter in course.chapters)
    current_unit = 0

    for idx, chapter in enumerate(course.chapters, 1):
        CHAPTER_DIR_PATH = COURSE_DIR_PATH / f"{idx:02d} - {chapter.name}"
        CHAPTER_DIR_PATH.mkdir(parents=True, exist_ok=True)

        panel = Panel(
            Align.center(f"{chapter.name}"),
            title=f"MODULE {idx}",
            style="green",
            border_style="cyan",
            box=box.ROUNDED,
            expand=False,
        )
        console.print(Align.left(panel))

        for jdx, unit in enumerate(chapter.units, 1):
            current_unit += 1
            progress_str = f"{current_unit}/{total_units}"

            if unit.type == TypeUnit.VIDEO:
                await download_unit(
                    context,
                    unit,
                    CHAPTER_DIR_PATH / f"{jdx:02d} - {unit.name}.mp4",
                    progress_str=progress_str,
                    **kwargs,
                )
            else:
                await download_unit(
                    context,
                    unit,
                    CHAPTER_DIR_PATH / f"{jdx:02d} - {unit.name}.mhtml",
                    progress_str=progress_str,
                    **kwargs,
                )

        print()

    console.print(
        Panel(
            Align.center("Download complete!"),
            border_style="cyan",
            style="bold green",
            expand=False,
        )
    )
