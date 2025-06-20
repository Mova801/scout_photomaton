import tomllib
from pathlib import Path
from typing import Any

from core.exceptions import ConfigNotFoundError, ConfigLookupError


class Config:
    def __init__(self, config_path: str = "config.toml") -> None:
        self.config_path = Path(config_path)
        self.config: dict[str, Any] = self.load_config()

    def load_config(self) -> None:
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                return tomllib.load(f)
        else:
            raise ConfigNotFoundError(
                f"Configurazione '{self.config_path}' non trovata."
            )

    def get(self, key: str, default: Any = None) -> Any:
        """Accesso con dot notation: config.get('app.name')"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_path(self, key: str) -> str:
        for path in self.get("paths.folders"):
            folder = self.get("paths.folders." + path)
            files = self.get("paths." + folder)
            if files and key in files.keys():
                return self.get(f"paths.{path}.{key}")
        raise ConfigLookupError(f"Impossibile trovare {key}")


_config: dict[str, Any] = Config()


# class Config:
#     # pins
#     TOKEN_SLOT_PIN: int = 24
#     BUTTON_PIN: int = 25
#     # paths
#     PHOTOS_FOLDER: Path = Path("photos")
#     WATERMARK_IMAGE_PATH: Path = (
#         Path("images") / Path("template") / Path("template.png")
#     )
#     BACKGROUND_IMAGE_PATH: Path = Path("images") / Path("background.png")
#     ARROW_IMAGE_PATH_PATH: Path = Path("images") / Path("arrow.png")
#     # font
#     FONT_FAMILY: str = None
#     # colors
#     TEXT_COLOR: pg.Color = pg.Color("white")
#     BACKGROUND_COLOR: pg.Color = pg.Color("black")
#     # photobooth
#     PHOTO_COUNT: int = 3
#     COUNTDOWN: int = 3
#     # camera
#     DEFAULT_CAMERA: int = 0
#     # printer
#     MAX_QUEUE_SIZE: int = 3
#     MAX_WAIT_TIME: int = 60
#     # image
#     IMAGE_WIDTH = 550
#     IMAGE_HEIGHT = 360
#     # other
#     WIN_SCALE_FACTOR: int = 1
#     TRANSITION_DELAY_SEC: float = 0.2
