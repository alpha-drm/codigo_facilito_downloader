import asyncio
from pathlib import Path

import typer
from typing_extensions import Annotated

from facilito import AsyncFacilito, Quality

from .helpers import check_dependencies
from .utils import banner

app = typer.Typer(rich_markup_mode="rich")


@app.callback()
def main():
    banner()


@app.command()
def login() -> None:
    """
    Open a browser window to log in to Codigo Facilito.

    Usage:
        facilito login
    """
    asyncio.run(_login())


@app.command()
def set_cookies(
    path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            help="Path to cookies.json",
            show_default=False,
        ),
    ],
):
    """
    Login to Codigo Facilito using your cookies.

    Usage:
        facilito set-cookies cookies.json
    """
    asyncio.run(_set_cookies(path))


@app.command()
def logout():
    """
    Delete the Facilito session from the local storage.

    Usage:
        facilito logout
    """
    asyncio.run(_logout())


@app.command()
def download(
    url: Annotated[
        str,
        typer.Argument(
            help="The URL of the bootcamp | course | video | lecture to download.",
            show_default=False,
        ),
    ],
    quality: Annotated[
        Quality,
        typer.Option(
            "--quality",
            "-q",
            help="The quality of the video to download.",
            show_default=True,
        ),
    ] = Quality.P1080,
    override: Annotated[
        bool,
        typer.Option(
            "--override",
            "-w",
            help="Override existing file if exists.",
            show_default=True,
        ),
    ] = False,
    threads: Annotated[
        int,
        typer.Option(
            "--threads",
            "-t",
            min=1,
            max=16,
            help="Number of threads to use.",
            show_default=True,
        ),
    ] = 10,
    headless: Annotated[
        bool,
        typer.Option(
            "--headless/--no-headless",
            help="Run the browser hidden (--headless: default) or visible (--no-headless).",  # noqa: E501
            show_default=True,
        ),
    ] = True,
):
    """
    Download a bootcamp | course | video | lecture from the given URL.

    Arguments:
        url: str - The URL of the bootcamp, course, video, or lecture to download.

    Usage:
        facilito download <url>

    Examples:
        facilito download https://codigofacilito.com/programas/ingles-conversacional

        facilito download https://codigofacilito.com/cursos/docker

        facilito download https://codigofacilito.com/videos/...

        facilito download https://codigofacilito.com/articulos/...
    """

    try:
        check_dependencies()
    except RuntimeError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    asyncio.run(
        _download(
            url,
            quality=quality,
            override=override,
            threads=threads,
            headless=headless,
        )
    )


async def _login() -> None:
    """Run login flow inside an AsyncFacilito context."""
    async with AsyncFacilito(headless=False) as client:
        await client.login()


async def _logout() -> None:
    """Run logout (delete session) inside an AsyncFacilito context."""
    async with AsyncFacilito(headless=True) as client:
        await client.logout()


async def _download(url: str, **kwargs) -> None:
    """Run download for the given URL inside an AsyncFacilito context."""
    headless = kwargs.pop("headless", True)
    async with AsyncFacilito(headless=headless) as client:
        await client.download(url, **kwargs)


async def _set_cookies(path: Path) -> None:
    """Load cookies from file and save state inside an AsyncFacilito context."""
    async with AsyncFacilito(headless=True) as client:
        await client.set_cookies(path)
