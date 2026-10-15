"""
File: end_screen.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 11-09-2026
Description: The screen shown when the game is over: the winner, the
             standings and the credits of the box.
"""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Iterable

from concordia.models.description import GameDescription
from concordia.models.player import Player
from concordia.views.palette import (
    ACCENT, ACCENT_INK, MUTED_COLOR, PANEL_BACKGROUND, PANEL_EDGE,
    PANEL_RAISED, SIZE_BODY, SIZE_LEAD, SIZE_MICRO, SIZE_SMALL,
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6, TEXT_COLOR, sans,
    serif,
)

FALLBACK_TITLE = "Concordia"
SEPARATOR = " · "

# The winner is printed a size up from everyone else, their score two.
SIZE_HEADLINE = 30
SIZE_WINNER = 22
SIZE_WINNER_SCORE = 44
SIZE_SCORE = 18

# The colour disc beside a name, and the winner's larger one.
DOT = 12
WINNER_DOT = 18

# The CONCORDIA card, flagged beside whoever holds it.
CONCORDIA_PIP = "CONCORDIA"


@dataclass(frozen=True)
class Standing:
    """One row of the final standings."""

    rank: int
    color: str
    name: str
    victory_points: int
    has_concordia: bool


def screen_title(description: GameDescription | None) -> str:
    """The name of the game, in capitals, as the box spells it."""
    name = description.name if description is not None else FALLBACK_TITLE
    return name.upper()


def credits_lines(description: GameDescription | None) -> list[str]:
    """
    The credits of the box, as printed at the foot of the end screen.

    :param description: What the box says, None when it was not read.
    :return: Two lines at most: who made the game, then who sells it and for
        whom. A field the box does not give is left out, and a line with
        nothing left in it is dropped.
    """
    if description is None:
        return []

    title = description.name
    if description.edition_year is not None:
        title += f" ({description.edition_year})"

    made_by = [title]
    if description.designer:
        made_by.append(f"designed by {description.designer}")
    if description.artists:
        made_by.append(f"art by {', '.join(description.artists)}")

    sold_by = []
    if description.publisher:
        sold_by.append(description.publisher)
    if description.players:
        sold_by.append(f"{description.players} players")
    if description.age:
        # The ORDB may already spell the age "13+".
        age = str(description.age)
        sold_by.append(age if age.endswith("+") else f"{age}+")
    if description.playing_time is not None:
        sold_by.append(f"{description.playing_time} min")

    return [
        SEPARATOR.join(parts) for parts in (made_by, sold_by) if parts
    ]


def standings_rows(ranking: Iterable[tuple[Player, int]],
                   name_of: Callable[[Player], str]) -> list[Standing]:
    """
    The final standings, one row a player, first place first.

    :param ranking: The players with their victory points, best first, as
        the ScoreManager ranks them.
    :param name_of: What a player is called on screen.
    :return: The rows to print, numbered from 1.
    """
    return [
        Standing(
            rank=place, color=player.color, name=name_of(player),
            victory_points=victory_points,
            has_concordia=player.has_concordia,
        )
        for place, (player, victory_points) in enumerate(ranking, start=1)
    ]


