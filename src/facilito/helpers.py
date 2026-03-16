import hashlib
import json
import re
import shutil
from pathlib import Path

import aiofiles
import aiohttp
from unidecode import unidecode

from .constants import APP_NAME, DEPENDENCIES
from .models import Bootcamp, Chapter, Course, Module, Unit


def get_cached_course(url: str) -> Course | None:
    """
    Look up a cached course by URL from local JSON files under the app data directory.

    Searches all subdirectories for JSON files whose "url" field matches. Used to skip
    web scraping when a course structure was already fetched and saved.

    Parameters
    ----------
    url : str
        Course URL to look up.

    Returns
    -------
    Course | None
        The course model if a matching JSON is found, otherwise None.
    """
    base_dir = Path(APP_NAME)

    if not base_dir.exists():
        return None

    for json_path in base_dir.glob("*/*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                if data.get("url") == url:
                    chapters = []
                    for cap_data in data.get("chapters", []):
                        units = [Unit(**u) for u in cap_data.get("units", [])]
                        cap_dict = {k: v for k, v in cap_data.items() if k != "units"}
                        chapters.append(Chapter(**cap_dict, units=units))

                    course_dict = {k: v for k, v in data.items() if k != "chapters"}
                    return Course(**course_dict, chapters=chapters)
        except Exception:
            continue

    return None


def get_cached_bootcamp(url: str) -> Bootcamp | None:
    """
    Look up a cached bootcamp by URL from local JSON files under the app data directory.

    Searches subdirectories for JSON files whose "url" field matches. Used to skip
    web scraping when a bootcamp structure was already fetched and saved.

    Parameters
    ----------
    url : str
        Bootcamp URL to look up.

    Returns
    -------
    Bootcamp | None
        The bootcamp model if a matching JSON is found, otherwise None.
    """
    base_dir = Path(APP_NAME)
    if not base_dir.exists():
        return None
    for json_path in base_dir.glob("*/*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("url") != url:
                    continue
                modules = []
                for mod_data in data.get("modules", []):
                    units = [Unit(**u) for u in mod_data.get("units", [])]
                    mod_dict = {k: v for k, v in mod_data.items() if k != "units"}
                    modules.append(Module(**mod_dict, units=units))
                bootcamp_dict = {k: v for k, v in data.items() if k != "modules"}
                return Bootcamp(**bootcamp_dict, modules=modules)
        except Exception:
            continue
    return None


def read_json(path: str | Path) -> dict:
    """
    Read a JSON file and return its contents as a dictionary.

    :param str | Path path: path to the JSON file
    :return dict: dictionary containing the JSON data

    Example
    -------
    >>> read_json("data.json")
    {"key": "value"}
    """
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: str | Path, data: dict) -> None:
    """
    Write a dictionary to a JSON file.

    :param str | Path path: path to the JSON file
    :param dict data: dictionary to write
    :return None: None

    Example
    -------
    >>> write_json("data.json", {"key": "value"})
    """
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def clean_string(text: str) -> str:
    """
    Remove special characters from a string and strip it.

    :param str text: string to clean
    :return str: cleaned string

    Example
    -------
    >>> clean_string("   Hi:;<>?{}|"")
    "Hi"
    >>> clean_string("Mi*archivo??.mp4")
    "Miarchivo.mp4"
    >>> clean_string(" Carpeta de prueba... ")
    "Carpeta de prueba"
    """

    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    text = re.sub(invalid_chars, "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.rstrip(".")

    # Quitar espacios al inicio y al final
    return text.strip()


def slugify(text: str) -> str:
    """
    Slugify a string, removing special characters and replacing
    spaces with hyphens.

    :param str text: string to convert
    :return str: slugified string

    Example
    -------
    >>> slugify(""Café! Frío?"")
    "cafe-frio"
    """
    return unidecode(clean_string(text)).lower().replace(" ", "-")


def hashify(input: str) -> str:
    """
    Generate a unique hash for a given string.

    :param str input: string to hash
    :return str: hash string

    Example
    -------
    >>> hashify("Hello, World!")
    "b109f81c07a71be02dbc28adac84f3a5df7e4be2b91329d1b0149d17bd6c92b3"
    """
    hash_object = hashlib.sha256(input.encode("utf-8"))
    return hash_object.hexdigest()


async def download_file(url: str, path: Path | str, overwrite: bool = False) -> None:
    """
    Download a file from a URL and save it to a path.

    :param str url: URL of the file to download
    :param Path | str path: path to save the file
    :param bool overwrite: overwrite existing file if exists (default: False)
    :return None: None
    :raises aiohttp.ClientError: For network-related errors
    :raises OSError: If there's an error writing to the file
    :raises Exception: For other errors

    Example
    -------
    >>> await download_file("https://example.com/file.txt", "file.txt")
    """
    path = Path(path) if isinstance(path, str) else path

    if not overwrite and path.exists():
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(path, "wb") as file:
                    async for chunk in response.content.iter_chunked(1024):
                        await file.write(chunk)
        except aiohttp.ClientError:
            raise Exception(f"Network error downloading {url}")
        except OSError:
            raise Exception(f"Error saving to {path}")
        except Exception:
            raise Exception(f"Something went wrong downloading {url}")


def check_dependencies() -> None:
    """Ensure required external commands (e.g. yt-dlp, ffmpeg) are available on PATH."""
    missing = [cmd for cmd in DEPENDENCIES if not shutil.which(cmd)]

    if missing:
        lines = ["Missing required dependencies:\n"]

        for dep in missing:
            lines.append(f"- {dep}: {DEPENDENCIES[dep]}")

        lines.append("\nPlease install them and ensure they are in your PATH.")

        raise RuntimeError("\n".join(lines))
