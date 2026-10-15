"""
File: seat_rail.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 11-09-2026
Description: The supply of every player, drawn down the side of the window.
"""
from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Callable, Iterable

from concordia.views.card_render import draw_rounded_rect
from concordia.views.good_art import good_photo
from concordia.views.palette import (
    ACCENT, ACCENT_INK, CARD_SHADOW, HIGHLIGHT, MUTED_COLOR, PANEL_EDGE,
    PANEL_RAISED, SIZE_MICRO, SIZE_SMALL, TEXT_COLOR, ink_on, sans, serif,
)

if TYPE_CHECKING:
    from concordia.models.player import Player

TAG = "seats"

# How far the rail keeps off the parchment and off the edge of the table.
BOARD_GAP = 12
EDGE_INSET = 10

# The narrowest rail worth drawing.
MIN_WIDTH = 132

SEAT_GAP = 8
SEAT_PADDING = 9
SEAT_RADIUS = 8

# The rows of one card, deepest first in the order they are drawn.
TITLE_HEIGHT = 19
LINE_HEIGHT = 15
CHIPS_HEIGHT = 23

# One good of the rail, smaller than in the band because it is not clickable.
CHIP = 16
CHIP_GAP = 2
DOT = 10

# The flag on the player holding the PRÆFECTVS MAGNVS.
PIP = 11


