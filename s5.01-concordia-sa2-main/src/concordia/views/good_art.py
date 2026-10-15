"""
File: good_art.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Loads the good tokens of assets/ and caches them at the needed
             size.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from concordia.views.card_art import fitted_size
from concordia.views.palette import MAP_BACKGROUND

# Pillow and ImageTk are optional: without them the drawn swatch is used.
try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - exercised by the CI image
    Image = ImageTk = None

# assets/ is next to src/, so the fourth parent is the project root.
GOOD_ROOT = Path(__file__).resolve().parents[3] / "assets" / "goods"

# The resized copies, kept per file, size and fade.
_PHOTOS: dict[tuple[Path, int, int, int, str], Any] = {}

# How far a token is faded when the map is behind a question.
FADE_STEPS = 100


def good_path(name: str) -> Path:
    """Where a good's token lives."""
    return GOOD_ROOT / f"{name.strip().lower()}.png"


def good_photo(name: str, box_width: float, box_height: float,
               fade: float = 0.0, toward: str = MAP_BACKGROUND) -> Any:
    """
    A good's token, sized to fit the box a view gives it.

    :param name: The name of the good, as the database spells it.
    :param box_width: The width the token has to fit in.
    :param box_height: The height it has to fit in.
    :param fade: How far the token is faded towards `toward`, 0 leaving it
        alone.
    :param toward: The colour it is faded towards.
    :return: The Tk image to draw, None when the good has no token or when
        Pillow is missing. The caller then draws the swatch itself.
    """
    if ImageTk is None:
        return None

    path = good_path(name)
    if not path.is_file():
        return None

    washed = round(min(max(fade, 0.0), 1.0) * FADE_STEPS)

    try:
        with Image.open(path) as picture:
            size = fitted_size(*picture.size, box_width, box_height)
            key = (path, *size, washed, toward)
            if key not in _PHOTOS:
                token = picture.convert("RGBA").resize(size, Image.LANCZOS)
                _PHOTOS[key] = ImageTk.PhotoImage(
                    _washed(token, washed / FADE_STEPS, toward)
                )
    except (OSError, ValueError, RuntimeError):
        # No file, or no Tk yet: the drawn swatch is used.
        return None

    return _PHOTOS[key]


def _washed(token: Any, fade: float, toward: str) -> Any:
    """
    Wash a token towards a colour, without filling in what it does not cover.

    :param token: The sized token.
    :param fade: How far to wash it, 0 leaving it alone.
    :param toward: The colour to wash it towards.
    :return: The washed token.
    """
    if fade <= 0:
        return token

    ground = Image.new("RGB", token.size, toward)
    washed = Image.blend(token.convert("RGB"), ground, fade)
    washed.putalpha(token.getchannel("A"))
    return washed


def clear_cache() -> None:
    """Drop every sized copy, as when a window is closed."""
    _PHOTOS.clear()
