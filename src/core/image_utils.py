from pathlib import Path
from typing import Any
import PIL.Image
import pygame as pg
import math
import cv2

from core import string_utils

_Size = tuple[int, int]


UNIT_INCH: int = 2.54


def cv2_to_PIL(image: Any) -> PIL.Image.Image:
    color_converted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return PIL.Image.fromarray(color_converted)


def pil_to_pygame(image: PIL.Image.Image) -> pg.Surface:
    if image.mode != "RGB":
        image = image.convert("RGB")
    raw = image.tobytes()
    size = image.size
    return pg.image.fromstring(raw, size, "RGB")


def cm_to_px(cm_values: tuple[float], dpi: float) -> tuple[float]:
    conv = lambda x: (x * dpi) / UNIT_INCH
    return [conv(cm_val) for cm_val in cm_values]


def compute_cover_scale_factor(cover_size: _Size, bg_size: _Size) -> float:
    img_w, img_h = cover_size
    bg_w, bg_h = bg_size
    numerator_fn = min if img_w > bg_w and img_h > bg_h else max
    denominator_fn = max if img_w > bg_w and img_h > bg_h else min

    scale_x = numerator_fn(img_w, bg_w) / denominator_fn(img_w, bg_w)
    scale_y = numerator_fn(img_h, bg_h) / denominator_fn(img_h, bg_h)

    return denominator_fn(scale_x, scale_y)


def scale_surface(surface: pg.Surface, scale: float) -> tuple[pg.Surface, _Size]:
    size = surface.get_size()
    if scale == 1:
        return surface, size
    scaled_size = (size[0] * scale, size[1] * scale)
    return pg.transform.smoothscale(surface, scaled_size), scaled_size


def save_pic(image: PIL.Image.Image, path: Path, prefix: str, extension: str) -> None:
    filename = string_utils.generate_valid_filename(
        path,
        prefix,
        extension,
    )
    image.save(str(filename.resolve()))
    return filename


def merge_pics(
    merged_size: _Size,
    pics: tuple[PIL.Image.Image],
    margins: tuple[float, float, float, float],
    pics_spacing: float,
    qt_x_row: float = 2,
) -> PIL.Image.Image:
    """Handles correctly 1, 3 and 4, ... pictures."""
    qt_x_row = max(1, qt_x_row)
    w = int(
        (merged_size[0] - margins[1] - margins[3] - pics_spacing * (qt_x_row - 1))
        / qt_x_row
    )
    h = int(
        (merged_size[1] - margins[0] - margins[2] - pics_spacing * (qt_x_row - 1))
        / qt_x_row
    )
    resized = []
    merged_size = [int(s) for s in merged_size]
    merged = PIL.Image.new("RGB", merged_size, "white")
    y = margins[0]
    rows = math.ceil(len(pics) / qt_x_row)
    for i in range(rows):
        x = margins[3]
        col_start = math.ceil(i * len(pics) / qt_x_row)
        col_end = math.ceil((i + 1) * len(pics) / qt_x_row)
        for pic in pics[col_start:col_end]:
            res = pic.resize((w, h))
            resized.append(res)
            merged.paste(res, (int(x), int(y)))
            x += w + pics_spacing
        y += h + pics_spacing
    return merged
