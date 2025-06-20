from functools import wraps
from pathlib import Path
import pygame as pg

from core.image_utils import compute_cover_scale_factor, scale_surface
from core.config import _config
from core.logger import _logger


_Position = tuple[int, int]
_Size = tuple[int, int]


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
        if self._deferred:
            _logger.info("Initializing gui")

        pg.init()
        pg.mouse.set_visible(False)

        _logger.info("Display setup")
        self._setup_display(self.fullscreen)
        _logger.info("Loading gui images")
        self._load_images()

        pg.display.set_caption(f"{self.name}-{_config.get('app.version')}", self.name)
        pg.display.set_icon(self._get_image("icon"))

    def _setup_display(self, fullscreen: bool):
        if fullscreen:
            info = pg.display.Info()
            screen_size = (info.current_w, info.current_h)
            self._screen = pg.display.set_mode(screen_size, pg.FULLSCREEN)
        else:
            base_size = _config.get("app.base_size", (800, 600))
            self._screen = pg.display.set_mode(base_size)

    def _get_win_size(self) -> _Size:
        return pg.display.get_window_size()

    def _load_images(self) -> None:
        for path in _config.get("paths.folders"):
            folder = _config.get("paths.folders." + path)
            files = _config.get("paths." + folder)
            if not files:
                continue
            self._images: list[pg.Surface] = {
                file: pg.image.load(Path(folder) / Path(file)).convert_alpha()
                for file in files.values()
            }

    def _get_image(self, key: str) -> pg.Surface:
        return self._images.get(_config.get_path(key))

    def _flip(self) -> None:
        pg.display.flip()

    def _blit_text(self, text: str, h_ratio: float, pos: _Position = None) -> None:
        h_ratio = min(1, max(0.02, h_ratio))
        size: int = int(self._screen.get_size()[1] * h_ratio)
        font = pg.font.Font(None, int(size))
        text_surf = font.render(text, True, _config.get("gui.colors.text"))
        text_pos = text_surf.get_rect()
        if not pos:
            text_pos.center = self._screen.get_rect().center
        else:
            text_pos.center = pos
        self._screen.blit(text_surf, text_pos)

    def _blit_image(
        self,
        image: pg.Surface,
        pos: _Position,
        scale: float = 1,
        cover: bool = False,
        inverse: bool = False,
    ) -> None:
        img_size = image.get_size()
        screen_size = self._screen.get_size()
        if cover:
            transform_fn = lambda x, inverse: 1 / x if inverse else x
            scale *= transform_fn(
                compute_cover_scale_factor(img_size, screen_size), inverse
            )
        image, img_size = scale_surface(image, scale)
        if pos is None:
            pos = None, None
        x = pos[0] if pos[0] is not None else (screen_size[0] - img_size[0]) // 2
        y = pos[1] if pos[1] is not None else (screen_size[1] - img_size[1]) // 2
        self._screen.blit(image, (x, y))

    def _blit_overlay(self, opacity: float = 0.75) -> None:
        overlay = pg.Surface(self._screen.get_size())
        overlay.set_alpha(int(255 * opacity))
        overlay.fill("black")
        self._screen.blit(overlay, (0, 0))

    def _default_background(self) -> None:
        self._screen.fill(_config.get("gui.colors.background"))
        self._blit_image(self._get_image("background"), None, cover=True)

    def _default_bg_with_overlay(self, opacity: float = 0.75) -> None:
        self._default_background()
        self._blit_overlay(opacity)

    def _wait(self, secs: int) -> None:
        pg.event.pump()
        pg.time.wait(int(secs * 1000))
        pg.event.pump()

    def _show_photo_count(self, nth: int, total: int) -> None:
        self._default_bg_with_overlay()
        self._blit_text(
            f"{_config.get("gui.labels.photo_count", "")} {nth}/{total}",
            1 / 4,
        )
        self._flip()

    def _show_countdown(self, countdown: int) -> None:
        for i in range(countdown, 0, -1):
            self._default_bg_with_overlay()
            self._blit_text(str(i), 1 / 1.75)
            self._flip()
            self._wait(1)

    def show_init_screen(self) -> None:
        if not self._initialized:
            return
        self._default_background()
        self._blit_text(_config.get("gui.labels.init", ""), 1 / 4)
        self._flip()

    @deferred_init
    def show_token_screen(self) -> None:
        self._default_bg_with_overlay(0.3)
        self._blit_text(_config.get("gui.labels.token", ""), 1 / 4.5)
        self._flip()

    @deferred_init
    def show_button_screen(self) -> None:
        self._default_bg_with_overlay()
        y = self._screen.get_rect().centery
        self._blit_image(self._get_image("arrow"), (None, y + y // 4), 0.3, True, True)
        self._blit_text(_config.get("gui.labels.button", ""), 1 / 4.5)
        self._flip()

    @deferred_init
    def show_countdown_screen(self, photo_count: int) -> None:
        self._show_photo_count(photo_count, _config.get("photo.count"))
        self._wait(2)
        self._show_countdown(_config.get("photo.countdown"))
        self._blit_text(str(photo_count), 1 / 3)
        self._default_bg_with_overlay()
        self._blit_text(_config.get("gui.labels.pose"), 1 / 4)
        self._flip()
        self._wait(1)

    @deferred_init
    def show_print_preview(self, image: pg.Surface) -> None:
        self._default_bg_with_overlay()
        self._blit_image(image, None, 0.5, True)
        x, y = self._screen.get_size()
        self._blit_text(
            _config.get("gui.labels.print_preview"),
            1 / 8,
            (x // 2, y - y // 9),
        )
        self._flip()
        self._wait(5)

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
