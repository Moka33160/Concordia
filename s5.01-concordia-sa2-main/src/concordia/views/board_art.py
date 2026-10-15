"""
File: board_art.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Loads the board texture of assets/ and caches it at the needed
             size.
"""
from __future__ import annotations

from math import ceil, floor
from pathlib import Path
from typing import Any

from concordia.views.card_art import rounded_corners
from concordia.views.palette import MAP_BACKGROUND, MAP_MUTE

# Pillow and ImageTk are optional: without them the board is drawn flat.
try:
    from PIL import Image, ImageDraw, ImageFilter, ImageTk
except ImportError:  # pragma: no cover - exercised by the CI image
    Image = ImageDraw = ImageFilter = ImageTk = None

# assets/ is next to src/, so the fourth parent is the project root.
PAPER = (
    Path(__file__).resolve().parents[3]
    / "assets" / "background" / "paper.jpg"
)

# How much of the paper texture is kept over the parchment.
TEXTURE_STRENGTH = 0.45

# How far the edge of a province area is blurred.
GROUND_FEATHER = 2.0

# The resized copies, kept per board.
_PHOTOS: dict[tuple, Any] = {}


def _cover(picture: Any, width: int, height: int) -> Any:
    """
    Fill a box with a picture, cropping rather than stretching it.

    :param picture: The paper.
    :param width: The width to cover.
    :param height: The height to cover.
    :return: The picture, exactly `width` by `height`.
    """
    scale = max(width / picture.width, height / picture.height)
    sized = picture.resize(
        (max(width, round(picture.width * scale)),
         max(height, round(picture.height * scale))),
        Image.LANCZOS,
    )
    left = (sized.width - width) // 2
    top = (sized.height - height) // 2
    return sized.crop((left, top, left + width, top + height))


def _wash(paper: Any, color: str, points: tuple, strength: float) -> None:
    """
    Lay one province's ground into the paper, in place.

    :param paper: The paper to print the ground into.
    :param color: The province's tint.
    :param points: The region, as the polygon's own points.
    :param strength: How much of the tint the paper keeps, 0 to 1.
    """
    margin = ceil(GROUND_FEATHER * 3)
    left = max(0, floor(min(x for x, _y in points)) - margin)
    top = max(0, floor(min(y for _x, y in points)) - margin)
    right = min(paper.width, ceil(max(x for x, _y in points)) + margin)
    bottom = min(paper.height, ceil(max(y for _x, y in points)) + margin)

    if right <= left or bottom <= top:
        return

    box = (right - left, bottom - top)
    mask = Image.new("L", box, 0)
    ImageDraw.Draw(mask).polygon(
        [(x - left, y - top) for x, y in points],
        fill=round(255 * strength),
    )
    paper.paste(
        Image.new("RGB", box, color), (left, top),
        mask.filter(ImageFilter.GaussianBlur(GROUND_FEATHER)),
    )


def board_photo(width: float, height: float, radius: int = 0,
                recede: bool = False, grounds: tuple = ()) -> Any:
    """
    The paper the board is printed on, cut to the board's own size.

    :param width: The board's width.
    :param height: The board's height.
    :param radius: The corner radius the board is drawn with.
    :param recede: Whether the map is behind a question, which fades the paper
        too.
    :param grounds: One (tint, points, strength) per province to draw into the
        paper, the points being its polygon in the coordinates of the paper. A
        tuple and not a list, because the cache key holds it.
    :return: The Tk image to draw, None when there is no paper or no Pillow.
        The caller then fills the board flat.
    """
    if ImageTk is None or not PAPER.is_file():
        return None

    box = (max(1, round(width)), max(1, round(height)))
    key = (*box, radius, recede, grounds)

    if key in _PHOTOS:
        return _PHOTOS[key]

    try:
        with Image.open(PAPER) as picture:
            paper = _cover(picture.convert("RGB"), *box)
            ground = Image.new("RGB", box, MAP_BACKGROUND)
            paper = Image.blend(ground, paper, TEXTURE_STRENGTH)

            for color, points, strength in grounds:
                _wash(paper, color, points, strength)

            # The provinces fade with the paper, so the whole map fades evenly.
            if recede:
                paper = Image.blend(paper, ground, MAP_MUTE)

            _PHOTOS[key] = ImageTk.PhotoImage(
                rounded_corners(paper.convert("RGBA"), radius)
            )
    except (OSError, ValueError, RuntimeError):
        # No file, or no Tk yet: the board is drawn flat.
        return None

    return _PHOTOS[key]


def clear_cache() -> None:
    """Drop every sized copy, as when a window is closed."""
    _PHOTOS.clear()
