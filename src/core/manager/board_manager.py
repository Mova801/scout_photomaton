# import RPi.GPIO as GPIO
from enum import Enum

from core.config import _config
from core.logger import _logger

_Pin = int


class PinType(Enum):
    OUT = 0  # GPIO.OUT
    IN = 1  # GPIO.IN


class PUD(Enum):
    OFF = 20  # GPIO.PUD_OFF
    DOWN = 21  # GPIO.PUD_DOWN
    UP = 22  # GPIO.PUD_UP


class PinState(Enum):
    LOW = 0  # GPIO.LOW
    HIGH = 1  # GPIO.HIGH


class Module:
    def __init__(self, name: str, pin: _Pin, type: PinType, pud: PUD) -> None:
        self.name = name
        self.pin = pin
        self.type = PinType(type)
        self.pud = PUD(pud)


class BoardManager:

    def __init__(
        self,
        modules: tuple[Module],
    ) -> None:
        # GPIO.setmode(GPIO.BCM)
        self.modules = {}
        for module in modules:
            self.modules[module.name] = module
            # GPIO.setup(pin, ptype, pull_up_down=ppud)
            spaces: int = max(0, 18 - len(module.name) - len(module.type.name) - 2)
            _logger.debug(
                f"Registered {module.name}({module.type.name}){'':{spaces}} (pin: {module.pin}, pud: {module.pud.name:3})"
            )

    def __getitem__(self, name: str) -> Module:
        res = self.modules.get(name, None)
        if not res:
            raise ModuleNotFoundError(f"Invalid module name: {name}")

    def get_pin_state(self, name: str, expected: PinState = PinState.LOW) -> None:
        # controllo il pin
        # pin = self.modules.get(name)[0]
        # if GPIO.input(pin) == expected:
        #   return True
        return False

    def set_pin_state(self, name: str, value: PinState) -> None:
        # pin = self.modules.get(name)[0]
        # GPIO.output(pin, value)
        ...

    def stop(self) -> None:
        # GPIO.cleanup
        ...
