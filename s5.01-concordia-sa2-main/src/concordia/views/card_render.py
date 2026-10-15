"""
File: card_render.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 09-09-2026
Description: Draws a card face, used by the hand, the market and the detail
             panel.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.views.card_art import card_photo, deck_numeral
from concordia.views.good_art import good_photo
from concordia.views.palette import (
    CARD_BANNER, CARD_BORDER, CARD_FACE, CARD_GOD_BAND, CARD_HEIGHT,
    CARD_INK, CARD_MUTE, CARD_NAME_BAND, CARD_SHADOW, CARD_SELECTED,
    CARD_WIDTH, HIGHLIGHT, HIGHLIGHT_WIDTH, blend, serif,
)

if TYPE_CHECKING:
    import tkinter as tk

    from concordia.models.card import Card
    from concordia.models.market import DisplaySlot

# Stands for a good of the player's choice, asked at some display slots.
ANY_GOOD = "?"

# The size of one good of the price, and of the token beside the name.
COST_SWATCH = 13
GOOD_DOT = 11


def cost_colors(card: Card) -> list[str]:
    """List the colour of every good the card is bought with."""
    return [good.color for good in card.cost]


def subtitle(card: Card) -> str:
    """The line under the card name: its god, and the deck it is sold in."""
    parts = [
        part for part in (
            card.god.name if card.god is not None else "",
            deck_numeral(card.deck_number),
        ) if part
    ]
    return " · ".join(parts)


def slot_cost(slot: DisplaySlot | None) -> list[str]:
    """What buying from a display position costs, one entry per good."""
    if slot is None:
        return []

    owed = []
    if slot.good is not None:
        owed += [slot.good] * max(slot.n_goods or 1, 1)
    if slot.any_good_required:
        owed.append(ANY_GOOD)
    return owed


def card_bands(scale: float = 1.0) -> tuple[float, float, float]:
    """The three horizontal bands a card face is built from, top to bottom."""
    name = CARD_NAME_BAND * scale
    god = CARD_GOD_BAND * scale
    return name, CARD_HEIGHT * scale - name - god, god


# The functions below only use the canvas they are given, so Tkinter is not
# imported here.


def _scaled(base: int, scale: float, floor: int = 1) -> int:
    """Scale a base size, never below `floor`."""
    return max(floor, round(base * scale))


def rounded_points(x1: float, y1: float, x2: float, y2: float,
                   radius: float) -> list[float]:
    """
    The point ring drawing a rounded rectangle, for a smoothed polygon.

    :param x1: The left edge.
    :param y1: The top edge.
    :param x2: The right edge.
    :param y2: The bottom edge.
    :param radius: How far from each corner the curve starts, clamped to half
        the shorter side so the outline never crosses itself.
    :return: The flat x, y list `create_polygon` takes.
    """
    radius = min(radius, abs(x2 - x1) / 2, abs(y2 - y1) / 2)
    return [
        x1 + radius, y1, x1 + radius, y1,
        x2 - radius, y1, x2 - radius, y1,
        x2, y1,
        x2, y1 + radius, x2, y1 + radius,
        x2, y2 - radius, x2, y2 - radius,
        x2, y2,
        x2 - radius, y2, x2 - radius, y2,
        x1 + radius, y2, x1 + radius, y2,
        x1, y2,
        x1, y2 - radius, x1, y2 - radius,
        x1, y1 + radius, x1, y1 + radius,
        x1, y1,
    ]


def draw_rounded_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float,
                      y2: float, radius: float, tag: str, **options):
    """
    Draw a rounded rectangle, taking the options `create_polygon` takes.

    :param canvas: The canvas drawn onto.
    :param x1: The left edge.
    :param y1: The top edge.
    :param x2: The right edge.
    :param y2: The bottom edge.
    :param radius: The corner radius.
    :param tag: The tag the shape is given.
    :return: The canvas item id of the shape.
    """
    return canvas.create_polygon(
        rounded_points(x1, y1, x2, y2, radius),
        smooth=True, splinesteps=12, tags=tag, **options,
    )


def face_border(selected: bool, highlighted: bool) -> tuple[str, int]:
    """
    The rim a card face is drawn with.

    :param selected: Whether the detail overlay is open on this card.
    :param highlighted: Whether the running action offers this card.
    :return: The rim's colour and its width, before scaling.
    """
    if highlighted:
        return HIGHLIGHT, HIGHLIGHT_WIDTH
    if selected:
        return CARD_SELECTED, 2
    return CARD_BORDER, 2


def draw_card_face(canvas: tk.Canvas, card: Card, x: float, y: float,
                   scale: float = 1.0, tag: str = "card",
                   selected: bool = False, highlighted: bool = False,
                   dimmed: bool = False) -> tuple[float, float]:
    """
    Draw one card face, top-left anchored, onto an existing canvas.

    :param canvas: The canvas drawn onto.
    :param card: The card whose face is drawn.
    :param x: The left edge of the face.
    :param y: The top edge of the face.
    :param scale: The size relative to the resting hand card.
    :param tag: The tag every item of the face is given.
    :param selected: Whether to draw the face with the selected border.
    :param highlighted: Whether the action offers this card, which rims it in
        gold.
    :param dimmed: Whether to fade the face, for a card that cannot be played.
    :return: The (width, height) the face was drawn at.
    """
    width = CARD_WIDTH * scale
    height = CARD_HEIGHT * scale
    pad = _scaled(5, scale)
    radius = _scaled(9, scale)
    border, border_width = face_border(selected, highlighted)

    photo = card_photo(card, width, height, radius, dimmed=dimmed)

    # A picture of another shape comes back smaller, so the rim follows the
    # picture.
    drawn_width = width if photo is None else photo.width()
    drawn_height = height if photo is None else photo.height()
    left = x + (width - drawn_width) / 2
    top = y + (height - drawn_height) / 2

    draw_rounded_rect(
        canvas, left + pad, top + pad, left + drawn_width + pad,
        top + drawn_height + pad, radius, tag, fill=CARD_SHADOW, outline="",
    )

    if photo is None:
        _draw_plain_face(canvas, card, x, y, width, height, radius, scale,
                         tag, dimmed)
    else:
        canvas.create_image(
            left + drawn_width / 2, top + drawn_height / 2, image=photo,
            tags=tag,
        )

    # Drawn last, so the rim stays crisp over the face and the text.
    draw_rounded_rect(
        canvas, left, top, left + drawn_width, top + drawn_height, radius,
        tag, fill="", outline=border, width=_scaled(border_width, scale),
    )
    return width, height


def _spent(color: str, dimmed: bool) -> str:
    """
    The colour of a drawn face, faded when the card cannot be played.

    :param color: The colour the band is normally drawn in.
    :param dimmed: Whether the card is spent.
    :return: The colour to draw with.
    """
    return blend(color, CARD_SHADOW, CARD_MUTE) if dimmed else color


def _draw_plain_face(canvas: tk.Canvas, card: Card, x: float, y: float,
                     width: float, height: float, radius: float,
                     scale: float, tag: str, dimmed: bool = False) -> None:
    """
    Build a card face out of bands, for a card assets/ has no picture of.

    :param canvas: The canvas drawn onto.
    :param card: The card whose face is drawn.
    :param x: The left edge of the face.
    :param y: The top edge of the face.
    :param width: The width of the face.
    :param height: The height of the face.
    :param radius: The corner radius of the face.
    :param scale: The size relative to the resting hand card.
    :param tag: The tag every item of the face is given.
    :param dimmed: Whether the card cannot be played, which drains it.
    """
    name_band, _body, god_band = card_bands(scale)
    face = _spent(CARD_FACE, dimmed)
    banner = _spent(CARD_BANNER, dimmed)

    draw_rounded_rect(
        canvas, x, y, x + width, y + height, radius, tag,
        fill=face, outline="",
    )

    # Each band follows the corners at one end and is squared off at the other.
    draw_rounded_rect(
        canvas, x, y, x + width, y + name_band, radius, tag,
        fill=banner, outline="",
    )
    canvas.create_rectangle(
        x, y + radius, x + width, y + name_band,
        fill=banner, outline="", tags=tag,
    )
    canvas.create_text(
        x + width / 2, y + name_band / 2, text=card.name,
        font=serif(_scaled(10, scale), "bold"), fill=face,
        width=width - _scaled(6, scale), justify="center", tags=tag,
    )

    god_top = y + height - god_band
    draw_rounded_rect(
        canvas, x, god_top, x + width, y + height, radius, tag,
        fill=banner, outline="",
    )
    canvas.create_rectangle(
        x, god_top, x + width, y + height - radius,
        fill=banner, outline="", tags=tag,
    )
    canvas.create_text(
        x + width / 2, god_top + god_band / 2, text=subtitle(card) or "—",
        font=serif(_scaled(8, scale), "italic"), fill=face,
        width=width - 4, tags=tag,
    )

    if card.good is not None:
        dot = _scaled(GOOD_DOT, scale)
        _draw_good(canvas, card.good, x + width - dot * 1.4,
                   y + name_band + dot * 0.9, dot, tag, dimmed)

    _draw_cost(canvas, card, x, y, width, scale, tag, dimmed)


def _draw_cost(canvas: tk.Canvas, card: Card, x: float, y: float,
               width: float, scale: float, tag: str,
               dimmed: bool = False) -> None:
    """Draw the row of swatches a card is bought with, across its body."""
    if not card.cost:
        return

    name_band, body_band, _god = card_bands(scale)
    swatch = _scaled(COST_SWATCH, scale)
    gap = _scaled(3, scale)
    row_width = len(card.cost) * swatch + (len(card.cost) - 1) * gap
    left = x + (width - row_width) / 2
    top = y + name_band + (body_band - swatch) / 2

    for index, good in enumerate(card.cost):
        offset = left + index * (swatch + gap)
        _draw_good(canvas, good, offset + swatch / 2, top + swatch / 2,
                   swatch, tag, dimmed)


def _draw_good(canvas: tk.Canvas, good, cx: float, cy: float, size: float,
               tag: str, dimmed: bool) -> None:
    """
    One good on a drawn face: its printed token, centred on a point.

    :param canvas: The canvas drawn onto.
    :param good: The good to print.
    :param cx: The x to centre it on.
    :param cy: The y to centre it on.
    :param size: The largest it may be drawn, on either side.
    :param tag: The tag the swatch is given.
    :param dimmed: Whether the card is spent, which drains the token as far as
        the bands around it.
    """
    token = good_photo(
        good.name, size, size, CARD_MUTE if dimmed else 0.0, CARD_SHADOW,
    )

    if token is not None:
        canvas.create_image(cx, cy, image=token, tags=tag)
        return

    edge = size / 2
    canvas.create_rectangle(
        cx - edge, cy - edge, cx + edge, cy + edge,
        fill=_spent(good.color, dimmed), outline=_spent(CARD_INK, dimmed),
        tags=tag,
    )
