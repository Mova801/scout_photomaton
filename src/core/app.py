import argparse
from threading import Thread
from enum import Enum

from core.config import _config
from core.logger import _logger
from core.manager.camera_manager import CameraManager
from core.manager.printer_manager import PrinterManager
from core.manager.gui_manager import GuiManager, pg
from core.manager.board_manager import BoardManager, Module


class _Mode(Enum):
    NORMAL = 0
    DEBUG = 1
    THREADED = 2
    THREADED_DEBUG = 3


class _App:

    def __init__(
        self,
        name: str,
        mode: _Mode = False,
        fullscreen: bool = False,
        deferred: bool = False,
    ) -> None:

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
        self._camera: CameraManager = CameraManager(_config.get("camera.default"))

        _logger.info("Initializing printer manager")
        self._printer: PrinterManager = PrinterManager()

        _logger.info("Initializing board manager")
        pins_data = [
            Module(module, *_config.get(f"io.pins.{module}").values())
            for module in _config.get("io.pins")
        ]
        self._board: BoardManager = BoardManager(pins_data)

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
        _logger.info("Application started")
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
        # salvo le foto
        # mostro schermata stampa in corso con riepilogo foto
        # unisco le foto
        # avvio stampa foto e attendo il termine
        # mostro schermata di saluti (fine)
        self.stop()


def parse_argv() -> dict[str, str]:
    parser = argparse.ArgumentParser()
    commands_config = _config.get("commands")
    for _, cmd_config in commands_config.items():
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
    name = args.name if args.name else _config.get("app.name")
    mode = _Mode(int(args.mode if args.mode else _config.get("app.mode")))
    fullscreen = bool(args.fullscreen) if args.fullscreen is not None else False
    deferred = args.deferred

    # print(args)
    app = _App(name, mode, fullscreen, deferred)
    if mode == _Mode.THREADED:
        raise NotImplementedError("La modalità threaded non è ancora implementata")
    return app
