"""
File: layout.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Computes where the bands of the window fall, from the size of the
             screen.
"""
from __future__ import annotations

from dataclasses import dataclass

from concordia.views.palette import (
    CARD_HEIGHT, CARD_WIDTH, HAND_GUTTER, HAND_PEEK, MAP_BAND, MARKET_BAND,
    TABLE_WIDTH,
)

# How much of the screen the window may take.
WIDTH_SHARE = 0.92
HEIGHT_SHARE = 0.93

# What the window spends outside the table: title bar, HUD, status line,
# padding.
CHROME_HEIGHT = 122

# A wider table gains nothing: the map only holds a dozen cities.
MAX_TABLE_WIDTH = 1800

# The cards grow more slowly than the table.
MAX_CARD_SCALE = 1.2
MAX_GUTTER_SCALE = 1.15

# The deepest the map may be for its width.
MAP_ASPECT_CAP = 0.66


@dataclass(frozen=True)
class Layout:
    """The height of every band of the window, and the size of a card."""

    table_width: int
    market_band: int
    map_band: int
    hand_gutter: int
    hand_peek: int
    card_scale: float

    @classmethod
    def base(cls) -> "Layout":
        """
        The table at the size it was hard-coded to before it was measured.
        """
        return cls(
            table_width=TABLE_WIDTH,
            market_band=MARKET_BAND,
            map_band=MAP_BAND,
            hand_gutter=HAND_GUTTER,
            hand_peek=HAND_PEEK,
            card_scale=1.0,
        )

    @classmethod
    def for_screen(cls, screen_width: int, screen_height: int) -> "Layout":
        """
        The table sized to the screen it is about to be opened on.

        :param screen_width: The display's width in pixels.
        :param screen_height: The display's height in pixels.
        :return: The layout to build the window with.
        """
        width = max(
            TABLE_WIDTH,
            min(int(screen_width * WIDTH_SHARE), MAX_TABLE_WIDTH),
        )
        card_scale = max(1.0, min(width / TABLE_WIDTH, MAX_CARD_SCALE))

        market = round(MARKET_BAND * card_scale)
        peek = round(HAND_PEEK * card_scale)
        gutter = round(HAND_GUTTER * min(card_scale, MAX_GUTTER_SCALE))

        # What is left of the screen goes to the map.
        spare = int(screen_height * HEIGHT_SHARE) - CHROME_HEIGHT
        map_band = max(MAP_BAND, spare - market - gutter - peek)
        map_band = min(map_band, round(width * MAP_ASPECT_CAP))

        return cls(
            table_width=width,
            market_band=market,
            map_band=map_band,
            hand_gutter=gutter,
            hand_peek=peek,
            card_scale=card_scale,
        )

    @property
    def map_top(self) -> int:
        """The y the map band starts at, the market being above it."""
        return self.market_band

    @property
    def map_bottom(self) -> int:
        """The y the map band ends at."""
        return self.market_band + self.map_band

    @property
    def gutter_bottom(self) -> int:
        """The y the gap under the board ends at, the hand being below."""
        return self.map_bottom + self.hand_gutter

    @property
    def table_height(self) -> int:
        """The height of the whole canvas."""
        return self.gutter_bottom + self.hand_peek

    @property
    def card_width(self) -> float:
        """The width of a card of the hand, at rest."""
        return CARD_WIDTH * self.card_scale

    @property
    def card_height(self) -> float:
        """The height of a card of the hand, at rest."""
        return CARD_HEIGHT * self.card_scale