class EndScreen:
    """The panel drawn over the board once the game is over."""

    def __init__(self, canvas: tk.Canvas):
        """
        :param canvas: The table canvas the panel is placed over.
        """
        self._canvas = canvas
        self._frame: tk.Frame | None = None

    # --- Visibility ---

    def show(self, title: str, standings: list[Standing],
             credits: list[str]) -> None:
        """
        Open the panel, replacing whatever it was showing.

        :param title: The name of the game, printed across the top.
        :param standings: The players in finishing order, first place first.
        :param credits: What the box says about the game, a line each.
        """
        self.hide()

        self._frame = tk.Frame(
            self._canvas, bg=PANEL_BACKGROUND, highlightthickness=2,
            highlightbackground=ACCENT,
        )
        self._frame.place(relx=0.5, rely=0.5, anchor="center")

        body = tk.Frame(self._frame, bg=PANEL_BACKGROUND)
        body.pack(padx=SPACE_6, pady=SPACE_5)

        self._build_heading(body, title)

        if standings:
            self._build_standings(body, standings)
        else:
            tk.Label(
                body, text="Nobody was at the table.", fg=MUTED_COLOR,
                bg=PANEL_BACKGROUND, font=sans(SIZE_SMALL, "italic"),
            ).pack(pady=(SPACE_4, 0))

        if credits:
            self._build_credits(body, credits)

    def hide(self) -> None:
        """Close the panel."""
        if self._frame is not None:
            self._frame.destroy()
            self._frame = None

    @property
    def is_open(self) -> bool:
        """Whether the panel is currently on the table."""
        return self._frame is not None

    # --- Contents ---

    def _build_heading(self, parent: tk.Widget, title: str) -> None:
        """"Game over", the name of the game, and the close button."""
        head = tk.Frame(parent, bg=PANEL_BACKGROUND)
        head.pack(fill="x")

        tk.Label(
            head, text="G A M E   O V E R", fg=MUTED_COLOR,
            bg=PANEL_BACKGROUND, font=sans(SIZE_MICRO, "bold"),
        ).pack(side="left", anchor="s")

        # The panel closes on Escape and on the cross, so it says so.
        close = tk.Label(
            head, text="Esc  ✕", fg=MUTED_COLOR, bg=PANEL_RAISED,
            font=sans(SIZE_MICRO, "bold"), padx=SPACE_2, pady=SPACE_1,
            cursor="hand2",
        )
        close.pack(side="right", padx=(SPACE_5, 0))
        close.bind("<Button-1>", lambda _e: self.hide())

        tk.Label(
            parent, text=title, fg=ACCENT, bg=PANEL_BACKGROUND,
            font=serif(SIZE_HEADLINE, "bold"),
        ).pack(pady=(0, SPACE_2))

    def _build_standings(self, parent: tk.Widget,
                         standings: list[Standing]) -> None:
        """Every player in finishing order, the winner a size up."""
        self._rule(parent, pady=(SPACE_2, SPACE_4))

        winner, *others = standings
        self._build_winner(parent, winner)

        if not others:
            return

        self._rule(parent, pady=(SPACE_4, SPACE_3))

        table = tk.Frame(parent, bg=PANEL_BACKGROUND)
        table.pack(fill="x")
        table.columnconfigure(2, weight=1)

        for row, standing in enumerate(others):
            self._build_row(table, row, standing)

    def _build_winner(self, parent: tk.Widget, winner: Standing) -> None:
        """The first place, on its own raised card with the score big."""
        card = tk.Frame(parent, bg=PANEL_RAISED)
        card.pack(fill="x")

        inner = tk.Frame(card, bg=PANEL_RAISED)
        inner.pack(padx=SPACE_4, pady=SPACE_3, fill="x")
        inner.columnconfigure(1, weight=1)

        self._draw_dot(inner, winner.color, WINNER_DOT, PANEL_RAISED).grid(
            row=0, column=0, rowspan=2, padx=(0, SPACE_3), sticky="w",
        )

        name = tk.Frame(inner, bg=PANEL_RAISED)
        name.grid(row=0, column=1, sticky="w")
        tk.Label(
            name, text=winner.name, fg=ACCENT, bg=PANEL_RAISED,
            font=serif(SIZE_WINNER, "bold"),
        ).pack(side="left")
        if winner.has_concordia:
            self._draw_pip(name, PANEL_RAISED).pack(
                side="left", padx=(SPACE_2, 0), anchor="s", pady=(0, 3),
            )

        tk.Label(
            inner, text="wins the game", fg=MUTED_COLOR, bg=PANEL_RAISED,
            font=sans(SIZE_SMALL, "italic"),
        ).grid(row=1, column=1, sticky="w")

        self._draw_score(
            inner, winner.victory_points, SIZE_WINNER_SCORE, ACCENT,
            PANEL_RAISED,
        ).grid(row=0, column=2, rowspan=2, padx=(SPACE_6, 0), sticky="e")

    def _build_row(self, table: tk.Widget, row: int,
                   standing: Standing) -> None:
        """One of the places after the first."""
        pady = (0, SPACE_2)

        tk.Label(
            table, text=f"{standing.rank}", fg=MUTED_COLOR,
            bg=PANEL_BACKGROUND, font=sans(SIZE_BODY, "bold"), width=2,
            anchor="e",
        ).grid(row=row, column=0, padx=(0, SPACE_3), pady=pady, sticky="e")

        self._draw_dot(table, standing.color, DOT, PANEL_BACKGROUND).grid(
            row=row, column=1, padx=(0, SPACE_2), pady=pady,
        )

        name = tk.Frame(table, bg=PANEL_BACKGROUND)
        name.grid(row=row, column=2, pady=pady, sticky="w")
        tk.Label(
            name, text=standing.name, fg=TEXT_COLOR, bg=PANEL_BACKGROUND,
            font=serif(SIZE_LEAD),
        ).pack(side="left")
        if standing.has_concordia:
            self._draw_pip(name, PANEL_BACKGROUND).pack(
                side="left", padx=(SPACE_2, 0),
            )

        self._draw_score(
            table, standing.victory_points, SIZE_SCORE, TEXT_COLOR,
            PANEL_BACKGROUND,
        ).grid(row=row, column=3, padx=(SPACE_6, 0), pady=pady, sticky="e")

    def _build_credits(self, parent: tk.Widget, credits: list[str]) -> None:
        """What the box says, at the foot of the panel."""
        self._rule(parent, pady=(SPACE_4, SPACE_3))

        for line in credits:
            tk.Label(
                parent, text=line, fg=MUTED_COLOR, bg=PANEL_BACKGROUND,
                font=sans(SIZE_SMALL),
            ).pack()

    # --- Pieces ---

    @staticmethod
    def _draw_dot(parent: tk.Widget, color: str, size: int,
                  ground: str) -> tk.Canvas:
        """The colour of a seat, as the rail draws it."""
        dot = tk.Canvas(
            parent, width=size, height=size, bg=ground, highlightthickness=0,
        )
        dot.create_oval(1, 1, size - 1, size - 1, fill=color,
                        outline=TEXT_COLOR)
        return dot

    @staticmethod
    def _draw_score(parent: tk.Widget, victory_points: int, size: int,
                    color: str, ground: str) -> tk.Frame:
        """A score with "VP" set small beside it, both on the baseline."""
        box = tk.Frame(parent, bg=ground)
        tk.Label(
            box, text=f"{victory_points}", fg=color, bg=ground,
            font=serif(size, "bold"),
        ).pack(side="left", anchor="s")
        tk.Label(
            box, text="VP", fg=MUTED_COLOR, bg=ground,
            font=sans(SIZE_MICRO, "bold"),
        ).pack(side="left", anchor="s", padx=(SPACE_1, 0), pady=(0, 4))
        return box

    @staticmethod
    def _draw_pip(parent: tk.Widget, ground: str) -> tk.Label:
        """The tag saying a player holds the CONCORDIA card."""
        return tk.Label(
            parent, text=CONCORDIA_PIP, fg=ACCENT_INK, bg=ACCENT,
            font=sans(SIZE_MICRO - 1, "bold"), padx=SPACE_1, pady=1,
        )

    @staticmethod
    def _rule(parent: tk.Widget, pady: tuple[int, int]) -> None:
        """A hairline parting one part of the panel from the next."""
        tk.Frame(parent, bg=PANEL_EDGE, height=1).pack(fill="x", pady=pady)
