import argparse
from pathlib import Path
from enum import Enum
import asyncio

import PIL.Image

from core.config import _config
from core.logger import _logger
from core.manager.camera_manager import CameraManager
from core.manager.printer_manager import PrinterManager
from core.manager.gui_manager import GuiManager, pg
from core.manager.board_manager import BoardManager, Module
from core.image_utils import merge_pics, pil_to_pygame, save_pic, cm_to_px


class _Mode(Enum):
    INVALID = None
    NORMAL = 1
    DEBUG = 2
    THREADED = 3
    THREADED_DEBUG = 4


class _App:

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args

    def _init(self) -> None:
        mode = _Mode(int(self.args.mode) if self.args.mode else _config.get("app.mode"))
        name = self.args.name if self.args.name else _config.get("app.name")
        fullscreen = (
            self.args.fullscreen
            if self.args.fullscreen
            else _config.get("app.display_mode")
        )
        deferred = self.args.deferred if self.args.deferred else False
        camera = (
            int(self.args.camera)
            if self.args.camera
            else _config.get("usb.camera.default")
        )

        _logger.info(
            f"{_config.get('app.name')} application v-{_config.get('app.version')} setup as {mode.name.lower()} ({int(mode.value)}) mode"
        )

        self._mode: bool = mode
        if mode == _Mode.DEBUG:
            _logger.setLevel("DEBUG")

        _logger.info("Initializing gui manager")
        self._gui: GuiManager = GuiManager(name, fullscreen, deferred)
        self._gui.show_init_screen()

        _logger.info("Initializing camera manager")
        self._camera: CameraManager = CameraManager(camera)

        _logger.info("Initializing printer manager")
        self._printer: PrinterManager = PrinterManager()

        _logger.info("Initializing board manager")
        pins_data = [
            Module(module, *_config.get(f"io.pins.{module}").values())
            for module in _config.get("io.pins")
        ]
        self._board: BoardManager = BoardManager(pins_data)
        photos_dir = Path(_config.get("paths.folders.photos"))
        if not photos_dir.exists():
            _logger.info("Creating missing directories")
            photos_dir.mkdir(parents=True, exist_ok=True)

    def prepare_final_pic(self) -> tuple[PIL.Image.Image, Path]:
        watermark_path = Path(_config.get("paths.folders.images")) / Path(
            _config.get_path("watermark")
        )
        pics = [PIL.Image.open(str(watermark_path.resolve()))]
        pics.extend([self._camera.pop_pic() for _ in range(_config.get("photo.count"))])
        format_size = self._printer.get_sheet_format_size(
            _config.get("usb.printer.sheet_format")
        )
        dpi = _config.get("usb.printer.dpi")
        format_size = cm_to_px(format_size, dpi)[::-1]
        margins = cm_to_px(_config.get("usb.printer.sheet_margins"), dpi)
        spacing = cm_to_px([_config.get("usb.printer.pics_spacing")], dpi)[0]
        pics_per_row = _config.get("usb.printer.pics_per_row")
        merged = merge_pics(format_size, pics, margins, spacing, pics_per_row)
        return merged, save_pic(
            merged,
            _config.get("paths.folders.photos"),
            _config.get("photo.prefix"),
            _config.get("photo.extension"),
        )

    def stop(self) -> None:
        _logger.info("Closing application")
        self._board.stop()
        self._gui.stop()

    def wait_module(self, pin: int) -> bool:
        while True:
            if self._mode == _Mode.DEBUG:
                if self._gui.is_pressed(pg.K_k):
                    _logger.info("Skip stage")
                    return True
            if self._board.get_pin_state(pin):
                _logger.info("A token has been registered")
                return True
            if self._gui.request_to_stop():
                _logger.info("A request to stop has been registered")
                return False

    def start(self) -> None:
        asyncio.run(self.run())

    async def run(self) -> None:
        self._init()
        _logger.info("Application started")
        pics_count: int = _config.get("photo.count")
        while True:
            # mostro schermata attesa gettone
            self._gui.show_token_screen()
            # aspetto inserimento gettone
            if not self.wait_module(_config.get("io.pins.microswitch.pin")):
                break
            # mostro schermata attesa pressione pulsante
            self._gui.show_button_screen()
            # aspetto pressione pulsante
            if not self.wait_module(_config.get("io.pins.button.pin")):
                break
            # avvio sequenza foto
            for i in range(1, pics_count + 1):
                _logger.info(f"Processing photo {i}/{pics_count}")
                self._gui.show_countdown_screen(i)
                self._camera.take_pic()
            # unisco le foto
            pic, pic_path = self.prepare_final_pic()
            # mostro schermata stampa in corso con riepilogo foto
            self._gui.show_print_preview(pil_to_pygame(pic))
            # avvio stampa foto e attendo il termine
            await self._printer.send_print_request(pic_path)
            # mostro schermata di saluti (fine)
        self.stop()


def parse_argv() -> dict[str, str]:
    parser = argparse.ArgumentParser()
    commands_config: dict[str] = _config.get("commands")
    for cmd_config in commands_config.values():
        names = []
        kwargs = {"help": cmd_config["help"]}

        if cmd_config.get("short", False):
            names.append(cmd_config["short"])
        if cmd_config.get("long", False):
            names.append(cmd_config["long"])

        if cmd_config.get("arg", False):
            kwargs["required"] = False
            kwargs["metavar"] = "VALUE"
        else:
            kwargs["action"] = "store_true"
        parser.add_argument(*names, **kwargs)
    return parser.parse_args()


def app_factory() -> _App:
    args = parse_argv()
    print(args)
    return _App(args)
    # app = _App(args)
    # if _Mode(int()) == _Mode.THREADED:
    #     raise NotImplementedError("La modalità threaded non è ancora implementata")
    # return app
