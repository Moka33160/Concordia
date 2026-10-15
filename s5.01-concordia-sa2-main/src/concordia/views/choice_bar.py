"""
File: choice_bar.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The bar showing what the played card asks, with the buttons to
             answer it.
"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tk_font
from typing import Any, Callable, NamedTuple

from concordia.actions.requests import ChooseAmount, ChooseOption, Confirm
from concordia.views import highlight
from concordia.views.card_render import draw_rounded_rect
from concordia.views.palette import (
    ACCENT, ACCENT_INK, CARD_SHADOW, MUTED_COLOR, PANEL_BACKGROUND,
    PANEL_EDGE, SIZE_BODY, SIZE_SMALL, SPACE_2, TEXT_COLOR, sans,
)

TAG = "choices"

# The box the panel is centred in before the view gives it the board.
DEFAULT_BOX_HEIGHT = 56

BUTTON_HEIGHT = 32
BUTTON_GAP = 10
BUTTON_PADDING = 16
STEPPER_WIDTH = 30

# The panel never grows past this, a question is one line of text.
MAX_PANEL_WIDTH = 460
MIN_PANEL_WIDTH = 210
PANEL_PADDING = 16
PROMPT_GAP = 12

# The margin kept around the panel, and off the edge of the board.
CLEARANCE = 14

# How many places up the board are tried when the foot is taken.
PLACES = 24

# The number between the two buttons of the stepper.
COUNT_WIDTH = 42

# What the two ways out of a question are called.
SKIP_LABEL = "Skip"
CANCEL_LABEL = "Change card"
GIVE_UP_LABEL = "Give up card"


class _Item(NamedTuple):
    """
    One thing sitting in the panel's row: a button, or the count between the
    stepper's two.
    """

    label: str
    value: Any = None
    muted: bool = False
    width: float | None = None
    pressable: bool = True


class ChoiceBar:
    """One question, spelled out and given its buttons."""

    def __init__(self, canvas: tk.Canvas, left: float, width: float,
                 bottom: float, on_answer: Callable[[Any], None],
                 on_cancel: Callable[[], None], height: float | None = None):
        """
        :param canvas: The table canvas the strip is drawn onto.
        :param left: The left edge of the band it is centred in.
        :param width: The width of that band.
        :param bottom: The y the strip sits above.
        :param on_answer: Called with the answer a button carries.
        :param on_cancel: Called when the player drops the card entirely.
        :param height: How deep the strip is, the default when not given.
        """
        self.canvas = canvas
        self._on_answer = on_answer
        self._on_cancel = on_cancel

        tall = DEFAULT_BOX_HEIGHT if height is None else height
        self._box = (left, bottom - tall, left + width, bottom)
        self._obstacles: list[tuple[float, float]] = []
        self._panel = (0.0, 0.0, 0.0, 0.0)

        self._request = None
        self._amount = 1
        # What the way out is called, and so what it does.
        self._way_out = CANCEL_LABEL
        # True when the question is asked to an AI player.
        self._watching = False
        self._buttons: list[tuple[float, float, float, float, Any]] = []
        self._faces: dict[tuple, tk_font.Font] = {}

    def set_box(self, left: float, top: float, right: float,
                bottom: float) -> None:
        """
        Set the area the question is centred in, so the board.

        :param left: The board's left edge.
        :param top: The board's top edge.
        :param right: The board's right edge.
        :param bottom: The board's bottom edge.
        """
        self._box = (left, top, right, bottom)
        self.redraw()

    def set_obstacles(self, points) -> None:
        """Say where the things the question is about are drawn."""
        self._obstacles = [tuple(point) for point in points]

    # --- Contents ---

    def set_way_out(self, label: str) -> None:
        """
        Say what leaving this card behind is called, and so what it costs.
        """
        if label != self._way_out:
            self._way_out = label
            self.redraw()

    def set_watching(self, watching: bool) -> None:
        """
        Say whether the question belongs to a player the human is only
        watching.
        """
        if watching != self._watching:
            self._watching = watching
            self.redraw()

    def show(self, request) -> None:
        """Put a question up, replacing whatever was there."""
        self._request = request

        if isinstance(request, ChooseAmount):
            self._amount = request.minimum

        self.redraw()

    def hide(self) -> None:
        """Take the strip down."""
        self.show(None)

    @property
    def is_open(self) -> bool:
        """Whether a question is up."""
        return self._request is not None

    # --- Drawing ---

    def redraw(self) -> None:
        """Draw the panel: the wording, then the buttons under it."""
        self.canvas.delete(TAG)
        self._buttons = []
        self._panel = (0.0, 0.0, 0.0, 0.0)

        if self._request is None:
            return

        row = self._row()
        width = self._panel_width(row)
        prompt = self.canvas.create_text(
            0, 0, text=self._request.prompt, anchor="nw", fill=TEXT_COLOR,
            font=sans(SIZE_BODY), width=width - PANEL_PADDING * 2, tags=TAG,
        )
        _x0, y0, _x1, y1 = self.canvas.bbox(prompt)
        buttons = PROMPT_GAP + BUTTON_HEIGHT if row else 0
        height = PANEL_PADDING * 2 + (y1 - y0) + buttons

        left, top = self._place(width, height)
        self.canvas.coords(
            prompt, left + PANEL_PADDING, top + PANEL_PADDING
        )
        self._panel = (left, top, left + width, top + height)
        self._draw_ground(prompt, left, top, width, height)

        # The buttons are on their own row at the bottom, laid out right to
        # left.
        self._draw_row(
            left + width - PANEL_PADDING,
            top + height - PANEL_PADDING - BUTTON_HEIGHT / 2,
            row,
        )

    def _draw_ground(self, prompt: int, left: float, top: float,
                     width: float, height: float) -> None:
        """
        Lay the panel's own ground down, under the wording already drawn.

        :param prompt: The wording already drawn, which the ground goes under.
        :param left: The panel's left edge.
        :param top: The panel's top edge.
        :param width: The panel's width.
        :param height: The panel's height.
        """
        shadow = draw_rounded_rect(
            self.canvas, left + SPACE_2 / 2, top + SPACE_2 / 2,
            left + width + SPACE_2 / 2, top + height + SPACE_2 / 2, 12,
            TAG, fill=CARD_SHADOW, outline="",
        )
        ground = draw_rounded_rect(
            self.canvas, left, top, left + width, top + height, 12, TAG,
            fill=PANEL_BACKGROUND, outline=ACCENT, width=2,
        )
        # Drawn after the text, so above it and above the map.
        self.canvas.tag_lower(ground, prompt)
        self.canvas.tag_lower(shadow, ground)

    # --- What the panel comes out to ---

    def _panel_width(self, row: list["_Item"]) -> float:
        """How wide the panel is drawn: as wide as it has to be."""
        left, _top, right, _bottom = self._box
        ceiling = max(
            MIN_PANEL_WIDTH, min(MAX_PANEL_WIDTH, (right - left) / 2)
        )
        content = max(
            min(self._measure(self._request.prompt, sans(SIZE_BODY)),
                ceiling - PANEL_PADDING * 2),
            self._row_width(row),
        )

        return max(MIN_PANEL_WIDTH, min(ceiling,
                                        content + PANEL_PADDING * 2))

    def _row(self) -> list["_Item"]:
        """Everything sitting in the row under the wording, right to left."""
        if self._watching:
            return []

        row = [_Item(self._way_out, _CANCEL, muted=True)]

        if self._request.optional:
            row.append(_Item(SKIP_LABEL, None, muted=True))

        return row + self._controls()

    def _controls(self) -> list["_Item"]:
        """Whatever answers this kind of question, rightmost first."""
        request = self._request

        if not highlight.is_control(request):
            return []

        if isinstance(request, Confirm):
            return [_Item("No", False), _Item("Yes", True)]

        if isinstance(request, ChooseAmount):
            return [
                _Item("Take", _TAKE),
                _Item("+", _MORE, width=STEPPER_WIDTH),
                _Item(f"{self._amount} / {request.maximum}",
                      pressable=False, width=COUNT_WIDTH),
                _Item("\u2212", _LESS, width=STEPPER_WIDTH),
            ]

        if isinstance(request, ChooseOption):
            return [_Item(option.label, option)
                    for option in reversed(request.options)]

        # A way (land or sea) has no place of its own on the map.
        return [_Item(str(option).capitalize(), option)
                for option in reversed(request.options)]

    def _item_width(self, item: "_Item") -> float:
        """How wide one control is drawn."""
        if item.width is not None:
            return item.width

        return self._measure(item.label, sans(SIZE_SMALL, "bold")) \
            + BUTTON_PADDING * 2

    def _row_width(self, row: list["_Item"]) -> float:
        """How wide the whole row of controls comes out."""
        if not row:
            return 0.0

        return (
            sum(self._item_width(item) for item in row)
            + BUTTON_GAP * (len(row) - 1)
        )

    # --- Drawing the row ---

    def _draw_row(self, right: float, middle: float,
                  row: list["_Item"]) -> None:
        """
        Draw the controls, laying them out right to left.

        :param right: The x the row is laid out leftwards from.
        :param middle: The y the row is centred on.
        :param row: The controls the panel is carrying.
        """
        for item in row:
            width = self._item_width(item)

            if item.pressable:
                self._draw_button(right, middle, item, width)
            else:
                self.canvas.create_text(
                    right - width / 2, middle, text=item.label,
                    fill=ACCENT, font=sans(SIZE_BODY, "bold"), tags=TAG,
                )

            right -= width + BUTTON_GAP

    def _draw_button(self, right: float, middle: float, item: "_Item",
                     width: float) -> None:
        """
        Draw one button, its right edge at `right`.

        :param right: The x the button's right edge sits at.
        :param middle: The y the button is centred on.
        :param item: What the button reads and what it carries.
        :param width: How wide it is drawn.
        """
        left = right - width
        top = middle - BUTTON_HEIGHT / 2

        # Only the answers to the question itself are filled in gold.
        draw_rounded_rect(
            self.canvas, left, top, right, top + BUTTON_HEIGHT, 7, TAG,
            fill=PANEL_BACKGROUND if item.muted else ACCENT,
            outline=PANEL_EDGE if item.muted else ACCENT, width=1,
        )
        self.canvas.create_text(
            (left + right) / 2, middle, text=item.label,
            fill=MUTED_COLOR if item.muted else ACCENT_INK,
            font=sans(SIZE_SMALL, "bold"), tags=TAG,
        )

        self._buttons.append(
            (left, top, right, top + BUTTON_HEIGHT, item.value)
        )

    # --- Where it goes ---

    def _place(self, width: float, height: float) -> tuple[float, float]:
        """
        Find where on the board the panel goes.

        :param width: The panel's width.
        :param height: The panel's height.
        :return: The (left, top) to draw it at.
        """
        left, top, right, bottom = self._box
        panel_left = (left + right) / 2 - width / 2
        resting = bottom - height / 2 - CLEARANCE
        highest = top + height / 2 + CLEARANCE

        if not self._obstacles or resting <= highest:
            return panel_left, max(top, resting - height / 2)

        best, best_cost = resting, None
        for step in range(PLACES + 1):
            candidate = resting - (resting - highest) * step / PLACES
            cost = (
                self._hidden(panel_left, candidate - height / 2,
                             width, height),
                abs(candidate - resting),
            )
            if best_cost is None or cost < best_cost:
                best, best_cost = candidate, cost

        return panel_left, best - height / 2

    def _hidden(self, left: float, top: float, width: float,
                height: float) -> int:
        """
        How many lit things a panel drawn here would cover.

        :param left: The panel's left edge.
        :param top: The panel's top edge.
        :param width: The panel's width.
        :param height: The panel's height.
        :return: The number of obstacles falling under it.
        """
        return sum(
            1 for x, y in self._obstacles
            if left - CLEARANCE <= x <= left + width + CLEARANCE
            and top - CLEARANCE <= y <= top + height + CLEARANCE
        )

    def _measure(self, label: str, face: tuple) -> float:
        """
        How wide a label really is, in the face it is drawn in.

        :param label: The text to measure.
        :param face: The font tuple it is drawn in.
        :return: Its width in pixels, or an estimation when Tk is not up yet.
        """
        if face not in self._faces:
            try:
                self._faces[face] = tk_font.Font(root=self.canvas, font=face)
            except tk.TclError:
                return len(label) * 7

        return self._faces[face].measure(label)

    # --- Pointer ---

    def click_at(self, x: float, y: float) -> bool:
        """
        Take a click, if it landed on one of the buttons.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: True when the strip answered for the click.
        """
        if self._request is None:
            return False

        for x0, y0, x1, y1, value in self._buttons:
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._press(value)
                return True

        return self._covers(x, y)

    def _covers(self, x: float, y: float) -> bool:
        """
        Whether the panel itself is under the pointer.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: True when the pointer is over the panel.
        """
        left, top, right, bottom = self._panel
        return left <= x <= right and top <= y <= bottom

    def _press(self, value: Any) -> None:
        """Act on a button."""
        if value is _CANCEL:
            self._on_cancel()
            return

        if value is _MORE or value is _LESS:
            self._step(1 if value is _MORE else -1)
            return

        if value is _TAKE:
            self._on_answer(self._amount)
            return

        self._on_answer(value)

    def _step(self, by: int) -> None:
        """Move the stepper, without leaving the bounds it was given."""
        request = self._request
        self._amount = min(
            max(self._amount + by, request.minimum), request.maximum
        )
        self.redraw()


# The buttons acting on the bar itself. Sentinels, so they cannot be an answer.
_CANCEL = object()
_MORE = object()
_LESS = object()
_TAKE = object()
