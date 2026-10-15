"""
File: played_card.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 11-09-2026
Description: The card a player is playing, shown face up while it is played.
"""
from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from concordia.views.card_render import draw_card_face, draw_rounded_rect
from concordia.views.palette import (
    CARD_HEIGHT, CARD_SHADOW, CARD_WIDTH, MAP_INK, MUTED_COLOR,
    PANEL_BACKGROUND, PANEL_EDGE, SIZE_MICRO, SIZE_SMALL, SPACE_2, SPACE_3,
    TEXT_COLOR, sans, serif,
)

if TYPE_CHECKING:
    from concordia.models.card import Card
    from concordia.views.layout import Layout

TAG = "played-card"

# The scale the card is laid down at.
PLACARD_SCALE = 0.82

# How far the placard keeps from the corner of the map band.
INSET = 14

# How wide the caption under the card may run before it wraps.
CAPTION_WIDTH = 190


class PlayedCard:
    """The placard showing whose turn it is and what they laid down."""

    def __init__(self, canvas: tk.Canvas, layout: Layout):
        """
        :param canvas: The table canvas the placard is drawn on.
        :param layout: Where the bands of the table fall, for the corner
            of the map band to sit in.
        """
        self.canvas = canvas
        self.layout = layout
        self.card: Card | None = None
        self._who = ""
        self._color = ""
        self._caption = ""

    @property
    def is_open(self) -> bool:
        """Whether a card is laid down right now."""
        return self.card is not None

    def show(self, card: Card, who: str, color: str,
             caption: str = "") -> None:
        """
        Lay a card down, replacing whatever was there.

        :param card: The card being played.
        :param who: The name of the seat playing it.
        :param color: That seat's colour, for the band over the card.
        :param caption: What the card has done so far, if anything yet.
        """
        self.card = card
        self._who = who
        self._color = color
        self._caption = caption
        self.redraw()

    def set_caption(self, caption: str) -> None:
        """Say what the card has just done, under the face."""
        if not self.is_open or caption == self._caption:
            return

        self._caption = caption
        self.redraw()

    def hide(self) -> None:
        """Take the card back off the board."""
        self.card = None
        self._who = ""
        self._color = ""
        self._caption = ""
        self.canvas.delete(TAG)

    def redraw(self) -> None:
        """Draw the placard where it stands, from nothing."""
        self.canvas.delete(TAG)

        if self.card is None:
            return

        scale = PLACARD_SCALE * self.layout.card_scale
        inset = INSET * self.layout.card_scale
        width = CARD_WIDTH * scale
        height = CARD_HEIGHT * scale
        band = SIZE_SMALL + SPACE_3

        left = inset
        top = self.layout.map_top + inset
        right = left + width
        bottom = top + band + height + (SPACE_3 if self._caption else 0)

        if self._caption:
            bottom += self._caption_height()

        self._draw_ground(left - SPACE_2, top - SPACE_2,
                          right + SPACE_2, bottom + SPACE_2)
        self._draw_who(left, top, width)
        draw_card_face(
            self.canvas, self.card, left, top + band, scale=scale, tag=TAG,
        )

        if self._caption:
            self._draw_caption(left, top + band + height + SPACE_3, width)

        self.canvas.tag_raise(TAG)

    def _draw_ground(self, left: float, top: float, right: float,
                     bottom: float) -> None:
        """
        The panel the card rests on.

        :param left: Its left edge.
        :param top: Its top edge.
        :param right: Its right edge.
        :param bottom: Its bottom edge.
        """
        draw_rounded_rect(
            self.canvas, left + 3, top + 3, right + 3, bottom + 3, 10, TAG,
            fill=CARD_SHADOW, outline="",
        )
        draw_rounded_rect(
            self.canvas, left, top, right, bottom, 10, TAG,
            fill=PANEL_BACKGROUND, outline=PANEL_EDGE,
        )

    def _draw_who(self, left: float, top: float, width: float) -> None:
        """
        The seat's name over the card, with their colour beside it.

        :param left: The left edge of the card.
        :param top: The top edge of the name band.
        :param width: How wide the card is.
        """
        middle = top + SIZE_SMALL / 2 + 1
        radius = SIZE_MICRO / 2

        self.canvas.create_oval(
            left, middle - radius, left + radius * 2, middle + radius,
            fill=self._color or MAP_INK, outline=TEXT_COLOR, tags=TAG,
        )
        self.canvas.create_text(
            left + radius * 2 + SPACE_2, middle, anchor="w",
            text=self._who, font=sans(SIZE_SMALL, "bold"), fill=TEXT_COLOR,
            width=width, tags=TAG,
        )

    def _draw_caption(self, left: float, top: float, width: float) -> None:
        """
        What the card has done, under the face.

        :param left: The left edge of the card.
        :param top: Where the caption starts.
        :param width: How wide the card is, which the caption may exceed.
        """
        self.canvas.create_text(
            left, top, anchor="nw", text=self._caption,
            font=serif(SIZE_MICRO), fill=MUTED_COLOR,
            width=max(width, CAPTION_WIDTH * self.layout.card_scale),
            tags=TAG,
        )

    def _caption_height(self) -> float:
        """How tall the caption runs, near enough to lay a panel under it."""
        per_line = max(
            1, int(CAPTION_WIDTH * self.layout.card_scale / (SIZE_MICRO * 0.6))
        )
        lines = max(1, -(-len(self._caption) // per_line))

        return lines * (SIZE_MICRO + 4)
