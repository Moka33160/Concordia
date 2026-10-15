"""
File: card_art.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Loads the card pictures of assets/ and caches them at the needed
             size.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from concordia.models.card import CardOrigin

if TYPE_CHECKING:
    from concordia.models.card import Card

# Pillow and ImageTk are optional: without them the drawn face is used.
try:
    from PIL import Image, ImageDraw, ImageEnhance, ImageTk
except ImportError:  # pragma: no cover - exercised by the CI image
    Image = ImageDraw = ImageEnhance = ImageTk = None

# assets/ is next to src/, so the fourth parent is the project root.
ART_ROOT = Path(__file__).resolve().parents[3] / "assets" / "cards"

ROMAN = ["", "I", "II", "III", "IV", "V"]

# Every other card file is named after the card, in lowercase.
SLUG_ALIASES = {
    "PRÆFECTVS MAGNVS": "prefectus-magnus",
}

# The resized copies, kept per file and per size.
_PHOTOS: dict[tuple[Path, int, int, int, bool], Any] = {}

# How an unplayable card is drawn: less colour and less light.
SPENT_COLOR = 0.25
SPENT_BRIGHTNESS = 0.55


def deck_numeral(deck_number: int | None) -> str:
    """Spell a deck number as the roman numeral the box prints on the deck."""
    if deck_number is None or not 0 < deck_number < len(ROMAN):
        return ""
    return ROMAN[deck_number]


def card_slug(name: str) -> str:
    """The file name a card's picture is saved under, without extension."""
    return SLUG_ALIASES.get(name, name.lower())


def card_path(card: Card) -> Path | None:
    """Where the picture of a card is, in the folder of its origin."""
    slug = f"{card_slug(card.name)}.png"

    if card.origin is CardOrigin.STARTING:
        return ART_ROOT / "starting" / slug
    if card.origin is CardOrigin.MARKET:
        numeral = deck_numeral(card.deck_number)
        return ART_ROOT / "for-sale" / numeral / slug if numeral else None
    return ART_ROOT / slug


def fitted_size(source_width: int, source_height: int, box_width: float,
                box_height: float) -> tuple[int, int]:
    """
    The largest size a picture fits its box at without being stretched.

    :param source_width: The picture's width.
    :param source_height: The picture's height.
    :param box_width: The width the picture has to fit in.
    :param box_height: The height the picture has to fit in.
    :return: The (width, height) to draw it at, never a side below 1.
    """
    if source_width <= 0 or source_height <= 0:
        return max(1, round(box_width)), max(1, round(box_height))

    scale = min(box_width / source_width, box_height / source_height)
    return (
        max(1, round(source_width * scale)),
        max(1, round(source_height * scale)),
    )


def rounded_corners(picture: Any, radius: int) -> Any:
    """
    Round a picture's corners off, by cutting them out of its alpha.

    :param picture: The RGBA picture to round, modified in place.
    :param radius: How far from each corner the curve starts; 0 leaves the
        picture square.
    :return: The rounded picture.
    """
    if radius <= 0:
        return picture

    mask = Image.new("L", picture.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, picture.width - 1, picture.height - 1), radius, fill=255,
    )
    picture.putalpha(mask)
    return picture


def spend(picture: Any) -> Any:
    """Drain a picture's colour and light, for a card that cannot be played."""
    drained = ImageEnhance.Color(picture).enhance(SPENT_COLOR)
    return ImageEnhance.Brightness(drained).enhance(SPENT_BRIGHTNESS)


def card_photo(card: Card, box_width: float, box_height: float,
               radius: int = 0, dimmed: bool = False) -> Any:
    """
    A card's picture, sized to fit the box a view gives it.

    :param card: The card to picture.
    :param box_width: The width the picture has to fit in.
    :param box_height: The height the picture has to fit in.
    :param radius: The corner radius to cut the picture to.
    :param dimmed: Whether to fade it, for a card that cannot be played.
    :return: The Tk image to draw, None when the card has no picture or when
        Pillow is missing. The caller then draws the face itself.
    """
    if ImageTk is None:
        return None

    path = card_path(card)
    if path is None or not path.is_file():
        return None

    try:
        with Image.open(path) as picture:
            size = fitted_size(*picture.size, box_width, box_height)
            key = (path, *size, radius, dimmed)
            if key not in _PHOTOS:
                sized = picture.convert("RGBA").resize(size, Image.LANCZOS)
                if dimmed:
                    sized = spend(sized)
                _PHOTOS[key] = ImageTk.PhotoImage(
                    rounded_corners(sized, radius)
                )
    except (OSError, ValueError, RuntimeError):
        # No file, or no Tk yet: the drawn face is used.
        return None

    return _PHOTOS[key]


def clear_cache() -> None:
    """Drop every sized copy, as when a window is closed."""
    _PHOTOS.clear()
