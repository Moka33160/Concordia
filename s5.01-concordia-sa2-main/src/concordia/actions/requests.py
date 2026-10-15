"""
File: requests.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: What a card action asks for. An action is a generator: it yields a
             request and gets the answer back.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator


@dataclass(frozen=True)
class Request:
    """One decision an action is waiting on."""

    prompt: str
    options: tuple = ()
    optional: bool = False

    def accepts(self, answer: Any) -> bool:
        """Whether an answer is one this request can be sent."""
        if answer is None:
            return self.optional
        return any(answer == option for option in self.options)


@dataclass(frozen=True)
class Option:
    """
    A branch of an action that is neither a place nor a piece: taking the
    sestertii rather than a colonist, buying rather than selling.
    """

    key: str
    label: str


@dataclass(frozen=True)
class ChooseCity(Request):
    """A city of the board. `options` holds `City`."""


@dataclass(frozen=True)
class ChooseRoute(Request):
    """A route of the board. `options` holds `Route`."""

    steps: tuple = ()

    def cost(self, route) -> int:
        """How many steps reaching one of the options spends."""
        for offered, cost in zip(self.options, self.steps):
            if offered is route:
                return cost
        return 1


@dataclass(frozen=True)
class ChooseProvince(Request):
    """A province of the board. `options` holds `Province`."""


@dataclass(frozen=True)
class ChooseColonist(Request):
    """One of the player's own colonists. `options` holds `Colonist`."""


@dataclass(frozen=True)
class ChooseMarketCard(Request):
    """A card of the market display. `options` holds `Card`."""


@dataclass(frozen=True)
class ChooseDiscardCard(Request):
    """The top card of an opponent's discard pile."""


@dataclass(frozen=True)
class ChooseGood(Request):
    """A good. `options` holds good names."""

    giving_up: bool = False


@dataclass(frozen=True)
class ChooseWay(Request):
    """A way a colonist travels by. `options` holds way names."""


@dataclass(frozen=True)
class ChooseOption(Request):
    """A branch of the action. `options` holds `Option`."""


@dataclass(frozen=True)
class Confirm(Request):
    """A yes or no. Answered with a bool, so `accepts` takes both."""

    def accepts(self, answer: Any) -> bool:
        """
        :param answer: The answer a driver is about to send back.
        :return: True when the answer is a bool.
        """
        return isinstance(answer, bool)


@dataclass(frozen=True)
class ChooseAmount(Request):
    """How many units of something, between two bounds."""

    minimum: int = 1
    maximum: int = 1

    def accepts(self, answer: Any) -> bool:
        """
        :param answer: The answer a driver is about to send back.
        :return: True when the answer is a whole number within the bounds.
        """
        if answer is None:
            return self.optional
        return (
            isinstance(answer, int)
            and not isinstance(answer, bool)
            and self.minimum <= answer <= self.maximum
        )


# The type of every action: a generator returning True when the card was
# played.
Flow = Generator[Request, Any, bool]
