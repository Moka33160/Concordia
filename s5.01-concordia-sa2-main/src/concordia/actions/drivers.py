"""
File: drivers.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Answers the requests of an action, for the AI players and for the
             tests.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Callable

from concordia.actions.requests import Flow, Request
from concordia.actions.strategy import Strategy

if TYPE_CHECKING:
    from concordia.models.card import Card
    from concordia.models.player import Player
    from concordia.state.game_state import GameState

Answer = Callable[[Request], Any]


def run_flow(flow: Flow, answer: Answer) -> bool:
    """
    Drive an action to its end, asking `answer` for every request.

    :param flow: The generator the action returned.
    :param answer: What is asked for each request.
    :return: What the action returned: whether it was carried out.
    :raise ValueError: When the answer is not one of the options of the
        request.
    """
    try:
        request = next(flow)

        while True:
            given = answer(request)

            if not request.accepts(given):
                raise ValueError(
                    f"{given!r} is not an answer {type(request).__name__} "
                    f"offered: {request.prompt!r}"
                )

            request = flow.send(given)

    except StopIteration as done:
        return bool(done.value)


def card_worth(card: Card) -> int:
    """What a card is worth to a buyer: the value of the goods it costs."""
    return sum(good.value for good in card.cost)


class AiAnswerer:
    """Answers the requests of an action for an AI player."""

    def __init__(self, game_state: GameState, player: Player,
                 rng: random.Random | None = None):
        """
        :param game_state: The game, for what the board and the market
            look like right now.
        :param player: The player being answered for.
        :param rng: The random generator, kept injectable for tests and
            used only to break ties between equally good options.
        """
        self.game_state = game_state
        self.player = player
        self.strategy = Strategy(game_state, player, rng)

    def __call__(self, request: Request) -> Any:
        """Answer one request."""
        return self.strategy(request)
