import logging

from rich.logging import RichHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --- Rich Console Handler ---
console_handler = RichHandler(
    rich_tracebacks=True,
    markup=True,
    show_time=False,
    show_level=False,
    show_path=False,  # deleted async_api.py:
)
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(message)s")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# --- File Handler ---
log_file = "facilito.log"
file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

file_formatter = logging.Formatter(
    "{asctime} [{levelname}] [{filename}:{funcName}:{lineno}] - {message}",
    datefmt="%Y-%m-%d %H:%M:%S",
    style="{",
)

file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
