import platform
import PIL
import PIL.Image
import cv2
import queue

from core.exceptions import (
    CameraNotReadyError,
    CannotTakePictureError,
    InvalidCameraIndexError,
)
from core.utils import System
from core.image_utils import cv2_to_PIL
from core.config import _config
from core.logger import _logger


class CameraManager:

    def __init__(
        self, camera_id: int = 0, queue_size: int = _config.get("photo.queue_size")
    ):
        cv2.setLogLevel(0)
        self._pics_queue: queue.Queue[PIL.Image.Image] = queue.Queue(queue_size)
        self._camera = None
        self._camera_id = camera_id
        self._init_camera()
        self._name = self._get_camera_name(self._camera_id)
        _logger.debug(f"Camera {self._name}({self._camera_id}) opened")

    def _init_camera(self) -> None:
        if self._camera and self._camera.isOpened():
            return

        self._camera = cv2.VideoCapture(self._camera_id)
        if self._camera.isOpened():
            return
        else:
            self._camera.release()
        _logger.warning(f"Can't open camera [{self._camera_id}], trying default [0]")
        if self._camera_id != 0:
            self._camera = cv2.VideoCapture(0)
            if self._camera.isOpened():
                self._camera_id = 0
                return
        raise InvalidCameraIndexError(f"Camera {self._camera_id} not found")

    def _get_windows_camera_name(self, id: int) -> str:
        try:
            import logging

            logging.getLogger("comtypes").setLevel(logging.ERROR)
            from pygrabber.dshow_graph import FilterGraph

            devices = FilterGraph().get_input_devices()
            print(devices)
            return devices[id].replace(" ", "_")
        except ImportError:
            return "NONE"

    # TODO: testare la funzione per Linux
    def _get_linux_camera_name(self, id: int) -> str:
        try:
            with open(f"/sys/class/video4linux/video{id}/name", "r") as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError):
            return "NONE"

    def _get_camera_name(self, id: int) -> str:
        os_name = platform.system()
        match os_name:
            case System.WINDOWS:
                return self._get_windows_camera_name(id)
            case System.LINUX:
                return self._get_linux_camera_name(id)

    def _enqueue_image(self, image: PIL.Image.Image) -> None:
        self._pics_queue.put_nowait(image)

    def pop_pic(self) -> PIL.Image.Image:
        try:
            image = self._pics_queue.get_nowait()
        except queue.Empty:
            _logger.warning("Can't save picture: CameraManager pics queue is empty.")
            return None
        return image

    def take_pic(self) -> None:
        if not self._camera.isOpened():
            raise CameraNotReadyError(f"Camera {self._camera_id} not ready")
        result, image = self._camera.read()
        if not result:
            raise CannotTakePictureError("Can't take photo")
        self._enqueue_image(cv2_to_PIL(image))
        if self._pics_queue.qsize() == self._pics_queue.maxsize:
            _logger.info(
                f"CameraManager pics queue reached full capacity [{self._pics_queue.maxsize}]. Process it to avoid errors"
            )
        return image
