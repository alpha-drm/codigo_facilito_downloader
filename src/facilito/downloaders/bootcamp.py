import json
from pathlib import Path

from playwright.async_api import BrowserContext
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from ..constants import APP_NAME
from ..models import Bootcamp, TypeUnit
from ..utils import save_page
from .unit import download_unit

DIR_PATH = Path(APP_NAME)


async def download_bootcamp(
    context: BrowserContext, bootcamp: Bootcamp, **kwargs
) -> None:
    """
    Download a bootcamp: save structure as JSON, optionally save bootcamp page as MHTML,
    then download each module's units.

    Parameters
    ----------
    context : BrowserContext
        Playwright browser context (used for saving pages and delegating to
        download_unit).
    bootcamp : Bootcamp
        Bootcamp model with modules and units.

    Other Parameters
    ----------------
    override : bool, optional
        If True, re-download even when files exist. Default False.
    threads : int, optional
        Number of concurrent fragments for video downloads. Default 10.

    Directory structure
    ------------------
    Facilito/
    └── bootcamp-name/
        ├── bootcamp-name.json
        ├── source.mhtml
        ├── 01 - module-1/
        │   ├── 1.1 unit-name.mp4
        │   └── ...
        └── 02 - module-2/
            └── ...
    """
    BOOTCAMP_DIR_PATH = DIR_PATH / bootcamp.name
    BOOTCAMP_DIR_PATH.mkdir(parents=True, exist_ok=True)

    JSON_PATH = BOOTCAMP_DIR_PATH / f"{bootcamp.name}.json"

    override = kwargs.get("override", False)

    if override or not JSON_PATH.exists():
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(
                bootcamp, f, default=lambda o: o.__dict__, indent=4, ensure_ascii=False
            )

    source_path = BOOTCAMP_DIR_PATH / "source.mhtml"

    # Save bootcamp page as reference
    if override or not source_path.exists():
        await save_page(context, bootcamp.url, source_path)

        # --- Course Details Tree ---
        console = Console()

        # Root node (bootcamp)
        tree = Tree(f"[bold green]{bootcamp.name}[/bold green]")

        for idx, module in enumerate(bootcamp.modules, 1):
            module_branch = tree.add(f"[green]{idx}- {module.name}[/green]")
            for unit_idx, unit in enumerate(module.units, 1):
                module_branch.add(f"{idx}.{unit_idx} {unit.name}")

        console.print(tree)
        print()

    console = Console()
    total_units = sum(len(chapter.units) for chapter in bootcamp.modules)
    current_unit = 0

    # Download each module
    for idx, module in enumerate(bootcamp.modules, 1):
        MODULE_DIR_PATH = BOOTCAMP_DIR_PATH / f"{idx:02d} - {module.name}"
        MODULE_DIR_PATH.mkdir(parents=True, exist_ok=True)

        panel = Panel(
            Align.center(f"{module.name}"),
            style="green",
            border_style="cyan",
            box=box.HORIZONTALS,
            expand=False,
        )
        console.print(Align.left(panel))

        # Download each unit in the module
        for jdx, unit in enumerate(module.units, 1):
            current_unit += 1
            progress_str = f"{current_unit}/{total_units}"

            if unit.type == TypeUnit.VIDEO:
                await download_unit(
                    context,
                    unit,
                    MODULE_DIR_PATH / f"{idx}.{jdx} {unit.name}.mp4",
                    progress_str=progress_str,
                    **kwargs,
                )

            else:
                # For lectures, quizzes, etc., save as MHTML
                await download_unit(
                    context,
                    unit,
                    MODULE_DIR_PATH / f"{jdx:02d} {unit.name}.mhtml",
                    **kwargs,
                )
        print()

    console.print(
        Panel(
            Align.center("Download complete!"),
            border_style="green",
            style="bold green",
            expand=False,
        )
    )
