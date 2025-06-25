from enum import Enum, StrEnum
from pathlib import Path
import platform
import asyncio

# import cups

from core import exceptions
import asyncio
from core.utils import System
from core.config import _config
from core.logger import _logger

_Size = tuple[int, int]


class SheetFormat(StrEnum):
    A4 = "A4"
    A5 = "A5"
    A6 = "A6"


"""
A4 (DPI: 300, w: 21.0, h: 29.7, pxw: 2480, pxh: 3508)
A5 (DPI: 300, w: 14.8, h: 21.0, pxw: 1748, pxh: 2480)
A6 (DPI: 300, w: 10.5, h: 14.8, pxw: 1248, pxh: 1748)
"""

SHEET_FORMATS_SIZES_CM: dict[SheetFormat, _Size] = {
    SheetFormat.A4: (21.0, 29.7),
    SheetFormat.A5: (14.8, 21.0),
    SheetFormat.A6: (10.5, 14.8),
}
"""Dimensioni di vari formati di fogli in cm."""


class PrinterJobStates(Enum):
    PENDING = 3  # in attesa
    PENDING_HELD = 4  # in attesa, bloccato
    PROCESSING = 5  # in elaborazione
    PROCESSING_STOPPED = 6  # elaborazione fermata
    CANCELED = 7  # annullato
    ABORTED = 8  # interrotto
    COMPLETED = 9  # completato


class PrinterManager:

    def __init__(self):
        pass

    def get_sheet_format_size(self, format: SheetFormat | str) -> _Size:
        if type(format) == str:
            format = SheetFormat(format)
        size = SHEET_FORMATS_SIZES_CM.get(format)
        if not size:
            raise exceptions.PrinterInvalidSheetFormatError(
                f"Invalid sheet format: {format.name}"
            )
        return size

    def _start_printer_job_win(self, filename: Path) -> None:
        # import win32ui
        import win32print

        printer_name = win32print.GetDefaultPrinter()
        _logger.debug(f"Printing {filename} on printer {printer_name}")
        return

        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC()
        job_id = None
        try:
            job_id = hdc.StartDoc("Stampa Immagine")
            hdc.StartPage()

            dib = ImageWin.Dib(img)
            dib.draw(hdc.GetHandleOutput(), (0, 0, img.width, img.height))

            hdc.EndPage()
            hdc.EndDoc()

            if job_id:
                monitor_thread = threading.Thread(
                    target=monitora_job, args=(printer_name, job_id, callback)
                )
                monitor_thread.start()

        finally:
            hdc.DeleteDC()

        return job_id

    async def _print_windows(self, filename) -> None:
        self._start_printer_job_win(filename)
        # aspetta il thread in corso (stampa)

    async def _print_linux(self) -> None:
        pass

    async def send_print_request(self, filename: Path) -> bool:
        os_name = platform.system()
        match os_name:
            case System.WINDOWS:
                return await self._print_windows(filename)
            case System.LINUX:
                return await self._print_linux(filename)
