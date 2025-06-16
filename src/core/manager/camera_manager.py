import platform
import cv2
from enum import StrEnum

from core.exceptions import CameraNotReadyError, CannotTakePictureError
from core.logger import _logger


class OperativeSystem(StrEnum):
    WINDOWS = "Windows"
    LINUX = "Linux"


def _get_windows_camera_name(id: int) -> str:
    try:
        import logging

        # Sopprime i log di comtypes
        logging.getLogger("comtypes").setLevel(logging.ERROR)

        from pygrabber.dshow_graph import FilterGraph

        devices = FilterGraph().get_input_devices()
        return devices[0].replace(" ", "_")
    except ImportError:
        return "NONE"


def _get_linux_camera_name(id: int) -> str:
    try:
        with open(f"/sys/class/video4linux/video{id}/name", "r") as f:
            return f.read().strip()
    except (FileNotFoundError, PermissionError):
        return "NONE"


def _get_camera_name(id: int) -> str:
    os_name = platform.system()
    match os_name:
        case OperativeSystem.WINDOWS:
            return _get_windows_camera_name(id)
        case OperativeSystem.LINUX:
            return _get_linux_camera_name(id)


class CameraManager:

    def __init__(self, camera_id: int = 0):
        cv2.setLogLevel(0)
        self._camera_id = camera_id
        self._initialized = False
        self._init_camera()
        self._name = _get_camera_name(camera_id)
        _logger.debug(f"Opened camera {self._name}({self._camera_id})")

    def _init_camera(self) -> None:
        self._camera = cv2.VideoCapture(self._camera_id)
        self._initialized = True

    def take_picture(self) -> None:
        if not self._initialized:
            raise CameraNotReadyError(f"Camera {self._camera_id} not ready")
