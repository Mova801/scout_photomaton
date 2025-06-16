from pathlib import Path
import logging
from rich.logging import RichHandler

from core.config import _config

logging.basicConfig(
    level=_config.get("logging.level"),
    format=_config.get("logging.format"),
    handlers=[
        RichHandler(rich_tracebacks=True, show_path=False, markup=True),
        # logging.FileHandler(
        #     Path(_config.get("paths.logs_folder"))
        #     / Path(_config.get("app.name").lower())
        # ),
    ],
)

_logger = logging.getLogger(_config.get("app.name"))
