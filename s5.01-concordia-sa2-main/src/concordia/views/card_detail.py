"""
File: card_detail.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The panel opened when a card is clicked: its face, its text and
             the play button.
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from concordia.models.card import Card, CardOrigin
from concordia.views.card_render import (
    cost_colors, draw_card_face, draw_rounded_rect, subtitle,
)
from concordia.views.good_art import good_photo
from concordia.views.palette import (
    ACCENT, ACCENT_INK, CARD_BORDER, CARD_FACE, CARD_HEIGHT, CARD_WIDTH,
    HIGHLIGHT, MUTED_COLOR, PANEL_BACKGROUND, PANEL_EDGE, PANEL_RAISED,
    SIZE_BODY, SIZE_MICRO, SIZE_SMALL, SIZE_TITLE, SPACE_1, SPACE_2,
    SPACE_3, SPACE_4, SPACE_5, TEXT_COLOR, ink_on, sans, serif,
)

DETAIL_SCALE = 1.9
TEXT_WIDTH = 420
SWATCH = 24
# What a token keeps clear of the rim of the swatch it is printed on.
TOKEN_MARGIN = 5


class CardDetail:
    """The detail panel of one card, drawn over the board."""

    def __init__(self, canvas: tk.Canvas, on_play: Callable[[Card], None],
                 on_close: Callable[[], None]):
        """
        :param canvas: The table canvas the panel is placed over.
        :param on_play: Called with the card the Play button was hit for.
        :param on_close: Called whenever the panel closes.
        """
        self._canvas = canvas
        self._on_play = on_play
        self._on_close = on_close
        self._frame: tk.Frame | None = None
        self.card: Card | None = None

    # --- Visibility ---

    def show(self, card: Card, playable: bool,
             enabled: bool = True) -> None:
        """
        Open the panel on a card, replacing whatever it was showing.

        :param card: The card to detail.
        :param playable: Whether the card is in the current hand, which gives
            it a Play button.
        :param enabled: Whether that button does anything: a card with nothing
            to act on says so instead.
        """
        self.hide(notify=False)
        self.card = card

        self._frame = tk.Frame(
            self._canvas, bg=PANEL_BACKGROUND, highlightthickness=2,
            highlightbackground=ACCENT,
        )
        self._frame.place(relx=0.5, rely=0.5, anchor="center")
        self._build_face(card)
        self._build_text(card, playable, enabled)

    def hide(self, notify: bool = True) -> None:
        """Close the panel."""
        if self._frame is not None:
            self._frame.destroy()
            self._frame = None
        self.card = None
        if notify:
            self._on_close()

    @property
    def is_open(self) -> bool:
        """Whether the panel is currently showing a card."""
        return self._frame is not None

    # --- Contents ---

    def _build_face(self, card: Card) -> None:
        """Draw the enlarged card face down the left of the panel."""
        width = CARD_WIDTH * DETAIL_SCALE
        height = CARD_HEIGHT * DETAIL_SCALE
        face = tk.Canvas(
            self._frame, width=width + SPACE_2, height=height + SPACE_2,
            bg=PANEL_BACKGROUND, highlightthickness=0,
        )
        face.grid(
            row=0, column=0, padx=SPACE_5, pady=SPACE_5, sticky="n",
        )
        draw_card_face(face, card, 0, 0, scale=DETAIL_SCALE, tag="detail")

    def _build_text(self, card: Card, playable: bool,
                    enabled: bool) -> None:
        """Fill the right of the panel: name, god, cost, rules and button."""
        right = tk.Frame(self._frame, bg=PANEL_BACKGROUND)
        right.grid(
            row=0, column=1, padx=(0, SPACE_5), pady=SPACE_5, sticky="nsew",
        )

        self._build_heading(right, card)
        self._rule(right, pady=(SPACE_3, SPACE_3))
        self._build_cost(right, card)

        tk.Label(
            right, text=card.text or "No rules text.", fg=TEXT_COLOR,
            bg=PANEL_BACKGROUND, font=sans(SIZE_BODY), anchor="w",
            wraplength=TEXT_WIDTH, justify="left",
        ).pack(fill="x", pady=(SPACE_3, 0))

        if card.god is not None:
            self._build_god(right, card)

        self._build_button(right, card, playable, enabled)

    def _build_heading(self, parent: tk.Widget, card: Card) -> None:
        """The name of the card, what it is, and the close button."""
        head = tk.Frame(parent, bg=PANEL_BACKGROUND)
        head.pack(fill="x")

        tk.Label(
            head, text=card.name, fg=ACCENT, bg=PANEL_BACKGROUND,
            font=serif(SIZE_TITLE, "bold"), anchor="w",
            wraplength=TEXT_WIDTH, justify="left",
        ).pack(side="left")

        # The panel closes on Escape and on a click outside it, so it says so.
        close = tk.Label(
            head, text="Esc  ✕", fg=MUTED_COLOR, bg=PANEL_RAISED,
            font=sans(SIZE_MICRO, "bold"), padx=SPACE_2, pady=SPACE_1,
            cursor="hand2",
        )
        close.pack(side="right", padx=(SPACE_3, 0))
        close.bind("<Button-1>", lambda _e: self.hide())

        tk.Label(
            parent, text=subtitle(card) or card.origin.value,
            fg=MUTED_COLOR, bg=PANEL_BACKGROUND,
            font=sans(SIZE_SMALL, "italic"), anchor="w",
        ).pack(fill="x", pady=(SPACE_1, 0))

    def _build_god(self, parent: tk.Widget, card: Card) -> None:
        """The god the card scores with, set apart from its rules text."""
        box = tk.Frame(parent, bg=PANEL_RAISED)
        box.pack(fill="x", pady=(SPACE_3, 0))

        tk.Label(
            box, text=card.god.name.upper(), fg=ACCENT, bg=PANEL_RAISED,
            font=sans(SIZE_MICRO, "bold"), anchor="w",
        ).pack(fill="x", padx=SPACE_3, pady=(SPACE_2, 0))
        tk.Label(
            box, text=self._reward(card), fg=TEXT_COLOR, bg=PANEL_RAISED,
            font=sans(SIZE_SMALL),
            anchor="w", wraplength=TEXT_WIDTH - SPACE_5, justify="left",
        ).pack(fill="x", padx=SPACE_3, pady=(0, SPACE_2))

    @staticmethod
    def _reward(card: Card) -> str:
        """What scoring with a card's god is worth."""
        reward = card.god.reward

        if "VP" in reward:
            return reward
        return f"{reward}, {card.god.victory_points} VP"

    def _build_cost(self, parent: tk.Widget, card: Card) -> None:
        """Show the goods the card is bought with, as a row of swatches."""
        if card.origin is CardOrigin.AWARD and not card.cost:
            # An award card is won and not bought, so no cost is printed.
            return

        colors = cost_colors(card)
        row = tk.Frame(parent, bg=PANEL_BACKGROUND)
        row.pack(fill="x")

        tk.Label(
            row, text="COST", fg=MUTED_COLOR, bg=PANEL_BACKGROUND,
            font=sans(SIZE_MICRO, "bold"),
        ).pack(side="left", padx=(0, SPACE_2))

        if not colors:
            tk.Label(
                row, text="free", fg=ACCENT, bg=PANEL_BACKGROUND,
                font=sans(SIZE_SMALL, "bold"),
            ).pack(side="left")
            return

        for good, color in zip(card.cost, colors):
            self._draw_swatch(row, good.name, color)

    @staticmethod
    def _draw_swatch(row: tk.Widget, name: str, color: str) -> None:
        """
        One unit of a card's price: the good's token, rimmed in its colour.

        :param row: The row the swatch is packed into.
        :param name: The good's name, as the ORDB spells it.
        :param color: The good's own colour.
        """
        token = good_photo(name, SWATCH - TOKEN_MARGIN, SWATCH - TOKEN_MARGIN)
        swatch = tk.Canvas(
            row, width=SWATCH, height=SWATCH, bg=PANEL_BACKGROUND,
            highlightthickness=0,
        )
        swatch.pack(side="left", padx=(0, SPACE_1))
        draw_rounded_rect(
            swatch, 1, 1, SWATCH - 1, SWATCH - 1, 4, "swatch",
            fill=CARD_FACE if token is not None else color,
            outline=color if token is not None else CARD_BORDER, width=2,
        )

        if token is not None:
            swatch.create_image(SWATCH / 2, SWATCH / 2, image=token)
            return

        swatch.create_text(
            SWATCH / 2, SWATCH / 2, text=name[0].upper(),
            font=sans(SIZE_MICRO, "bold"), fill=ink_on(color),
        )

    @staticmethod
    def _rule(parent: tk.Widget, pady: tuple[int, int]) -> None:
        """A hairline parting one part of the panel from the next."""
        tk.Frame(parent, bg=PANEL_EDGE, height=1).pack(fill="x", pady=pady)

    def _build_button(self, parent: tk.Widget, card: Card, playable: bool,
                      enabled: bool) -> None:
        """Add the Play button, or say why the card cannot be played."""
        if card.origin is CardOrigin.AWARD:
            # The award cards are never played, they are only held.
            self._say(parent, "Held, not played, it works on its own.")
            return

        if not playable:
            self._say(parent, "On sale in the market, not in your hand.")
            return

        if not enabled:
            self._say(
                parent,
                "Nothing on the table for this card to act on right now.",
            )
            return

        # Drawn as a label and not a tk.Button: macOS repaints a button its own
        # colour.
        play = tk.Label(
            parent, text="▶  PLAY", bg=ACCENT, fg=ACCENT_INK,
            font=sans(SIZE_BODY, "bold"), padx=SPACE_5, pady=SPACE_2,
            cursor="hand2",
        )
        play.pack(anchor="e", pady=(SPACE_4, 0))
        play.bind("<Button-1>", lambda _e: self._on_play(card))
        play.bind("<Enter>", lambda _e: play.configure(bg=HIGHLIGHT))
        play.bind("<Leave>", lambda _e: play.configure(bg=ACCENT))

    @staticmethod
    def _say(parent: tk.Widget, text: str) -> None:
        """Put a line where the Play button would have gone."""
        tk.Label(
            parent, text=text, fg=MUTED_COLOR, bg=PANEL_BACKGROUND,
            font=sans(SIZE_SMALL, "italic"), anchor="w",
            wraplength=TEXT_WIDTH, justify="left",
        ).pack(fill="x", pady=(SPACE_4, 0))
