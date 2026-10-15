"""
File: play_flow.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Steps the action of a card one click at a time.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from concordia.actions.requests import Flow, Request
    from concordia.models.card import Card


class PlayFlow:
    """The card being played, and the question it is waiting on."""

    def __init__(self):
        self._flow: Flow | None = None
        self._request: Request | None = None
        self.card: Card | None = None
        self.result: bool | None = None

    @property
    def request(self) -> Request | None:
        """What the action is waiting on, None when it is not waiting."""
        return self._request

    @property
    def is_running(self) -> bool:
        """Whether an action is part-way through."""
        return self._flow is not None

    @property
    def is_finished(self) -> bool:
        """Whether the last action played ran to its end."""
        return self._flow is None and self.result is not None

    def start(self, card: Card, flow: Flow) -> Request | None:
        """
        Begin an action, stopping at the first thing it asks.

        :param card: The card being played, kept for the caller to discard.
        :param flow: The action's generator, unstarted.
        :return: The first request, None when the action asked nothing.
        """
        self._flow = flow
        self.card = card
        self.result = None

        return self._advance(lambda: next(flow))

    def answer(self, value: Any) -> Request | None:
        """Send an answer back and stop at the next thing the action asks."""
        if self._flow is None or self._request is None:
            raise ValueError("no action is waiting on an answer")

        if not self._request.accepts(value):
            raise ValueError(
                f"{value!r} is not an answer "
                f"{type(self._request).__name__} offered"
            )

        flow = self._flow

        return self._advance(lambda: flow.send(value))

    def cancel(self) -> None:
        """Abandon the action where it stands."""
        if self._flow is not None:
            self._flow.close()

        self._flow = None
        self._request = None
        self.card = None
        self.result = None

    def _advance(self, step: Callable[[], Request]) -> Request | None:
        """Take one step, and note where the action came to rest."""
        try:
            self._request = step()
        except StopIteration as done:
            self._request = None
            self._flow = None
            self.result = bool(done.value)

        return self._request
