"""
File: hand_bar.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The hand of the current player, below the window and rising when
             hovered.
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from concordia.models.card import Card
from concordia.views.animation import (
    FRAME_MS, LIFT_STEP, ease_out_cubic, step_toward,
)
from concordia.views.card_render import draw_card_face
from concordia.views.layout import Layout
from concordia.views.palette import (
    CARD_HEIGHT, CARD_WIDTH, HOVER_SCALE, MUTED_COLOR, SIZE_BODY, sans,
)

TAG = "hand"

# The base gaps, scaled with the cards themselves.
CARD_GAP = 12
NUDGE = 26
RAISE_MARGIN = 10

# How much lower than the rest a card that cannot be played sits.
REST_DROP = 10


class HandBar:
    """The hand of the player, drawn at the bottom of the canvas."""

    def __init__(self, canvas: tk.Canvas, layout: Layout,
                 on_select: Callable[[Card], None]):
        """
        :param canvas: The table canvas the hand is drawn onto.
        :param layout: Where the bands of the table fall, and how big a
            card is drawn on it.
        :param on_select: Called with the card a click landed on.
        """
        self.canvas = canvas
        self.layout = layout
        self._on_select = on_select

        self._left = 0.0
        self._width = layout.table_width
        self._floor = layout.table_height
        self._gap = CARD_GAP * layout.card_scale

        self._cards: list[Card] = []
        self._lifts: list[float] = []
        self._placed: list[
            tuple[float, float, float, float, Card, float]
        ] = []
        self._hovered: int | None = None
        self._selected: Card | None = None
        self._playable: set[int] = set()
        self._highlighted: set[int] = set()
        self._job: str | None = None

    def set_cards(self, cards: list[Card]) -> None:
        """Show a hand, every card back down in the row."""
        self._cards = list(cards)
        self._lifts = [0.0] * len(self._cards)
        self._hovered = None
        self._playable = {id(card) for card in cards}
        self._highlighted = set()
        self.redraw()

    def set_selected(self, card: Card | None) -> None:
        """Mark which card the detail overlay is showing."""
        self._selected = card
        self.redraw()

    def set_playable(self, cards) -> None:
        """Mark which cards of the hand are worth playing."""
        self._playable = {id(card) for card in cards}
        self.redraw()

    def set_highlighted(self, cards) -> None:
        """Mark which cards the running action is offering."""
        self._highlighted = {id(card) for card in cards}
        self.redraw()

    def _scale_of(self, index: int) -> float:
        """The scale the card at that index is currently drawn at."""
        eased = ease_out_cubic(self._lifts[index])
        return self.layout.card_scale * (1 + (HOVER_SCALE - 1) * eased)

    def _place(self) -> list[tuple[float, float, float, float, Card, float]]:
        """
        Place every card for the lift it currently stands at.

        :return: One (x, y, width, height, card, lift) per card, in hand
            order.
        """
        card_width = self.layout.card_width
        count = len(self._cards)
        row_width = count * card_width + (count - 1) * self._gap
        row_left = self._left + (self._width - row_width) / 2
        rest_top = self._floor - self.layout.hand_peek
        raised_top = (
            self._floor - self.layout.card_height * HOVER_SCALE - RAISE_MARGIN
        )

        placed = []
        for index, card in enumerate(self._cards):
            eased = ease_out_cubic(self._lifts[index])
            scale = self._scale_of(index)
            width = CARD_WIDTH * scale
            height = CARD_HEIGHT * scale

            centre = (
                row_left + index * (card_width + self._gap) + card_width / 2
            )
            for other, lift in enumerate(self._lifts):
                if other != index:
                    away = 1 if index > other else -1
                    centre += NUDGE * ease_out_cubic(lift) * away

            # An unplayable card sits lower and rises from there.
            seated = rest_top + (
                0 if id(card) in self._playable else REST_DROP
            )
            top = seated + (raised_top - seated) * eased
            placed.append(
                (centre - width / 2, top, width, height, card,
                 self._lifts[index])
            )
        return placed

    def redraw(self) -> None:
        """Draw the row, the most-raised card last so it sits on top."""
        self.canvas.delete(TAG)
        self._placed = []

        if not self._cards:
            self.canvas.create_text(
                self._left + self._width / 2,
                self._floor - self.layout.hand_peek / 2,
                text="No card left in hand.", fill=MUTED_COLOR,
                font=sans(SIZE_BODY, "italic"), tags=TAG,
            )
            return

        self._placed = sorted(self._place(), key=lambda placed: placed[5])
        for x, y, _w, _h, card, _lift in self._placed:
            index = self._cards.index(card)
            draw_card_face(
                self.canvas, card, x, y, scale=self._scale_of(index),
                tag=TAG, selected=card is self._selected,
                highlighted=id(card) in self._highlighted,
                dimmed=id(card) not in self._playable,
            )

    def _tick(self) -> None:
        """Walk every card one frame towards the lift it is heading for."""
        self._job = None
        moved = False

        for index in range(len(self._cards)):
            target = 1.0 if index == self._hovered else 0.0
            stepped = step_toward(self._lifts[index], target, LIFT_STEP)
            if stepped != self._lifts[index]:
                self._lifts[index] = stepped
                moved = True

        if moved:
            self.redraw()
            self._schedule()

    def _schedule(self) -> None:
        """Ask for another frame, unless one is already on its way."""
        if self._job is None:
            self._job = self.canvas.after(FRAME_MS, self._tick)

    def _index_at(self, x: float, y: float) -> int | None:
        """
        The card under the pointer, the most-raised one winning.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: The card's index in the hand, None when over no card.
        """
        for px, py, width, height, card, _lift in reversed(self._placed):
            if px <= x <= px + width and py <= y <= py + height:
                return self._cards.index(card)
        return None

    def card_at(self, x: float, y: float) -> Card | None:
        """
        The card under the pointer, for the view to route a click to.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: The card, None when the pointer is over no card.
        """
        index = self._index_at(x, y)
        return None if index is None else self._cards[index]

    def hover_at(self, x: float, y: float) -> None:
        """
        Point the hover at whatever card sits under the pointer.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        """
        index = self._index_at(x, y)
        if index != self._hovered:
            self._hovered = index
            self._schedule()

    def clear_hover(self) -> None:
        """Send every card back down, as when the pointer leaves."""
        if self._hovered is not None:
            self._hovered = None
            self._schedule()
