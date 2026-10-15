"""
File: piece_art.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Draws the houses and the colonists in the color of their owner.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from concordia.views.palette import MAP_INK
from concordia.views.svg_art import Glyph, read_glyph, render

# ImageTk is optional: without it the views draw the plain shapes.
try:
    from PIL import ImageTk
except ImportError:  # pragma: no cover - exercised by the CI image
    ImageTk = None

# assets/ is next to src/, so the fourth parent is the project root.
PION_ROOT = Path(__file__).resolve().parents[3] / "assets" / "pions"

# What a house is filed under.
HOUSE = "house"
COLONIST = "colonist"

# The outlines, read once, and the resized coloured copies.
_GLYPHS: dict[str, Glyph | None] = {}
_PHOTOS: dict[tuple[str, int, int, str, str], Any] = {}


def colonist_kind(way: str) -> str:
    """What a colonist travelling one way is filed under."""
    return f"{COLONIST}-{way.strip().lower()}"


def piece_path(kind: str) -> Path:
    """Where a piece's outline lives."""
    return PION_ROOT / f"{kind}.svg"


def piece_glyph(kind: str) -> Glyph | None:
    """A piece's outline, read off disk once and kept."""
    if kind not in _GLYPHS:
        path = piece_path(kind)
        _GLYPHS[kind] = read_glyph(path) if path.is_file() else None

    return _GLYPHS[kind]


def piece_photo(kind: str, box_width: float, box_height: float, fill: str,
                outline: str = MAP_INK) -> Any:
    """
    A piece, sized to its box and filled with the colour of a player.

    :param kind: The piece, `HOUSE` or a `colonist_kind`.
    :param box_width: The width the piece has to fit in.
    :param box_height: The height it has to fit in.
    :param fill: The colour to draw it in, so the one of its owner.
    :param outline: The keyline drawn around it, so a dark piece stays visible
        on a route.
    :return: The Tk image to draw, None when the piece has no picture or when
        Pillow is missing. The caller then draws the shape itself.
    """
    if ImageTk is None:
        return None

    glyph = piece_glyph(kind)
    if glyph is None:
        return None

    box = (max(1, round(box_width)), max(1, round(box_height)))
    key = (kind, *box, fill, outline)

    if key not in _PHOTOS:
        try:
            drawn = render(glyph, *box, fill, outline)
            _PHOTOS[key] = ImageTk.PhotoImage(drawn)
        except (ValueError, RuntimeError):
            # A bad colour, or no Tk yet: the plain shape is drawn instead.
            return None

    return _PHOTOS[key]


def clear_cache() -> None:
    """Drop every sized copy, as when a window is closed."""
    _PHOTOS.clear()
    _GLYPHS.clear()
