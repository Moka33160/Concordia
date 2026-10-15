"""
File: context.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 08-09-2026
Description: What an action receives when a card is played: the card, the
             player and the game.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from concordia.models.card import Card
    from concordia.models.player import Player
    from concordia.state.game_state import GameState


class ActionContext:
    """The three things every action needs, kept out of the card itself."""

    def __init__(self, card: Card, player: Player, game_state: GameState):
        """
        :param card: The card being played.
        :param player: The player playing it.
        :param game_state: The game it is played in.
        """
        self.card = card
        self.player = player
        self.game_state = game_state

    def for_card(self, card: Card) -> ActionContext:
        """The same player and game, acting through another card."""
        return ActionContext(card, self.player, self.game_state)

    def __repr__(self) -> str:
        return f"ActionContext({self.card!r}, {self.player!r})"
