"""
File: market_panel.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Draws the card market in a row at the top of the window.
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from concordia.models.card import Card
from concordia.models.market import CardMarket
from concordia.views.card_render import (
    ANY_GOOD, draw_card_face, draw_rounded_rect, slot_cost,
)
from concordia.views.good_art import good_photo
from concordia.views.layout import Layout
from concordia.views.palette import (
    ACCENT, ANY_GOOD_FILL, CARD_BORDER, CARD_FACE, CARD_HEIGHT, CARD_INK,
    CARD_WIDTH, MUTED_COLOR, PANEL_BACKGROUND, PANEL_EDGE, SIZE_MICRO,
    SIZE_SMALL, SPACE_1, SPACE_2, SPACE_3, TEXT_COLOR, ink_on, sans, serif,
)

TAG = "market"
MARKET_SCALE = 0.78
# The set-aside card is not for sale, so it is drawn smaller.
ASIDE_SCALE = 0.55
ASIDE_MARGIN = 10
CARD_GAP = 12
SIDE_PADDING = 18
COST_SWATCH = 17
COST_GAP = 4
COST_MARGIN = 7
# The margin a token keeps inside its swatch.
TOKEN_MARGIN = 4


class MarketPanel:
    """The cards for sale, in one row at the top of the window."""

    def __init__(self, canvas: tk.Canvas, layout: Layout,
                 on_select: Callable[[Card], None],
                 good_color: Callable[[str], str | None]):
        """
        :param canvas: The table canvas the row is drawn onto.
        :param layout: Where the bands of the table fall, and how big a
            card is drawn on it.
        :param on_select: Called with the card a click landed on.
        :param good_color: Looks a good's colour up by name, for the
            goods a display position is bought with.
        """
        self.canvas = canvas
        self.layout = layout
        self._on_select = on_select
        self._good_color = good_color

        self._left = 0.0
        self._top = 0.0
        self._width = layout.table_width
        self._height = layout.market_band
        self._scale = layout.card_scale

        self._boxes: list[tuple[float, float, float, float, Card]] = []
        self._selected: Card | None = None
        self._highlighted: set[int] = set()
        self._market: CardMarket | None = None

    # --- Contents ---

    def set_market(self, market: CardMarket) -> None:
        """Show a market's display, its stack count and its set-aside card."""
        self._market = market
        self.redraw()

    def set_selected(self, card: Card | None) -> None:
        """Mark which card the detail overlay is showing."""
        self._selected = card
        self.redraw()

    def set_highlighted(self, cards) -> None:
        """Mark which cards of the display the running action is offering."""
        self._highlighted = {id(card) for card in cards}
        self.redraw()

    def highlighted_card_at(self, x: float, y: float) -> Card | None:
        """
        The offered card under the pointer, for answering a request with.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: The card, None when the pointer is over none it offers.
        """
        card = self.card_at(x, y)

        return card if card is not None and id(card) in self._highlighted \
            else None

    # --- Drawing ---

    def redraw(self) -> None:
        """Draw the band: the stack count, the row and the set-aside note."""
        self.canvas.delete(TAG)
        self._boxes = []

        if self._market is None:
            return

        self.canvas.create_rectangle(
            self._left, self._top, self._left + self._width,
            self._top + self._height,
            fill=PANEL_BACKGROUND, outline="", tags=TAG,
        )
        # The hairline separates the band from the map below it.
        self.canvas.create_line(
            self._left, self._top + self._height,
            self._left + self._width, self._top + self._height,
            fill=PANEL_EDGE, width=1, tags=TAG,
        )

        self._draw_heading()
        self._draw_row(self._market.display)

        if self._market.aside is not None:
            self._draw_aside(
                self._market.aside, self._top + self._height / 2
            )

    def _draw_heading(self) -> None:
        """Name the band, and say how deep the stack still is."""
        middle = self._top + self._height / 2
        left = self._left + SIDE_PADDING

        self.canvas.create_text(
            left, middle - SPACE_2, text="MARKET", anchor="w",
            fill=TEXT_COLOR, font=serif(SIZE_SMALL, "bold"), tags=TAG,
        )
        self.canvas.create_text(
            left, middle + SPACE_2,
            text=f"{len(self._market.stack)} cards left", anchor="w",
            fill=MUTED_COLOR, font=sans(SIZE_MICRO), tags=TAG,
        )

    def _draw_aside(self, card: Card, middle: float) -> None:
        """
        Show the set-aside card at the right end of the band.

        :param card: The set-aside card.
        :param middle: The y the band is centred on.
        """
        scale = ASIDE_SCALE * self._scale
        width = CARD_WIDTH * scale
        height = CARD_HEIGHT * scale
        left = self._left + self._width - SIDE_PADDING - width

        draw_card_face(
            self.canvas, card, left, middle - height / 2,
            scale=scale, tag=TAG,
        )
        self.canvas.create_text(
            left - ASIDE_MARGIN, middle - SPACE_2, text="SET ASIDE",
            anchor="e", fill=MUTED_COLOR, font=sans(SIZE_MICRO, "bold"),
            tags=TAG,
        )
        self.canvas.create_text(
            left - ASIDE_MARGIN, middle + SPACE_1, text="ends the game",
            anchor="e", fill=MUTED_COLOR, font=sans(SIZE_MICRO), tags=TAG,
        )
        self.canvas.create_text(
            left - ASIDE_MARGIN, middle + SPACE_3 + SPACE_1, text="+7 VP",
            anchor="e", fill=ACCENT, font=serif(SIZE_SMALL, "bold"),
            tags=TAG,
        )

    def _draw_row(self, cards: list[Card]) -> None:
        """Deal the display across the middle of the band."""
        if not cards:
            self.canvas.create_text(
                self._left + self._width / 2, self._top + self._height / 2,
                text="The display is empty.", fill=MUTED_COLOR,
                font=sans(SIZE_SMALL, "italic"), tags=TAG,
            )
            return

        scale = MARKET_SCALE * self._scale
        width = CARD_WIDTH * scale
        height = CARD_HEIGHT * scale
        gap = CARD_GAP * self._scale
        swatch = COST_SWATCH * self._scale
        row_width = len(cards) * width + (len(cards) - 1) * gap
        row_left = self._left + (self._width - row_width) / 2

        # The card and its price are centred in the band as one block.
        block = height + COST_MARGIN + swatch
        top = self._top + (self._height - block) / 2

        for index, card in enumerate(cards):
            x = row_left + index * (width + gap)
            draw_card_face(
                self.canvas, card, x, top, scale=scale, tag=TAG,
                selected=card is self._selected,
                highlighted=id(card) in self._highlighted,
                dimmed=bool(self._highlighted)
                and id(card) not in self._highlighted,
            )
            self._boxes.append((x, top, x + width, top + height, card))
            self._draw_slot_cost(
                index + 1, x + width / 2, top + height + COST_MARGIN, swatch
            )

    def _draw_slot_cost(self, position: int, centre: float, top: float,
                        swatch: float) -> None:
        """
        Print the goods a display position is bought with, under its card.

        :param position: The 1-based position of the slot.
        :param centre: The x the row is centred on, the card's middle.
        :param top: The top edge of the row.
        :param swatch: The size of one swatch.
        """
        owed = slot_cost(self._market.slot_at(position))
        if not owed:
            self.canvas.create_text(
                centre, top + swatch / 2, text="free", fill=ACCENT,
                font=sans(SIZE_MICRO, "bold"), tags=TAG,
            )
            return

        gap = COST_GAP * self._scale
        row_width = len(owed) * swatch + (len(owed) - 1) * gap
        left = centre - row_width / 2

        for index, good in enumerate(owed):
            x = left + index * (swatch + gap)
            self._draw_swatch(good, x, top, swatch)

    def _draw_swatch(self, good: str, left: float, top: float,
                     swatch: float) -> None:
        """
        One unit of a price: a good's token, or the "?" standing for any.

        :param good: The good owed, `ANY_GOOD` for one of the buyer's choice.
        :param left: The left edge of the swatch.
        :param top: The top edge of the swatch.
        :param swatch: The size of the swatch.
        """
        wildcard = good == ANY_GOOD
        color = (
            ANY_GOOD_FILL if wildcard
            else self._good_color(good) or "#8a8a8a"
        )
        inner = swatch - TOKEN_MARGIN * self._scale
        token = None if wildcard else good_photo(good, inner, inner)

        draw_rounded_rect(
            self.canvas, left, top, left + swatch, top + swatch, 3, TAG,
            fill=CARD_FACE if token is not None else color,
            outline=color if token is not None else CARD_BORDER, width=1,
        )

        if token is not None:
            self.canvas.create_image(
                left + swatch / 2, top + swatch / 2, image=token, tags=TAG,
            )
            return

        self.canvas.create_text(
            left + swatch / 2, top + swatch / 2,
            text=ANY_GOOD if wildcard else good[0].upper(),
            font=sans(max(SIZE_MICRO - 1, 7), "bold"),
            fill=CARD_INK if wildcard else ink_on(color), tags=TAG,
        )

    # --- Pointer ---

    def card_at(self, x: float, y: float) -> Card | None:
        """
        The card under the pointer, for the view to route a click to.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: The card, None when the pointer is over no card.
        """
        for x0, y0, x1, y1, card in self._boxes:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return card
        return None
