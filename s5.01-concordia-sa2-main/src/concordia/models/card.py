"""
File: card.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: A personality card, as the database gives it. What it does is in
             concordia.actions.
"""
from __future__ import annotations

from enum import Enum

from concordia.models.god import God
from concordia.models.resource import Good


class CardOrigin(Enum):
    """
    Where a card comes from, which tells two copies of the same name apart.
    """

    STARTING = "starting"  # dealt at setup: god of the row, no price
    MARKET = "market"      # decks I to V: god of the copy, price
    AWARD = "award"        # CONCORDIA and the PRÆFECTVS MAGNVS marker


class Card:
    """A personality card, sitting in the market or held in a hand."""

    def __init__(self, name: str, god: God | None, text: str,
                 origin: CardOrigin, deck_number: int | None = None,
                 good: Good | None = None,
                 cost: list[Good] | None = None,
                 example: str | None = None):
        """
        :param name: The card name, as the ORDB spells it.
        :param god: The god of this copy, None when the card has none.
        :param text: The rules text printed on the card.
        :param origin: Where the card comes from.
        :param deck_number: The deck the card is sold in, None off-market.
        :param good: The good the copy is themed after: the DIPLOMAT-style
            copies get it from the ORDB, the MINERVA specialists from
            their name.
        :param cost: The goods the card is bought with.
        :param example: The worked example printed under the rules text.
        """
        self.name = name
        self.god = god
        self.text = text
        self.origin = origin
        self.deck_number = deck_number
        self.good = good
        self.cost = cost or []
        self.example = example

    def __repr__(self) -> str:
        return (
            f"Card({self.name!r}, {self.origin.value}, "
            f"deck={self.deck_number!r}, {self.god!r})"
        )
