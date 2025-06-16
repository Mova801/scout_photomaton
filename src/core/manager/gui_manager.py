from functools import wraps
from pathlib import Path
import pygame as pg

from core.config import _config
from core.logger import _logger


_Position = tuple[int, int]


def deferred_init(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._deferred and not self._initialized:
            self._set_up()
        return func(self, *args, **kwargs)

    return wrapper


class GuiManager:

    def __init__(self, name: str, fullscreen: bool = False, deferred: bool = False):
        self.name = name if name else _config.get("app.name")
        self.fullscreen = fullscreen
        self._deferred = deferred
        self._initialized = False
        if not deferred:
            self._set_up()
        else:
            _logger.info("Gui init deferred" if deferred else None)

    def _set_up(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        _logger.info("Initializing gui")

        pg.init()
        pg.mouse.set_visible(False)

        _logger.info("Display setup")
        self._setup_display(self.fullscreen)
        _logger.info("Loading gui images")
        self._load_images()
        self._current_pics = []

        pg.display.set_caption(f"{self.name}-{_config.get('app.version')}", self.name)
        pg.display.set_icon(self._get_image("icon"))

        self._primary_font = pg.font.Font(None, 180)
        self._secondary_font = pg.font.Font(None, 100)

    def _setup_display(self, fullscreen: bool):
        if fullscreen:
            info = pg.display.Info()
            self._screen_size = (info.current_w, info.current_h)
            self._screen = pg.display.set_mode(self._screen_size, pg.FULLSCREEN)
        else:
            base_size = _config.get("app.base_size", (800, 600))
            self._screen_size = base_size
            self._screen = pg.display.set_mode(base_size)

    def _load_images(self) -> None:
        for path in _config.get("paths.folders"):
            folder = _config.get("paths.folders." + path)
            files = _config.get("paths." + folder)
            if not files:
                continue
            self._images = {
                file: pg.image.load(Path(folder) / Path(file)).convert_alpha()
                for file in files.values()
            }

    def _get_image(self, key: str) -> str:
        return self._images.get(_config.get_path(key))

    def _flip(self) -> None:
        pg.display.flip()

    def _blit_text(self, text: str, font: pg.font.Font, pos: _Position = None) -> None:
        text_surf = font.render(text, True, _config.get("gui.colors.text"))
        text_pos = text_surf.get_rect()
        if not pos:
            text_pos.center = self._screen.get_rect().center
        else:
            text_pos.center = pos
        self._screen.blit(text_surf, text_pos)

    def _blit_image(
        self, image: pg.Surface, pos: _Position, scale: float = 1, cover: bool = False
    ) -> None:
        img_w, img_h = image.get_size()
        if cover:
            scale_x = min(img_w, self._screen_size[0]) / max(
                img_w, self._screen_size[0]
            )
            scale_y = min(img_h, self._screen_size[1]) / max(
                img_h, self._screen_size[1]
            )
            scale = max(scale_x, scale_y)
        new_size = tuple(int(comp * scale) for comp in image.get_size())
        scaled = pg.transform.smoothscale(image, new_size)
        if not pos:
            pos = None, None
        x = pos[0] if pos[0] is not None else (self._screen_size[0] - new_size[0]) // 2
        y = pos[1] if pos[1] is not None else (self._screen_size[1] - new_size[1]) // 2

        self._screen.blit(scaled, (x, y))

    def _blit_overlay(self) -> None:
        overlay = pg.Surface(self._screen.get_size())
        overlay.set_alpha(int(255 * 0.75))
        overlay.fill("black")
        self._screen.blit(overlay, (0, 0))

    def show_init_screen(self) -> None:
        if not self._initialized:
            return
        self._blit_image(self._get_image("background"), None, cover=True)
        self._blit_text(_config.get("gui.labels.init", ""), self._primary_font)
        self._flip()

    @deferred_init
    def show_token_screen(self) -> None:
        self._screen.fill(_config.get("gui.colors.background"))
        self._blit_image(self._get_image("background"), None, cover=True)
        self._blit_text(_config.get("gui.labels.token", ""), self._primary_font)
        self._flip()

    @deferred_init
    def show_button_screen(self) -> None:
        self._screen.fill(_config.get("gui.colors.background"))
        self._blit_image(self._get_image("background"), None, cover=True)
        self._blit_overlay()
        y = self._screen.get_rect().centery
        self._blit_image(self._get_image("arrow"), (None, y + y // 3), 0.3)
        self._blit_text(_config.get("gui.labels.button", ""), self._primary_font)
        self._flip()

    @deferred_init
    def is_pressed(self, key: int) -> bool:
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == key:
                return True
        return False

    @deferred_init
    def request_to_stop(self) -> bool:
        for event in pg.event.get():
            if event.type == pg.QUIT or (
                event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
            ):
                return True
        return False

    def stop(self) -> None:
        if not self._initialized:
            return
        pg.quit()