class SeatRail:
    """One card per player, down the margin beside the board."""

    def __init__(self, canvas: tk.Canvas, table_width: float,
                 good_color: Callable[[str], str | None]):
        """


        :param canvas: The table canvas the rail is drawn onto.
        :param table_width: The width of the whole table, the rail is measured
            back from its edge.
        :param good_color: Gives the colour of a good by name, for the rim of
            its chip.
        """
        self.canvas = canvas
        self._table_width = table_width
        self._good_color = good_color

        self._box = (0.0, 0.0, 0.0, 0.0)
        self._seats: list[Player] = []
        self._current: Player | None = None
        self._person: Player | None = None
        self._wanted: frozenset[str] = frozenset()

    # --- Where it stands ---

    def set_board(self, left: float, top: float, right: float,
                  bottom: float) -> None:
        """
        Say where the parchment is, the rail is drawn beside it.

        :param left: The left edge of the parchment, unused but taken so the
            caller can pass the whole rectangle.
        :param top: The top edge of the parchment, where the rail starts.
        :param right: Its right edge, which the rail keeps clear of.
        :param bottom: Its bottom edge, the rail may run to it.
        """
        del left
        rail_left = min(
            right + BOARD_GAP,
            self._table_width - EDGE_INSET - MIN_WIDTH,
        )
        self._box = (
            rail_left, top, self._table_width - EDGE_INSET, bottom
        )
        self.redraw()

    # --- Contents ---

    def set_seats(self, seats: Iterable[Player], current: Player | None,
                  person: Player | None,
                  wanted: Iterable[str] = ()) -> None:
        """
        Say who is at the table and what is being asked of them.

        :param seats: Every player, in turn order.
        :param current: The seat whose turn it is, whose card is ringed.
        :param person: The player the human is playing, named "You".
        :param wanted: The goods the running action is asking the current seat
            for, which are rimmed in gold on their card.
        """
        self._seats = list(seats)
        self._current = current
        self._person = person
        self._wanted = frozenset(wanted)
        self.redraw()

    # --- Drawing ---

    def redraw(self) -> None:
        """Draw the whole rail, replacing whatever was there."""
        self.canvas.delete(TAG)

        if not self._seats:
            return

        left, top, right, bottom = self._box
        width = right - left
        tall = self._seat_height(bottom - top)

        for index, seat in enumerate(self._seats):
            seat_top = top + index * (tall + SEAT_GAP)
            self._draw_seat(seat, left, seat_top, width, tall)

    def _seat_height(self, room: float) -> float:
        """The height of the card of one player."""
        seats = len(self._seats)
        share = (room - SEAT_GAP * (seats - 1)) / seats
        full = (
            SEAT_PADDING * 2 + TITLE_HEIGHT + LINE_HEIGHT * 3
            + CHIPS_HEIGHT
        )

        return min(full, share)

    def _draw_seat(self, seat: Player, left: float, top: float,
                   width: float, height: float) -> None:
        """
        Draw one seat's card: who they are, then as much of what they hold as
        the card is deep enough for.

        :param seat: The player the card belongs to.
        :param left: The card's left edge.
        :param top: The card's top edge.
        :param width: The card's width.
        :param height: The card's depth.
        """
        playing = seat is self._current
        draw_rounded_rect(
            self.canvas, left + 2, top + 2, left + width + 2,
            top + height + 2, SEAT_RADIUS, TAG, fill=CARD_SHADOW,
            outline="",
        )
        draw_rounded_rect(
            self.canvas, left, top, left + width, top + height,
            SEAT_RADIUS, TAG, fill=PANEL_RAISED,
            outline=ACCENT if playing else PANEL_EDGE,
            width=2 if playing else 1,
        )

        floor = top + height - SEAT_PADDING
        x = left + SEAT_PADDING
        y = top + SEAT_PADDING
        self._draw_name(seat, x, y, width - SEAT_PADDING * 2)
        y += TITLE_HEIGHT

        for line in self._lines(seat):
            if y + LINE_HEIGHT > floor:
                return

            self.canvas.create_text(
                x, y, text=line, anchor="nw", fill=MUTED_COLOR,
                font=sans(SIZE_MICRO), tags=TAG,
            )
            y += LINE_HEIGHT

        if y + CHIPS_HEIGHT <= floor:
            self._draw_goods(seat, x, y)

    def _draw_name(self, seat: Player, x: float, y: float,
                   width: float) -> None:
        """
        Draw the seat's colour, its name and the award tile it holds.

        :param seat: The player the card belongs to.
        :param x: The left edge of the card's contents.
        :param y: The top of the name row.
        :param width: How wide the contents may run.
        """
        middle = y + DOT / 2 + 1
        self.canvas.create_oval(
            x, middle - DOT / 2, x + DOT, middle + DOT / 2,
            fill=seat.color, outline=TEXT_COLOR, tags=TAG,
        )
        self.canvas.create_text(
            x + DOT + 6, middle, text=self._name_of(seat), anchor="w",
            fill=ACCENT if seat is self._current else TEXT_COLOR,
            font=serif(SIZE_SMALL, "bold"), tags=TAG,
        )

        if not seat.has_praefectus_magnus:
            return

        # The rail has no room for the tile itself, so the player is flagged
        # instead.
        right = x + width
        self.canvas.create_rectangle(
            right - PIP, middle - PIP / 2, right, middle + PIP / 2,
            fill=ACCENT, outline=ACCENT, tags=TAG,
        )
        self.canvas.create_text(
            right - PIP / 2, middle, text="P", fill=ACCENT_INK,
            font=sans(SIZE_MICRO - 1, "bold"), tags=TAG,
        )

    def _name_of(self, seat: Player) -> str:
        """The name shown on the card of a player."""
        if seat is self._person:
            return "You"

        return seat.color.capitalize()

    @staticmethod
    def _lines(seat: Player) -> list[str]:
        """What the player holds, as text, tallest row first."""
        return [
            f"{seat.sestertii} sestertii · {seat.houses} houses",
            f"{len(seat.hand)} in hand · "
            f"{len(seat.discarded_cards)} on the pile",
            f"{len(seat.storehouse_colonists)} colonists in reserve",
        ]

    def _draw_goods(self, seat: Player, x: float, y: float) -> None:
        """
        Draw the storehouse as one chip a good, or say it is empty.

        :param seat: The player the card belongs to.
        :param x: The left edge of the card's contents.
        :param y: The top of the chip row.
        """
        held = [
            (name, count)
            for name, count in sorted(seat.storehouse.items())
            if count > 0
        ]

        if not held:
            self.canvas.create_text(
                x, y + CHIP / 2, text="storehouse empty", anchor="w",
                fill=MUTED_COLOR, font=sans(SIZE_MICRO, "italic"),
                tags=TAG,
            )
            return

        right = self._box[2] - SEAT_PADDING

        for name, count in held:
            # The count is part of the chip: a chip that does not fit with its
            # "×2" does not fit.
            if x + CHIP + self._count_width(count) > right:
                return

            self._draw_chip(seat, name, count, x, y)
            x += CHIP + CHIP_GAP + self._count_width(count)

    def _draw_chip(self, seat: Player, name: str, count: int,
                   x: float, y: float) -> None:
        """
        One good of a storehouse: its token, its colour and how many.

        :param seat: The player the card belongs to.
        :param name: The good's name, as the ORDB spells it.
        :param count: How many units are held.
        :param x: The chip's left edge.
        :param y: The chip's top edge.
        """
        wanted = seat is self._current and name in self._wanted
        color = self._good_color(name) or MUTED_COLOR
        token = good_photo(name, CHIP - 4, CHIP - 4)

        draw_rounded_rect(
            self.canvas, x, y, x + CHIP, y + CHIP, 3, TAG,
            fill=PANEL_RAISED if token is not None else color,
            outline=HIGHLIGHT if wanted else color,
            width=2 if wanted else 1,
        )

        if token is not None:
            self.canvas.create_image(
                x + CHIP / 2, y + CHIP / 2, image=token, tags=TAG,
            )
        else:
            self.canvas.create_text(
                x + CHIP / 2, y + CHIP / 2, text=name[0].upper(),
                font=sans(SIZE_MICRO, "bold"), fill=ink_on(color), tags=TAG,
            )

        self.canvas.create_text(
            x + CHIP + 2, y + CHIP / 2, text=f"×{count}", anchor="w",
            fill=HIGHLIGHT if wanted else TEXT_COLOR,
            font=sans(SIZE_MICRO, "bold"), tags=TAG,
        )

    @staticmethod
    def _count_width(count: int) -> float:
        """How much room the "×2" beside a chip takes."""
        return 11 + 4.5 * len(str(count))
